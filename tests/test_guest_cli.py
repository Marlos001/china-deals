import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from test_hardware import G16_2024

from china_deals.cli import main, markdown
from china_deals.ranking import rank_offers


def invoke(argv):
    out = io.StringIO()
    with redirect_stdout(out):
        code = main(argv)
    return code, json.loads(out.getvalue())


class GuestCliTests(unittest.TestCase):
    @patch('china_deals.adapters.search_marketplace')
    @patch('china_deals.guest.search_guest')
    def test_default_guest_uses_chinese_override_and_blocks_english(self, guest, native):
        guest.return_value = {'status': 'discovery_only', 'items': [], 'warnings': []}
        code, result = invoke(['search', 'Zephyrus G16', '--markets', 'jd', '--currency', 'native'])
        self.assertEqual(code, 3)
        self.assertEqual(result['sources'][0]['error']['code'], 'chinese_query_required')
        guest.assert_not_called()
        invoke(['search', 'Zephyrus G16', '--zh-query', '华硕 幻16', '--markets', 'jd', '--currency', 'native'])
        self.assertEqual(guest.call_args.args[1], '华硕 幻16')
        native.assert_not_called()

    @patch('china_deals.guest.get_guest_item')
    @patch('china_deals.guest.search_guest')
    def test_blibli_hydration_uses_native_url_and_index_price_stays_unranked(self, guest, detail):
        url = 'https://www.blibli.com/p/example/ps--ABC-123'
        guest.return_value = {'status': 'discovery_only', 'items': [{'item_id': 'ABC-123', 'title': 'G16', 'url': url,
                              'price': 'Rp100000', 'source_mode': 'search_index'}], 'warnings': []}
        detail.return_value = {'items': []}
        _, result = invoke(['search', 'G16', '--markets', 'blibli', '--hydrate', '1', '--currency', 'native'])
        self.assertEqual(detail.call_args.args[1], url)
        self.assertEqual(result['groups'], {})
        self.assertIsNone(result['unranked'][0]['price']['amount'])

    @patch('china_deals.browser_guest.search_browser_guest')
    def test_explicit_browser_path_receives_filters_and_executable(self, browser):
        browser.return_value = {'status': 'blocked', 'items': [], 'warnings': []}
        invoke(['search', '幻16', '--markets', 'jd', '--guest-engine', 'browser', '--browser-executable', '/usr/bin/chromium',
                '--max-price', '9000', '--currency', 'native'])
        self.assertEqual(browser.call_args.kwargs['executable_path'], '/usr/bin/chromium')
        self.assertEqual(browser.call_args.kwargs['filters']['max_price'], '9000')

    @patch('china_deals.shipping.fansbuy_quotes')
    def test_blibli_shipping_excluded_without_network_or_weight(self, quotes):
        code, result = invoke(['shipping', '--market', 'blibli'])
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'excluded_by_market_policy')
        quotes.assert_not_called()

    def test_price_descending_sorts_before_cutoff(self):
        offers = [{'marketplace': 'jd', 'sku': str(i), 'title': 'Laptop', 'price': str(i)} for i in range(1, 151)]
        self.assertEqual(rank_offers(offers, limit=1, descending=True)['groups']['CNY'][0]['price']['amount'], '150')
        self.assertEqual(len(rank_offers(offers, limit=None)['groups']['CNY']), 150)

    def test_comparison_preserves_contradictory_observations(self):
        first = {'marketplace': 'jd', 'sku': '123', 'title': G16_2024, 'price': '12000',
                 'url': 'https://item.jd.com/123.html', 'source_mode': 'listing_content'}
        second = dict(first, description='RAM 16GB')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'offers.json'
            path.write_text(json.dumps([first, second]))
            _, result = invoke(['compare', str(path), '--currency', 'native'])
        self.assertEqual(len(result['incomplete']), 1)
        self.assertIn('ram_gb', result['incomplete'][0]['hardware']['conflicts'])
        self.assertEqual(len(result['groups'][0]['candidates']), 1)

    def test_cli_preserves_structured_hardware_conflicts(self):
        item = {'marketplace': 'jd', 'sku': '123', 'title': G16_2024, 'price': '12000',
                'url': 'https://item.jd.com/123.html', 'source_mode': 'listing_content',
                'hardware': {'verified': True, 'evidence': {'ram_gb': [{'excerpt': 'RAM 16GB'}]}}}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'offers.json'
            path.write_text(json.dumps([item]))
            _, result = invoke(['compare', str(path), '--currency', 'native'])
        self.assertFalse(result['groups'])
        self.assertEqual(result['incomplete'][0]['hardware']['conflicts']['ram_gb'], [32, 16])

    @patch('china_deals.guest.search_guest')
    def test_api_envelope_provenance_survives_normalization(self, guest):
        guest.return_value = {'status': 'ok', 'source_mode': 'guest_api', 'items': [
            {'title': G16_2024, 'price': 'Rp20000000', 'url': 'https://www.blibli.com/p/example/ps--ABC', 'sku': 'ABC'}], 'warnings': []}
        _, result = invoke(['search', 'Zephyrus G16', '--markets', 'blibli', '--currency', 'native', '--include-offers'])
        self.assertEqual(result['offers'][0]['source_mode'], 'guest_api')

    def test_guest_detail_enters_hardware_review_and_markdown_works(self):
        item = {'marketplace': 'jd', 'sku': '123', 'title': 'ROG 幻16 RTX 5060 32GB RAM 1TB SSD',
                'price': None, 'source_mode': 'guest_product_page'}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'offers.json'
            path.write_text(json.dumps([item]))
            code, result = invoke(['compare', str(path), '--currency', 'native'])
        self.assertEqual(code, 0)
        self.assertEqual(len(result['incomplete']), 1)
        self.assertEqual(result['discoveries'], [])
        self.assertIn('incomplete: 1', markdown(result))


if __name__ == '__main__':
    unittest.main()
