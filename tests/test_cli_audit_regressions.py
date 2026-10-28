import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from china_deals.cli import main


def invoke(args):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = main(args)
    return code, output.getvalue()


TITLE = ('ASUS ROG Zephyrus G16 (2024) GU605MI Intel Core Ultra 9 185H '
         'RTX 4070 Laptop GPU 8GB TGP 105W 32GB LPDDR5X 1TB SSD '
         '16-inch 2560x1600 OLED 240Hz brand new')


class CliAuditTests(unittest.TestCase):
    def test_compare_cny_scenario_and_usd_hold_in_json_and_markdown(self):
        rows = [
            {'marketplace': 'jd', 'sku': '123', 'url': 'https://item.jd.com/123.html',
             'title': TITLE, 'price': '12000', 'source_mode': 'listing_content'},
            {'marketplace': 'aliexpress', 'item_id': '1005001234567890',
             'url': 'https://www.aliexpress.com/item/1005001234567890.html',
             'title': TITLE, 'price': '1000', 'currency': 'USD', 'source_mode': 'listing_content'},
        ]
        rates = {'base': 'BRL', 'rate_date': '2026-10-27', 'source': 'offline-test',
                 'brl_per_unit': {'CNY': '1', 'USD': '5', 'IDR': '0.0003'}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, data in [('offers.json', rows), ('fx.json', rates),
                               ('config.json', {'marketplaces': {'aliexpress': {'shipping': 'fansbuy'}}})]:
                (root / name).write_text(json.dumps(data))
            args = ['compare', str(root / 'offers.json'), '--config', str(root / 'config.json'),
                    '--fx-from-json', str(root / 'fx.json'), '--freight-cny', '100', '--icms-rate', '.2']
            code, output = invoke(args)
            self.assertEqual(code, 0, output)
            result = json.loads(output)
            candidates = [c for g in result['groups'] for c in g['candidates']]
            cny = next(c for c in candidates if c['marketplace'] == 'jd')['landed_scenario']
            usd = next(c for c in candidates if c['marketplace'] == 'aliexpress')['landed_scenario']
            self.assertEqual(cny['assumptions']['inputs']['goods_cny'], '12000')
            self.assertEqual(cny['fx_provenance']['source'], 'offline-test')
            self.assertIsNone(usd['total_brl'])
            self.assertEqual(usd['reason'], 'verified_cny_goods_amount_required')
            code, markdown = invoke(args + ['--format', 'markdown'])
            self.assertEqual(code, 0)
            for value in ('Landed scenario: BRL', 'Assumptions:', 'offline-test', 'Landed scenario: unknown'):
                self.assertIn(value, markdown)

    @patch('china_deals.guest.search_guest')
    def test_filter_exclusion_does_not_change_acquisition_status(self, search):
        search.return_value = {'status': 'ok', 'items': [
            {'title': 'Laptop', 'sku': '123', 'price': '100', 'condition': 'used'}], 'warnings': []}
        code, output = invoke(['search', '电脑', '--markets', 'jd', '--currency', 'native',
                               '--min-price', '200', '--include-offers'])
        result = json.loads(output)
        self.assertEqual(code, 0)
        source = result['sources'][0]
        self.assertEqual((source['status'], source['acquired_item_count'], source['item_count'],
                          source['filter_excluded_count']), ('ok', 1, 0, 1))
        self.assertEqual(len(result['filter_excluded_offers']), 1)
        self.assertEqual(result['offers'], [])

    @patch('china_deals.guest.search_guest')
    def test_malformed_row_keeps_source_status_but_reports_partial_failure(self, search):
        search.return_value = {'status': 'ok', 'items': [{'title': 'Laptop', 'price': '100'}, None], 'warnings': []}
        code, output = invoke(['search', '电脑', '--markets', 'jd', '--currency', 'native'])
        source = json.loads(output)['sources'][0]
        self.assertEqual(code, 3)
        self.assertEqual((source['status'], source['acquired_item_count'], source['malformed_item_count']), ('ok', 2, 1))

    def test_missing_store_is_error_and_empty_store_is_success(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'history.sqlite'
            code, output = invoke(['history', '--store', str(path)])
            self.assertEqual(code, 2)
            self.assertIn('does not exist', json.loads(output)['error']['message'])
            self.assertFalse(path.exists())
            sqlite3.connect(path).close()
            code, output = invoke(['history', '--store', str(path), '--limit', '50'])
            self.assertEqual((code, json.loads(output)['observations']), (0, []))
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                invoke(['history', '--store', str(path), '--limit', '51'])

    def test_manual_shipping_markdown_does_not_show_quote_table(self):
        code, output = invoke(['shipping', '--market', 'aliexpress', '--format', 'markdown'])
        self.assertEqual(code, 0)
        self.assertIn('manual', output)
        self.assertIn('no Fansbuy freight quote requested', output)
        self.assertNotIn('| Route |', output)
        self.assertNotIn('routes rejected', output)
