"""Cached observations stay useful without becoming current offer prices."""
import unittest
from unittest.mock import patch

from china_deals.cli import build_parser, markdown, run
from china_deals.models import normalize_offer
from china_deals.ranking import rank_offers


class SourceObservationTests(unittest.TestCase):
    def row(self, mode='indexed_product_block'):
        return {'marketplace': 'blibli', 'item_id': 'SYN-1', 'url': 'https://www.blibli.com/p/airpods/ps--SYN-1',
                'title': 'AirPods Max USB-C', 'price': '8799000', 'price_basis': 'displayed', 'currency': 'IDR',
                'source_mode': mode, 'source_detail': {'price_observation': {
                    'amount': '8799000', 'currency': 'IDR', 'crawl_age': '2 weeks ago'}}}

    def test_known_cache_modes_override_displayed_price_assertion(self):
        for mode in ('indexed_product_block', 'connector_product_open_cached', 'category_card', 'proxy_catalog'):
            with self.subTest(mode=mode):
                row = normalize_offer('blibli', self.row(mode))
                self.assertIsNone(row['price']['amount'])
                result = rank_offers([row], query='AirPods Max')
                self.assertFalse(result['groups'])
                self.assertEqual(result['unranked'][0]['price']['raw'], '8799000')

    def test_brl_and_markdown_show_observation_without_rank_or_extra_coupon(self):
        rates = {'base': 'BRL', 'rate_date': '2026-10-27', 'source': 'synthetic',
                 'brl_per_unit': {'CNY': '.8', 'IDR': '.0003', 'USD': '5'}}
        with patch('china_deals.cli.read_json', return_value=[self.row()]), patch('china_deals.fx.fetch_rates', return_value=rates):
            result, _ = run(build_parser().parse_args(['rank', 'input', '--query', 'AirPods Max']))
        self.assertFalse(result['groups'])
        row = result['unranked'][0]
        self.assertIsNone(row['brl']['product_cost'])
        self.assertEqual(row['brl']['source_observation_cost'], '2639.70')
        text = markdown(result)
        self.assertIn('Source observation: 8799000 IDR', text)
        self.assertIn('2639.70', text)
        self.assertIn('2 weeks ago', text)
        self.assertNotIn('coupon_estimates', row)

    def test_invalid_or_wrong_currency_observation_cannot_gain_brl_value(self):
        from china_deals.config import load_config
        from china_deals.fx import annotate_offers
        rates = {'base': 'BRL', 'rate_date': '2026-10-27',
                 'brl_per_unit': {'CNY': '.8', 'IDR': '.0003', 'USD': '5'}}
        for patch_value in ({'amount': '-1'}, {'amount': True}, {'amount': 'NaN'}, {'currency': 'CNY'}):
            row = self.row()
            row['source_detail']['price_observation'].update(patch_value)
            normalized = normalize_offer('blibli', row)
            annotate_offers([normalized], rates, load_config())
            self.assertNotIn('source_observation_cost', normalized['brl'])


if __name__ == '__main__':
    unittest.main()
