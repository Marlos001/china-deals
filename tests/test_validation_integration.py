"""Offline regressions from the three Astra marketplace search audits."""
import json
import unittest
from unittest.mock import Mock, patch

from china_deals import adapters, browser_guest, guest
from china_deals.cli import build_parser, hydrate_leads, run
from china_deals.models import MARKETPLACES, normalize_offer
from china_deals.ranking import rank_offers

BLIBLI = 'https://www.blibli.com/p/synthetic/ps--SYN-00001-00001'
OPAQUE = 'https://item.jd.com/product/6QDM9CaD9ZAa0SxjEPbKrg.html'


class AccessSessionTests(unittest.TestCase):
    def test_command_stops_shared_index_after_challenge_but_tries_independent_host(self):
        challenge = adapters._Failure('blocked', 'challenge', 'Synthetic gate')
        with patch.object(guest, '_fetch', side_effect=challenge) as fetch:
            args = build_parser().parse_args(['search', 'AirPods Max', '--zh-query', '苹果 耳机', '--currency', 'native'])
            result, code = run(args)
            self.assertEqual(code, 3)
            # One DDG request plus one independent Blibli API request.
            self.assertEqual(fetch.call_count, 2)
            attempts = [a for source in result['sources'] for a in source.get('access', {}).get('attempts', [])]
            skipped = [a for a in attempts if a['status'] == 'skipped_after_challenge']
            self.assertEqual(len(skipped), len(MARKETPLACES) - 1)
            self.assertEqual({s['marketplace'] for s in result['sources']}, set(MARKETPLACES))
            self.assertTrue(all(a['network_attempted'] is False for a in skipped))
            self.assertTrue(all('duckduckgo.com' in a['gate_origin']['url'] for a in skipped))
            run(args)
            self.assertEqual(fetch.call_count, 4, 'A new command resets its access gates')

    def test_browser_gate_prevents_second_navigation_and_late_gate_updates_receipt(self):
        result = guest._envelope('jd')
        result['source_mode'] = 'search_index'
        page = Mock(url='https://www.google.com/search?q=one')
        page.goto.return_value = None
        page.evaluate.return_value = {'title': 'Google', 'text': ''}
        context = Mock()
        context.new_page.return_value = page
        with guest.access_session():
            browser_guest._navigate(context, page.url, 'jd', result, __import__('time').monotonic() + 10)
            guest._failure(result, adapters._Failure('blocked', 'challenge', 'Late rendered challenge'))
            with self.assertRaises(adapters._Failure):
                browser_guest._navigate(context, 'https://www.google.com/search?q=two', 'jd', result,
                                        __import__('time').monotonic() + 10)
        self.assertEqual(context.new_page.call_count, 1)
        self.assertEqual(result['access']['attempts'][0]['error_code'], 'challenge')
        self.assertFalse(result['access']['attempts'][1]['network_attempted'])

    def test_redirect_destination_challenge_does_not_gate_index_host(self):
        result = guest._envelope('jd')
        result['source_mode'] = 'search_index'
        page = Mock(url='https://item.jd.com/1.html')
        page.goto.return_value = None
        page.evaluate.return_value = {'title': 'Product', 'text': '', 'verification': True}
        context = Mock()
        context.new_page.return_value = page
        with guest.access_session():
            with self.assertRaises(adapters._Failure):
                browser_guest._navigate(context, 'https://www.google.com/url?q=jd', 'jd', result,
                                        __import__('time').monotonic() + 10)
            independent = {'url': 'https://www.google.com/search?q=blibli'}
            guest._check_gate(independent)
            self.assertTrue(independent['network_attempted'])
            attempt = {'url': 'https://item.jd.com/2.html'}
            with self.assertRaises(adapters._Failure):
                guest._check_gate(attempt)
            self.assertEqual(attempt['gate_origin']['url'], page.url)


    def test_repeated_blibli_skips_remain_non_network_receipts(self):
        with guest.access_session(), patch.object(guest, '_fetch', side_effect=adapters._Failure('blocked', 'http_403', 'Denied')) as fetch:
            guest.search_guest('blibli', 'one')
            result = guest.search_guest('blibli', 'two')
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual([a['status'] for a in result['access']['attempts']], ['skipped_after_challenge'] * 2)
        self.assertTrue(all(not a['network_attempted'] for a in result['access']['attempts']))



