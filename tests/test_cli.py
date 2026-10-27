import io
import json
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from china_deals.cli import _md_cell, captured_shipping, main


def invoke(argv):
    out = io.StringIO()
    with redirect_stdout(out):
        code = main(argv)
    return code, json.loads(out.getvalue())


class CliTests(unittest.TestCase):
    def test_schema_without_backend(self):
        code, result = invoke(['schema'])
        self.assertEqual(code, 0)
        self.assertIn('blibli', result['marketplaces'])
        self.assertNotIn('bilibili', result['marketplaces'])

    def test_estimate_uses_explicit_fx_and_gross_up(self):
        code, result = invoke(['estimate', '--goods-cny', '100', '--freight-cny', '20',
                               '--cny-brl', '1', '--usd-brl', '5', '--icms-rate', '.2'])
        self.assertEqual(code, 0)
        self.assertEqual(result['total_brl'], '240.00')

    def test_bad_numeric_input_is_json_error(self):
        code, result = invoke(['shipping', '--weight-g', 'NaN'])
        self.assertEqual(code, 2)
        self.assertIn('error', result)

    @patch('china_deals.cli.read_json', return_value=[{'marketplace': 'jd', 'sku': '123', 'title': 'Example', 'price': '¥20'}])
    def test_imported_ranking_provenance(self, unused):
        code, result = invoke(['rank', 'test.json'])
        self.assertEqual(code, 0)
        self.assertEqual(result['dataset_origin'], 'imported_json')
        self.assertIsNone(result['groups']['CNY'][0]['observed_at'])

    def test_captured_rate_must_match_package_and_destination(self):
        capture = {'request': {'weight_g': 1000, 'dimensions_cm': [20, 20, 15], 'destination': 'BR', 'categories': []},
                   'response': {'code': 0, 'data': []}, 'captured_at': '2026-10-27T13:22:00Z'}
        self.assertEqual(captured_shipping(capture, '1000', ['20', '20', '15'], [])[0], capture['response'])
        for changed in [dict(capture, request=dict(capture['request'], destination='US')),
                        dict(capture, request=dict(capture['request'], weight_g=500)),
                        dict(capture, request=dict(capture['request'], dimensions_cm=[10, 10, 10]))]:
            with self.assertRaises(ValueError):
                captured_shipping(changed, 1000, [20, 20, 15], [])
        with self.assertRaises(ValueError):
            captured_shipping({'code': 0, 'data': []}, 1000, [20, 20, 15], [])

    def test_markdown_listing_text_is_not_active_markup(self):
        result = _md_cell('![track](https://evil.test/a.gif) [buy](https://evil.test) <img>')
        self.assertIn('\\!\\[track\\]', result)
        self.assertIn('&lt;img&gt;', result)

    @patch('china_deals.adapters.get_item')
    def test_taobao_field_table_is_one_detail_with_unverified_minimum(self, getter):
        getter.return_value = {'marketplace': 'taobao', 'status': 'ok', 'warnings': [], 'error': None,
                               'items': [{'field': '商品名称', 'value': 'Example'}, {'field': '价格', 'value': '¥20'},
                                         {'field': 'ID', 'value': '123'}, {'field': '链接', 'value': 'https://item.taobao.com/item.htm?id=123'}]}
        code, result = invoke(['detail', 'taobao', '123'])
        self.assertEqual(code, 0)
        self.assertEqual(len(result['items']), 1)
        self.assertIsNone(result['items'][0]['price']['amount'])
        self.assertEqual(len(result['source_fields']), 4)

    @patch('china_deals.adapters.get_item')
    def test_jd_page_amount_is_not_a_bound_product_price(self, getter):
        getter.return_value = {'marketplace': 'jd', 'status': 'ok', 'warnings': [], 'error': None,
                               'items': [{'field': '商品名称', 'value': 'Example'}, {'field': '价格', 'value': '¥9.90'},
                                         {'field': 'SKU', 'value': '123'}, {'field': '链接', 'value': 'https://item.jd.com/123.html'}]}
        code, result = invoke(['detail', 'jd', '123'])
        self.assertEqual(code, 0)
        self.assertIsNone(result['items'][0]['price']['amount'])
        self.assertEqual(result['items'][0]['price']['raw'], '¥9.90')
        self.assertEqual(result['items'][0]['price']['basis'], 'unbound_page_amount')

    @patch('china_deals.adapters.search_marketplace')
    def test_one_source_failure_preserves_other_results(self, search):
        search.side_effect = [ValueError('failure'), {'marketplace': 'jd', 'status': 'ok', 'warnings': [], 'error': None,
                                                    'items': [{'title': 'Example', 'sku': '123', 'price': '¥20'}]}]
        code, result = invoke(['search', 'Example', '--markets', 'taobao,jd'])
        self.assertEqual(code, 3)
        self.assertEqual(result['sources'][0]['status'], 'error')
        self.assertEqual(len(result['groups']['CNY']), 1)
        self.assertEqual(result['sources'][1]['item_count'], 1)
        self.assertNotIn('items', result['sources'][1])
        self.assertNotIn('offers', result)


if __name__ == '__main__':
    unittest.main()
