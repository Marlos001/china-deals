import unittest

from china_deals.models import normalize_offer, parse_price, safe_url
from china_deals.ranking import rank_offers


class RankingTests(unittest.TestCase):
    def test_currency_grammar_and_ambiguous_prices(self):
        self.assertEqual(parse_price('¥1,234.50', 'CNY'), '1234.50')
        self.assertEqual(parse_price('Rp1.234.500', 'IDR'), '1234500')
        self.assertEqual(parse_price(1234500, 'IDR'), '1234500')
        for value in ['¥50-100', '¥99起', '定金 ¥20', 'NaN', True, 0, -1, '1,2,3']:
            self.assertIsNone(parse_price(value, 'CNY'), repr(value))

    def test_marketplace_urls_not_lookalike_hosts(self):
        for url in ['https://jd.com.evil.test/1', 'javascript:alert(1)', 'https://user:pass@jd.com/1',
                    'https://evil.test\\.jd.com/1', 'https://jd.com:443/1', 'https://jd.com/white space',
                    'http://jd.com/123.html']:
            self.assertIsNone(safe_url(url, 'jd'))
        self.assertEqual(safe_url('https://item.jd.com/123.html', 'jd'), 'https://item.jd.com/123.html')

    def test_no_fabricated_observation_or_blibli_forwarding(self):
        result = normalize_offer('blibli', {'title': 'Example', 'price': 'Rp1.000', 'url': '/p/example/ps--EXAMPLE'})
        self.assertIsNone(result['observed_at'])
        self.assertEqual(result['price']['currency'], 'IDR')
        self.assertTrue(any('Indonesia' in x for x in result['warnings']))

    def test_separate_currencies_and_filter_exact_terms(self):
        offers = [
            {'marketplace': 'jd', 'sku': '123', 'title': 'Keyboard K8', 'price': '¥300'},
            {'marketplace': 'taobao', 'item_id': '456', 'title': 'Keyboard K8', 'price': '¥200'},
            {'marketplace': 'goofish', 'item_id': '789', 'title': 'Keyboard K8 for parts', 'price': '¥20'},
            {'marketplace': 'blibli', 'title': 'Keyboard K8', 'price': 'Rp100.000', 'url': '/p/example/ps--EXAMPLE'},
        ]
        result = rank_offers(offers, ['K8'], ['for parts'])
        self.assertEqual(set(result['groups']), {'CNY', 'IDR'})
        self.assertEqual(result['groups']['CNY'][0]['marketplace'], 'taobao')
        self.assertEqual(result['filtered_count'], 1)
        self.assertEqual(result['comparability'], 'unverified')

    def test_variants_are_not_deduplicated_and_unsafe_links_unranked(self):
        rows = [{'marketplace': 'jd', 'sku': '123', 'title': 'Example', 'price': '¥20', 'variant': x}
                for x in ['red', 'blue']]
        rows.append({'marketplace': 'jd', 'title': 'Bad link', 'price': '¥1', 'url': 'https://evil.test'})
        result = rank_offers(rows)
        self.assertEqual(len(result['groups']['CNY']), 2)
        self.assertEqual(len(result['unranked']), 1)

    def test_normalized_roundtrip_keeps_original_idr_and_time(self):
        offer = normalize_offer('blibli', {'title': 'Example', 'price': 100000, 'url': '/p/example'}, '2026-01-01T00:00:00Z')
        result = rank_offers([offer])
        self.assertEqual(result['groups']['IDR'][0]['price']['amount'], '100000')
        self.assertEqual(result['groups']['IDR'][0]['observed_at'], '2026-01-01T00:00:00Z')
        self.assertEqual(result['groups']['IDR'][0]['price']['currency_basis'], 'marketplace_adapter_contract')

    def test_explicit_currency_mismatch_stays_unranked_on_roundtrip(self):
        offer = normalize_offer('jd', {'title': 'Example', 'sku': '123', 'price': 20, 'currency': 'USD'})
        self.assertIsNone(offer['price']['amount'])
        result = rank_offers([offer])
        self.assertFalse(result['groups'])

    def test_minimum_range_and_page_minimum_are_not_exact_prices(self):
        offer = normalize_offer('blibli', {'title': 'Example', 'price': {'minPrice': 100000}, 'url': '/p/example'})
        self.assertIsNone(offer['price']['amount'])
        self.assertEqual(offer['price']['raw'], {'minPrice': 100000})
        offer = normalize_offer('taobao', {'title': 'Example', 'item_id': '123', 'price': '¥10',
                                          'price_basis': 'page_minimum_unverified'})
        self.assertFalse(rank_offers([offer])['groups'])

    def test_product_ids_are_marketplace_specific_and_binding_conflicts_rejected(self):
        self.assertIsNone(normalize_offer('taobao', {'title': 'Example', 'sku': '123', 'price': '¥10'})['url'])
        offer = normalize_offer('jd', {'title': 'Example', 'sku': '123', 'url': 'https://item.jd.com/456.html', 'price': '¥10'})
        self.assertIsNone(offer['price']['amount'])

    def test_blibli_structured_offer_roundtrip(self):
        row = {'name': 'Example', 'url': 'https://www.blibli.com/p/example/ps--ABC',
               'offers': {'@type': 'Offer', 'price': '100000.00', 'priceCurrency': 'IDR'}}
        normalized = normalize_offer('blibli', row)
        self.assertEqual(normalized['price']['amount'], '100000.00')
        self.assertEqual(rank_offers([normalized])['groups']['IDR'][0]['price']['amount'], '100000.00')

    def test_unknown_and_unused_conditions_are_not_invented(self):
        result = normalize_offer('goofish', {'title': 'unused example', 'item_id': '123', 'price': '¥10'})
        self.assertEqual(result['condition'], 'unknown')
        self.assertNotIn('possible_used_or_damaged', result['signals'])
        self.assertIn('secondhand_marketplace_condition_needs_review', result['signals'])

    def test_term_filter_precedes_deduplication(self):
        rows = [{'marketplace': 'jd', 'sku': '123', 'price': '¥20', 'title': title}
                for title in ['Wrong model', 'Desired model', 'Desired model']]
        result = rank_offers(rows, require_terms=['Desired'])
        self.assertEqual(len(result['groups']['CNY']), 1)
        self.assertEqual(result['groups']['CNY'][0]['title'], 'Desired model')

    def test_distinct_displayed_prices_are_retained_as_observations(self):
        rows = [{'marketplace': 'jd', 'sku': '123', 'price': price, 'title': 'Example'}
                for price in ['¥20', '¥30', '¥20']]
        self.assertEqual(len(rank_offers(rows)['groups']['CNY']), 2)


if __name__ == '__main__':
    unittest.main()