class DiscoveryTests(unittest.TestCase):
    def test_opaque_jd_preserved_as_unpriced_lead_without_sku(self):
        html = f'<a class="result__a" href="{OPAQUE}">iPhone 17 Pro Max</a>'
        html += '<a class="result__a" href="https://item.jd.com/category">unsupported</a>'
        with patch.object(guest, '_fetch', return_value=(html, 'https://html.duckduckgo.com/html/')):
            result = guest.search_guest('jd', '苹果')
        self.assertEqual(result['status'], 'discovery_only')
        row = result['items'][0]
        self.assertEqual(row['url'], OPAQUE)
        self.assertIsNone(row['item_id'])
        self.assertIsNone(guest._product_url('jd', OPAQUE))
        self.assertEqual(result['rejected_routes']['count'], 1)
        self.assertFalse(rank_offers([dict(row, marketplace='jd')])['groups'])
        with patch.object(guest, '_fetch') as fetch:
            detail = guest.get_guest_item('jd', OPAQUE)
            self.assertEqual(detail['error']['code'], 'numeric_sku_unresolved')
            fetch.assert_not_called()
        self.assertEqual(browser_guest.get_browser_guest_item('jd', OPAQUE)['error']['code'], 'numeric_sku_unresolved')
        self.assertIsNone(guest._item_id('jd', 'https://item.jd.com/product/123.html'))
        self.assertEqual(guest._item_id('jd', 'https://item.m.jd.com/product/123.html'), '123')

    def test_opaque_validation_is_exact(self):
        for value in [OPAQUE.replace('item.jd.com', 'item.jd.com.evil.test'),
                      'https://item.jd.com/product/abc/def.html', 'https://item.jd.com/product/' + 'x' * 129 + '.html']:
            self.assertIsNone(guest._discovery_url('jd', value))


class StockTests(unittest.TestCase):
    def row(self, offer_stock=None, product_stock=None, condition=None):
        offer = {'@type': 'Offer', 'url': BLIBLI, 'price': '100000', 'priceCurrency': 'IDR'}
        product = {'@type': 'Product', 'name': 'Apple AirPods Max', 'url': BLIBLI, 'offers': offer}
        if offer_stock:
            offer['availability'] = 'https://schema.org/' + offer_stock
        if product_stock:
            product['availability'] = 'https://schema.org/' + product_stock
        if condition:
            offer['itemCondition'] = 'https://schema.org/' + condition
        parser = guest._html('<script type="application/ld+json">' + json.dumps(product) + '</script>')
        return guest._blibli_detail(parser, BLIBLI)[0]

    def test_unavailable_stock_cannot_rank(self):
        for value in ('OutOfStock', 'SoldOut', 'Discontinued'):
            row = self.row(value)
            self.assertEqual(row['availability'], 'unavailable')
            ranked = rank_offers([dict(row, marketplace='blibli')])
            self.assertFalse(ranked['groups'])
            self.assertIsNone(ranked['unranked'][0]['price']['amount'])

    def test_stock_conflict_condition_and_raw_evidence_retained(self):
        row = self.row('InStock', 'OutOfStock', 'UsedCondition')
        normalized = normalize_offer('blibli', row)
        self.assertEqual(normalized['availability'], 'unavailable')
        self.assertEqual(normalized['condition'], 'used')
        self.assertTrue(normalized['source_warnings'])
        self.assertIn('OutOfStock', normalized['source_detail']['product']['availability'])
        self.assertEqual(self.row('InStock')['availability'], 'source_claimed_available')
        self.assertEqual(self.row()['availability'], 'unknown')
        self.assertEqual(self.row('PreOrder')['availability'], 'unknown')


