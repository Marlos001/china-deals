import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from china_deals.cli import main


def invoke(argv, markdown=False):
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(argv)
    return code, output.getvalue() if markdown else json.loads(output.getvalue())


class ProductCliTests(unittest.TestCase):
    def test_plan_is_offline_and_includes_all_requested_product_families(self):
        with patch('china_deals.guest.search_guest') as search:
            code, result = invoke(['plan', 'ASUS ROG Zephyrus'])
        self.assertEqual(code, 0)
        self.assertTrue(any('M16' in q for q in result['marketplace_queries']['blibli']))
        search.assert_not_called()

    @patch('china_deals.guest.search_guest')
    def test_search_and_imported_rerank_keep_accessories_out(self, search):
        search.return_value = {'status': 'ok', 'items': [
            {'title': 'AirPods Max ear pads', 'price': '100', 'sku': '1'},
            {'title': 'Apple AirPods Max USB-C', 'price': '4000', 'sku': '2'},
            {'title': 'AirPods Max deposit', 'price': '50', 'sku': '3'}], 'warnings': [],
            'source_mode': 'guest_product_page'}
        _, result = invoke(['search', 'AirPods Max', '--zh-query', '苹果 AirPods Max 耳机',
                            '--markets', 'jd', '--currency', 'native', '--include-offers'])
        self.assertEqual([r['item_id'] for r in result['groups']['CNY']], ['2'])
        for payload in (result, {k: v for k, v in result.items() if k != 'offers'}):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'result.json'
                path.write_text(json.dumps(payload))
                _, ranked = invoke(['rank', str(path), '--currency', 'native'])
                path.write_text(json.dumps(ranked))
                _, twice = invoke(['rank', str(path), '--currency', 'native'])
            self.assertEqual([r['item_id'] for r in twice['groups']['CNY']], ['2'])
            self.assertIsNone(next(r for r in twice['unranked'] if r['item_id'] == '3')['price']['amount'])
            self.assertEqual(twice['intent_query'], 'AirPods Max')

    @patch('china_deals.cli.read_json')
    def test_unranked_observations_are_visible_in_markdown(self, read):
        read.return_value = [{'marketplace': 'jd', 'sku': '1', 'title': 'Case iPhone 17 Pro Max', 'price': '10'}]
        code, result = invoke(['rank', 'file', '--query', 'iPhone 17 Pro Max', '--currency', 'native', '--format', 'markdown'], True)
        self.assertEqual(code, 0)
        self.assertIn('Unranked observations: 1', result)
        self.assertIn('different product or accessory', result)


if __name__ == '__main__':
    unittest.main()
