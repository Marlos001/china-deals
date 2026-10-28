"""Offline international storefront, quantity, currency and workflow contracts."""

import copy
import json
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

from china_deals import adapters, browser_guest, guest, refresh
from china_deals.brazil import compare_brazil
from china_deals.capabilities import marketplace_capabilities, resolve_markets
from china_deals.china_capture import parse_capture
from china_deals.china_public import parse_product_page
from china_deals.cli import build_parser, run
from china_deals.config import DEFAULT_CONFIG
from china_deals.coupons import evaluate_coupons
from china_deals.fx import annotate_offers, convert_brl, parse_ecb
from china_deals.marketplaces import FANSBUY_MARKETPLACES, canonical_product_url, item_url, product_id
from china_deals.models import normalize_offer
from china_deals.ranking import rank_offers
from tests.test_brazil import AS_OF, payload
from tests.test_browser_guest import Context, Page
from tests.test_preferences import XML

URLS = {'alibaba': 'https://www.alibaba.com/product-detail/Synthetic-Headphones_1601234567890.html',
        'aliexpress': 'https://www.aliexpress.com/item/1005001234567890.html'}


def offer(market, **changes):
    return {'marketplace': market, 'url': URLS[market], 'title': 'Sony WH-1000XM6',
            'currency': 'USD', 'price': '100', 'observed_at': AS_OF, **changes}


def document(market, currency='USD', **changes):
    node = {'@type': 'Product', 'url': URLS[market], 'name': 'Sony WH-1000XM6',
            'offers': {'@type': 'AggregateOffer', 'lowPrice': '1', 'highPrice': '100',
                       'priceCurrency': currency, 'eligibleQuantity': {'minValue': 100}}, **changes}
    return '<html><head><script type="application/ld+json">' + json.dumps(node) + '</script></head><body>Product</body></html>'


