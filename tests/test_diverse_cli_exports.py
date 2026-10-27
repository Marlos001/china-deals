import unittest
from unittest.mock import patch

from china_deals.cli import build_parser, run
from china_deals.ranking import rank_offers


class DiverseCliExports(unittest.TestCase):
    def test_filtered_population_is_retained_separately_and_safety_is_uniform(self):
        rows = [
            {'sku': '1', 'title': 'Sony WH-1000XM6 headphones', 'price': '3000'},
            {'sku': '2', 'title': 'Replacement ear pads for Sony WH-1000XM6', 'price': '10'},
            {'sku': '3', 'title': 'Sony WH-1000XM6 deposit', 'price': '10000'},
        ]
        receipt = {'status': 'ok', 'source_mode': 'guest_api', 'items': rows, 'warnings': []}
        with patch('china_deals.guest.search_guest', return_value=receipt):
            result, code = run(build_parser().parse_args(['search', 'Sony WH-1000XM6', '--markets', 'jd',
                '--zh-query', '索尼 WH-1000XM6 耳机', '--min-price', '1000', '--max-price', '9000',
                '--include-offers', '--currency', 'native']))
        self.assertEqual(code, 0)
        self.assertEqual(len(result['offers']), 1)
        self.assertEqual(result['offers'][0]['price']['amount'], '3000')
        self.assertEqual(len(result['filter_excluded_offers']), 2)
        for row in result['filter_excluded_offers']:
            self.assertIn('requested_filter_mismatch', row['ranking_exclusions'])
            self.assertFalse(rank_offers([row])['groups'])
        deposit = next(row for row in result['filter_excluded_offers'] if row['item_id'] == '3')
        self.assertIsNone(deposit['price']['amount'])
        self.assertIn('possible_deposit_or_installment_price', deposit['ranking_exclusions'])

    def test_generic_unknown_transaction_scope_is_identical_in_export(self):
        receipt = {'status': 'ok', 'source_mode': 'guest_api', 'warnings': [], 'items': [
            {'sku': '1', 'title': 'Unlisted Camera Z900 monthly installment', 'price': '100'}]}
        with patch('china_deals.guest.search_guest', return_value=receipt):
            result, _ = run(build_parser().parse_args(['search', 'Unlisted Camera Z900', '--markets', 'jd',
                '--zh-query', '相机 Z900', '--include-offers', '--currency', 'native']))
        self.assertIsNone(result['unranked'][0]['price']['amount'])
        self.assertIsNone(result['offers'][0]['price']['amount'])
        self.assertIn('possible_deposit_or_installment_price', result['offers'][0]['ranking_exclusions'])
