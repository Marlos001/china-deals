import unittest

from china_deals.products import assess_product, query_plan
from china_deals.ranking import rank_offers


class ProductTests(unittest.TestCase):
    def test_native_query_plans_and_no_english_china_fallback(self):
        for query in ('Iphone 17 pro max', 'Airpods max', 'Asus Rog Zephyrus'):
            plan = query_plan(query)
            self.assertFalse(plan['requires_agent_translation'])
            for market in ('taobao', 'jd', 'goofish'):
                self.assertTrue(all(any('\u3400' <= c <= '\u9fff' for c in q)
                                    for q in plan['marketplace_queries'][market]))
        self.assertEqual(query_plan('Something unknown')['marketplace_queries']['jd'], [])

    def test_iphone_whole_phone_vs_accessories_and_wrong_model(self):
        for title in ('iPhone 17 Pro Max 256GB', '苹果 iPhone17 Pro Max 512GB',
                      'iPhone 17 Pro Max 1TB with free case'):
            self.assertEqual(assess_product({'title': title}, 'iPhone 17 Pro Max')['status'], 'match')
        for title in ('Case iPhone 17 Pro Max', 'iPhone 17 Pro Max 钢化膜', 'Apple iPhone 17 Pro 256GB', 'iPhone 16 Pro Max'):
            self.assertEqual(assess_product({'title': title}, 'iPhone 17 Pro Max')['status'], 'mismatch')

    def test_airpods_case_is_not_headphones_but_included_case_is_allowed(self):
        for title in ('Apple AirPods Max USB-C', 'AirPods Max with Smart Case'):
            self.assertEqual(assess_product({'title': title}, 'AirPods Max')['status'], 'match')
        for title in ('Smart Case for AirPods Max', 'AirPods Max ear cushions', '苹果 AirPods Max 耳垫', 'Apple AirPods Pro'):
            self.assertEqual(assess_product({'title': title}, 'AirPods Max')['status'], 'mismatch')

    def test_all_zephyrus_families_and_obvious_non_zephyrus(self):
        for title in ('ASUS ROG Zephyrus G14', 'Zephyrus G15', 'Zephyrus G16', 'Zephyrus M16',
                      'ROG Zephyrus Duo 16', 'ROG Zephyrus S17', '华硕 ROG 幻14 笔记本'):
            self.assertEqual(assess_product({'title': title}, 'ASUS ROG Zephyrus')['status'], 'match')
        for title in ('ASUS ROG Strix G16', 'ASUS TUF A16', 'ROG Flow X16 GV601',
                      '华硕幻16翻转', 'Replacement fan for ASUS ROG Zephyrus G14'):
            self.assertEqual(assess_product({'title': title}, 'ASUS ROG Zephyrus')['status'], 'mismatch')

    def test_recommendations_in_description_do_not_establish_product_identity(self):
        result = assess_product({'title': 'HP Omen laptop', 'description': 'Recommended ASUS ROG Zephyrus G16'}, 'ROG Zephyrus')
        self.assertEqual(result['status'], 'uncertain')

    def test_deposit_is_separate_from_product_relevance(self):
        result = assess_product({'title': 'iPhone 17 Pro Max deposit'}, 'iPhone 17 Pro Max')
        self.assertEqual(result['status'], 'match')
        self.assertIn('possible_deposit_or_installment_price', result['price_scope_warnings'])

    def test_unicode_query_and_exact_zephyrus_model(self):
        self.assertEqual(query_plan('iPhone 17 Pro‑Max')['family'], 'iphone-17-pro-max')
        self.assertEqual(assess_product({'title': 'ASUS ROG Zephyrus G16'}, 'ROG Zephyrus G14')['status'], 'mismatch')
        self.assertEqual(assess_product({'title': 'Case for AirPods Max'}, 'AirPods Max')['status'], 'mismatch')

    def test_search_urls_are_not_product_links(self):
        result = rank_offers([{'marketplace': 'jd', 'title': 'iPhone 17 Pro Max',
                              'price': '1', 'url': 'https://search.jd.com/Search?keyword=iphone'}])
        self.assertFalse(result['groups'])
        self.assertIn('not_a_validated_product_route', result['unranked'][0]['ranking_exclusions'])

    def test_search_intent_prevents_cheapest_accessory_or_deposit_winning(self):
        rows = [{'marketplace': 'jd', 'sku': str(i), 'title': title, 'price': price}
                for i, title, price in [(1, 'Case iPhone 17 Pro Max', '10'),
                                       (2, 'iPhone 17 Pro Max deposit', '100'),
                                       (3, 'iPhone 17 Pro Max 256GB', '9000')]]
        result = rank_offers(rows, query='iPhone 17 Pro Max')
        self.assertEqual([r['item_id'] for r in result['groups']['CNY']], ['3'])
        self.assertEqual(len(result['unranked']), 2)
        self.assertTrue(all(r['ranking_exclusions'] for r in result['unranked']))
        deposit = next(r for r in result['unranked'] if r['item_id'] == '2')
        self.assertIsNone(deposit['price']['amount'])
        self.assertEqual(deposit['price']['raw'], '100')


if __name__ == '__main__':
    unittest.main()