class InternationalMarketplaces(unittest.TestCase):
    def test_distinct_keys_aliases_manual_logistics_and_capabilities(self):
        self.assertEqual(resolve_markets('alibaba.com,aliexpress.com,1688'), ['alibaba', 'aliexpress', '1688'])
        self.assertEqual(len(resolve_markets('all')), 9)
        self.assertEqual(resolve_markets('fansbuy'), list(FANSBUY_MARKETPLACES))
        for market in URLS:
            self.assertEqual(DEFAULT_CONFIG['marketplaces'][market], {'access': 'guest', 'shipping': 'manual', 'currency': 'USD'})
            cap = next(r for r in marketplace_capabilities()['marketplaces'] if r['marketplace'] == market)
            self.assertEqual(cap['fansbuy_named_evidence'], [])
            self.assertIn('English', cap['query_language'])

    def test_native_routes_preserve_region_and_never_invent_alibaba_slug(self):
        for market, url in URLS.items():
            self.assertEqual(canonical_product_url(market, url + '?spm=synthetic#details'), url)
            self.assertEqual(product_id(market, url), url.rsplit('_' if market == 'alibaba' else '/', 1)[-1].removesuffix('.html'))
            for suffix in ('?id=1', '?product_id=1', '?ID=', '?sku_id=1', '?quantity=100', '?SkuId='):
                self.assertIsNone(canonical_product_url(market, url + suffix))
            for bad in (url.replace('https:', 'http:'), url.replace('www.', 'user@www.'),
                        url.replace('.com', '.com.evil.test'), url.replace('.com', '.com:443')):
                self.assertIsNone(canonical_product_url(market, bad))
        self.assertIsNone(item_url('alibaba', '1601234567890'))
        us = 'https://www.aliexpress.us/item/3256801234567890.html'
        self.assertEqual(canonical_product_url('aliexpress', us), us)

    def test_explicit_currencies_and_localized_brl_survive_four_passes(self):
        for market in URLS:
            for code, amount in (('USD', '100'), ('EUR', '100.50'), ('BRL', 'R$ 1.234,50'), ('JPY', '100')):
                row = offer(market, currency=code, price=amount)
                for _ in range(4):
                    result = rank_offers(json.loads(json.dumps([row])), query='Sony WH-1000XM6')
                    self.assertEqual(set(result['groups']), {code})
                    row = result['groups'][code][0]
                    self.assertEqual(row['currency_observations'], [code])
                    self.assertIsNotNone(row['price']['amount'])

    def test_missing_conflicting_unsupported_and_overflow_currency_stay_unpriced(self):
        for market in URLS:
            for fields in ({'currency': None}, {'currency': False}, {'currency': 'ZZZ'},
                           {'currency': 'USD', 'priceCurrency': 'BRL'},
                           {'currency': 'USD', 'offers': {'@type': 'Offer', 'price': '100', 'priceCurrency': 'EUR'}},
                           {'currency_observations': ['USD'] * 21}):
                row = offer(market, **fields)
                for _ in range(4):
                    result = rank_offers(json.loads(json.dumps([row])), query='Sony WH-1000XM6')
                    self.assertFalse(result['groups'])
                    row = result['unranked'][0]
                    self.assertIsNone(row['price']['amount'])

    def test_moq_tiers_and_order_quantity_never_become_single_unit_prices(self):
        for market in URLS:
            for field in ('moq', 'minOrderQuantity', 'minimum_order_quantity', 'quantity', 'lot_size', 'price_tiers', 'eligibleQuantity'):
                row = offer(market, **{field: [{'price': 1}] if field == 'price_tiers' else 100})
                for _ in range(3):
                    result = rank_offers(json.loads(json.dumps([row])))
                    self.assertFalse(result['groups'])
                    row = result['unranked'][0]
                    self.assertIsNone(row['price']['amount'])
                    self.assertIn(field, row['purchase_constraints'])
            self.assertTrue(rank_offers([offer(market, moq='1 piece', quantity=1)])['groups'])

    def test_structured_offer_quantity_cannot_escape_unit_price_hold(self):
        for market in URLS:
            row = offer(market, price=None, offers={
                '@type': 'Offer', 'price': '1', 'priceCurrency': 'USD',
                'eligibleQuantity': {'minValue': 100}})
            for _ in range(4):
                result = rank_offers(json.loads(json.dumps([row])))
                self.assertFalse(result['groups'])
                row = result['unranked'][0]
                self.assertIsNone(row['price']['amount'])
                self.assertIn('eligibleQuantity', row['purchase_constraints'])

    def test_metadata_captures_keep_tier_claims_and_source_time_but_no_quote(self):
        for market in URLS:
            html = document(market, currency='BRL')
            cap = {'url': URLS[market], 'capturedAt': AS_OF, 'html': html,
                   'htmlBytes': len(html.encode()), 'htmlTruncated': False}
            row = parse_capture(cap, market, URLS[market])
            self.assertEqual(row['currency'], 'BRL')
            self.assertEqual(row['source_detail']['offer_claims'][0]['eligibleQuantity']['minValue'], 100)
            for _ in range(3):
                result = rank_offers([row])
                self.assertFalse(result['groups'])
                row = result['unranked'][0]
                self.assertEqual(row['observed_at'], AS_OF)
                self.assertIsNone(row['price']['amount'])

    def test_alibaba_observed_numeric_identity_localized_url_binding(self):
        identity = '1601234567890'
        localized = '//indonesian.alibaba.com/product-detail/Native-Alias-' + identity + '.html'
        product = {'@type': 'Product', '@id': identity, 'sku': identity, 'name': 'SANITIZED native product'}
        def html(node, page_url=localized):
            return ('<html><head><meta property="og:url" content="' + page_url + '">'
                    '<script type="application/ld+json">' + json.dumps(node) + '</script></head><body></body></html>')
        row = parse_product_page(html(product), 'alibaba', URLS['alibaba'], AS_OF)
        self.assertEqual(row['item_id'], identity)
        self.assertIsNone(row['price'])
        for node, url in ((dict(product, sku='999'), localized),
                          (dict(product, **{'@id': '999'}), localized),
                          (dict(product, url=URLS['alibaba'].replace(identity, '999')), localized),
                          (product, localized.replace(identity, '999')),
                          (product, localized.replace('.alibaba.com', '.evil.test'))):
            with self.assertRaises(ValueError):
                parse_product_page(html(node, url), 'alibaba', URLS['alibaba'], AS_OF)
        with self.assertRaises(ValueError):
            parse_product_page('<html><head><script type="application/ld+json">' + json.dumps(product) + '</script></head><body></body></html>', 'alibaba', URLS['alibaba'], AS_OF)

    def test_http_browser_and_native_boundaries(self):
        for market in URLS:
            with patch.object(guest, '_fetch', return_value=(document(market), URLS[market])):
                result = guest.get_guest_item(market, URLS[market])
            self.assertEqual(result['status'], 'ok')
            self.assertIsNone(result['items'][0]['price'])
            page = Page(URLS[market], html=document(market))
            with patch.object(browser_guest, '_browser_context', return_value=nullcontext(Context([page]))):
                result = browser_guest.get_browser_guest_item(market, URLS[market])
            self.assertEqual(result['status'], 'ok')
            self.assertTrue(page.closed)
            with patch.object(adapters, '_run', side_effect=AssertionError('unsupported native I/O')):
                self.assertEqual(adapters.get_item(market, URLS[market])['error']['code'], 'native_adapter_unavailable')

    def test_english_queries_are_not_replaced_by_chinese_override(self):
        seen = []
        def search(market, query, *args, **unused):
            seen.append((market, query))
            return {'marketplace': market, 'status': 'empty_unverified', 'items': [], 'warnings': [], 'error': None}
        with patch.object(guest, 'search_guest', side_effect=search):
            run(build_parser().parse_args(['search', 'Sony WH-1000XM6', '--markets', 'alibaba,aliexpress',
                                          '--zh-query', '索尼 耳机', '--currency', 'native']))
        self.assertEqual(seen, [('alibaba', 'Sony WH-1000XM6'), ('aliexpress', 'Sony WH-1000XM6')])

    def test_capture_cli_stays_offline_and_processes_usd_coupon_rules(self):
        for market in URLS:
            body = document(market)
            cap = {'url': URLS[market], 'capturedAt': AS_OF, 'html': body,
                   'htmlBytes': len(body.encode()), 'htmlTruncated': False}
            with patch('china_deals.cli.read_json', side_effect=lambda p: cap if p == 'capture.json' else {'campaigns': []}), patch('china_deals.fx.fetch_rates', side_effect=AssertionError('offline FX')):
                result, code = run(build_parser().parse_args(['detail', market, URLS[market],
                                  '--from-browser-json', 'capture.json', '--coupons-from-json', 'rules.json']))
            self.assertEqual(code, 0)
            self.assertFalse(result['access']['attempts'])
            self.assertIn('coupon_estimates', result['items'][0])

    def test_access_challenges_gate_followups_and_capture(self):
        for market in URLS:
            body = '<html><head><title>Security Check</title></head><body>Please slide to verify</body></html>'
            with guest.access_session(), patch.object(guest, '_fetch', return_value=(body, URLS[market])) as fetch:
                first = guest.get_guest_item(market, URLS[market])
                second = guest.get_guest_item(market, URLS[market])
            self.assertEqual(first['error']['code'], 'challenge')
            self.assertEqual(second['error']['code'], 'skipped_after_challenge')
            self.assertEqual(fetch.call_count, 1)
            self.assertTrue(browser_guest._gate_url(URLS[market] + '/_____tmd_____/punish'))

    def test_refresh_history_preserves_new_identity_and_unpriced_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            store = str(Path(folder) / 'history.sqlite3')
            for market in URLS:
                with patch.object(guest, '_fetch', return_value=(document(market), URLS[market])):
                    result = refresh.refresh_offers([offer(market)], store_path=store)
                self.assertIsNone(result['items'][0]['price']['amount'])
                self.assertEqual(result['items'][0]['marketplace'], market)
                self.assertEqual(len(refresh.history(store, marketplace=market)), 1)

    def test_fx_and_coupons_support_explicit_usd_eur_brl(self):
        snapshot = parse_ecb(XML)
        self.assertEqual(convert_brl('10', 'EUR', snapshot), '60.00')
        for currency in ('USD', 'EUR', 'BRL'):
            row = normalize_offer('aliexpress', offer('aliexpress', currency=currency), AS_OF)
            annotate_offers([row], snapshot, DEFAULT_CONFIG)
            self.assertEqual(row['brl']['shipping_policy'], 'manual')
            campaign = {'currency': currency, 'discount': {'amount': 10}}
            result = evaluate_coupons(row, [campaign], as_of=AS_OF)
            self.assertEqual(result['campaigns'][0]['amount_due'], '90.00')

    def test_brazil_comparison_keeps_usd_and_requires_all_manual_costs(self):
        for market in URLS:
            data = payload()
            foreign = data['cases'][0]['imported']['offer']
            foreign.pop('sku')
            foreign.update(marketplace=market, url=URLS[market], price='100', currency='USD')
            result = compare_brazil(data, config=copy.deepcopy(DEFAULT_CONFIG))['cases'][0]
            self.assertEqual(result['financial_outcome'], 'brazil_cheaper')
            data['cases'][0]['imported']['costs'].pop('international_freight')
            result = compare_brazil(data, config=copy.deepcopy(DEFAULT_CONFIG))['cases'][0]
            self.assertEqual(result['financial_outcome'], 'needs_review')
            self.assertIsNone(result['savings_amount_brl'])


if __name__ == '__main__':
    unittest.main()