class HydrationTests(unittest.TestCase):
    def leads(self):
        return {'items': [{'url': f'https://item.jd.com/{i}.html', 'item_id': str(i), 'title': 'AirPods Max',
                           'source_mode': 'search_index', 'price': None,
                           'index_source_url': 'https://index.example/search', 'discovered_at': '2026-10-27T00:00:00Z'}
                          for i in (1, 2)], 'access': {'attempts': [{'url': 'https://index.example/search', 'status': 'ok'}]}}

    def test_failed_hydration_retains_receipt_and_skips_remaining_detail(self):
        result = self.leads()
        result['items'].append(dict(result['items'][1], url='https://item.jd.com/3.html', item_id='3'))
        getter = Mock(return_value={'status': 'blocked', 'items': [], 'error': {'code': 'challenge'},
                                    'access': {'attempts': [{'url': 'https://item.m.jd.com/product/1.html', 'status': 'blocked'}]}})
        hydrate_leads(result, getter, 'jd', 3, 10, {})
        self.assertEqual(getter.call_count, 1)
        self.assertEqual([r['status'] for r in result['hydration']], ['blocked', 'skipped_after_challenge', 'skipped_after_challenge'])
        self.assertEqual(len(result['access']['attempts']), 2)
        self.assertEqual(len(result['items']), 3)
        self.assertEqual(result['hydration'][2]['gate_origin']['target'], 'https://item.jd.com/1.html')
        self.assertIsNone(result['items'][0]['price'])
        self.assertTrue(normalize_offer('jd', result['items'][0])['source_warnings'])

    def test_successful_hydration_preserves_product_and_index_evidence(self):
        result = self.leads()
        getter = Mock(return_value={'status': 'ok', 'items': [{'title': 'AirPods Max USB-C', 'price': '4000',
                      'url': 'https://item.jd.com/1.html', 'source_mode': 'guest_product_page', 'detail': {'sku': '1'}}],
                      'access': {'attempts': [{'url': 'https://item.m.jd.com/product/1.html', 'status': 'ok'}]}})
        hydrate_leads(result, getter, 'jd', 1, 10, {})
        row = normalize_offer('jd', result['items'][0])
        self.assertEqual(row['source_detail']['sku'], '1')
        self.assertEqual(row['source_detail']['discovery']['title'], 'AirPods Max')
        self.assertEqual(row['index_source_url'], 'https://index.example/search')
        self.assertEqual(row['price']['amount'], '4000')


class ExportedIntentTests(unittest.TestCase):
    def test_offer_array_retains_exclusion_without_parent_envelope(self):
        from china_deals.hardware import compare_laptops
        title = ('ASUS ROG Zephyrus G16 GU605MI Intel Core Ultra 9 185H RTX 4070 Laptop GPU '
                 '8GB TGP 105W RAM 32GB SSD 1TB 16-inch 2560x1600 OLED 240Hz new')
        response = {'status': 'ok', 'items': [{'title': title, 'sku': '123', 'price': '12000'}],
                    'source_mode': 'guest_product_page', 'warnings': []}
        with patch.object(guest, 'search_guest', return_value=response):
            payload, _ = run(build_parser().parse_args(['search', 'ASUS ROG Zephyrus G14', '--zh-query',
                             '华硕 幻14', '--markets', 'jd', '--include-offers', '--currency', 'native']))
        offers = payload['offers']
        self.assertTrue(offers[0]['ranking_exclusions'])
        self.assertFalse(compare_laptops(offers)['groups'])
        reranked = rank_offers(offers)
        self.assertFalse(reranked['groups'])
        self.assertTrue(reranked['unranked'][0]['ranking_exclusions'])
        self.assertFalse(rank_offers(reranked['unranked'])['groups'])
        # Explicit replacement intent can establish a matching product again.
        self.assertTrue(rank_offers(offers, query='ASUS ROG Zephyrus G16')['groups'])



class CouponRoundtripTests(unittest.TestCase):
    def test_query_and_accessory_exclusion_survive_coupons(self):
        first = rank_offers([{'marketplace': 'jd', 'sku': '1', 'title': 'Case iPhone 17 Pro Max', 'price': '10'}],
                            query='iPhone 17 Pro Max')
        with patch('china_deals.cli.read_json', side_effect=[first, {'campaigns': []}]):
            coupons, _ = run(build_parser().parse_args(['coupons', 'input', '--rules', 'rules', '--currency', 'native']))
        self.assertEqual(coupons['intent_query'], 'iPhone 17 Pro Max')
        with patch('china_deals.cli.read_json', return_value=coupons):
            final, _ = run(build_parser().parse_args(['rank', 'input', '--currency', 'native']))
        self.assertFalse(final['groups'])
        self.assertEqual(final['unranked'][0]['relevance']['status'], 'mismatch')


if __name__ == '__main__':
    unittest.main()
