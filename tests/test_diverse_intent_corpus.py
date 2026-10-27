import json
import unittest
from pathlib import Path
from unittest.mock import patch

from china_deals.products import query_plan
from china_deals.ranking import rank_offers


class DiverseIntentCorpus(unittest.TestCase):
    def test_frozen_multilingual_cases_through_repeated_ranking(self):
        path = Path(__file__).parent / 'fixtures' / 'diverse-intent-cases.synthetic.json'
        corpus = json.loads(path.read_text())
        self.assertTrue(corpus['synthetic_offline_only'])
        with patch('socket.socket', side_effect=AssertionError('offline corpus attempted network')):
            for case in corpus['cases']:
                with self.subTest(case=case['id'], lang=case['lang']):
                    result = rank_offers([case['input']], query=case['query'])
                    self.assertEqual(bool(result['groups']), case['expected_ranked'])
                    rows = [row for group in result['groups'].values() for row in group] + result['unranked']
                    result = rank_offers(rows)
                    self.assertEqual(bool(result['groups']), case['expected_ranked'])

    def test_fresh_adversarial_review_cases_through_three_ranking_passes(self):
        directory = Path(__file__).parent / 'fixtures'
        corpus = {'cases': []}
        for name in ('selected-intent-review.synthetic.json', 'axis-intent-review.synthetic.json'):
            corpus['cases'].extend(json.loads((directory / name).read_text())['cases'])
        with patch('socket.socket', side_effect=AssertionError('offline review attempted network')):
            for case in corpus['cases']:
                with self.subTest(case=case['id']):
                    rows = [case['input']]
                    for iteration in range(3):
                        result = rank_offers(rows, query=case['query'] if iteration == 0 else None)
                        self.assertEqual(bool(result['groups']), case['expected_ranked'])
                        rows = [row for group in result['groups'].values() for row in group] + result['unranked']

    def test_bounded_plans_preserve_scope_and_have_chinese_queries(self):
        for query in ('Steam Deck OLED 1TB', 'Sony WH-1000XM6', 'AMD Ryzen 7 9800X3D',
                      'RTX 5070 Ti 16GB desktop graphics card', 'DJI Mini 4 Pro RC 2', 'Nintendo Switch 2'):
            plan = query_plan(query)
            self.assertTrue(plan['family'])
            for market in ('jd', 'taobao', 'goofish'):
                self.assertTrue(plan['marketplace_queries'][market])
                for text in plan['marketplace_queries'][market]:
                    self.assertIn(query, text)
                    self.assertRegex(text, '[\u3400-\u9fff]')

    def test_unfamiliar_intent_stays_visible_without_claimed_match(self):
        query = 'Unlisted Camera Z900 Ultra'
        row = {'marketplace': 'jd', 'sku': '123', 'title': 'USB cable', 'price': '10'}
        result = rank_offers([row], query=query)
        self.assertFalse(result['groups'])
        self.assertEqual(result['unranked'][0]['price']['amount'], '10')
        self.assertEqual(result['unranked'][0]['relevance']['reasons'], ['unsupported_product_intent'])
        self.assertTrue(rank_offers([row])['groups'])

    def test_package_controller_bundle_and_memory_roles_remain_distinct(self):
        for query, good, bad in (
            ('AMD Ryzen 9800X3D boxed', 'AMD Ryzen 9800X3D box processor', 'AMD Ryzen 9800X3D tray CPU'),
            ('DJI Mini 4 Pro RC 2', 'DJI Mini 4 Pro DJI RC 2 drone', 'RC 2 controller only for DJI Mini 4 Pro'),
            ('DJI Mini 4 Pro Fly More Combo', 'DJI Mini 4 Pro Fly More Combo drone', 'DJI Mini 4 Pro standard drone'),
            ('ROG Zephyrus G16 RAM 32GB SSD 1TB', 'ROG Zephyrus G16 RAM 32GB SSD 1TB', 'ROG Zephyrus G16 RAM 1TB SSD 32GB'),
        ):
            for title, expected in ((good, True), (bad, False)):
                with self.subTest(query=query, title=title):
                    row = {'marketplace': 'jd', 'sku': '123', 'title': title, 'price': '100'}
                    self.assertEqual(bool(rank_offers([row], query=query)['groups']), expected)
