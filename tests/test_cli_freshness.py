import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from china_deals.cli import build_parser, run
from tests.test_brazil import payload
from tests.test_freshness import NOW, offer


class FreshnessCliTests(unittest.TestCase):
    def invoke(self, argv):
        return run(build_parser().parse_args(argv))

    def test_rank_fresh_filter_is_offline_with_native_currency(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'offers.json'
            path.write_text(json.dumps([offer(observed_at='2026-10-20T17:00:00Z')]))
            with patch('socket.socket', side_effect=AssertionError('offline command attempted network')):
                result, code = self.invoke(['rank', str(path), '--fresh-only', '--currency', 'native', '--as-of', NOW])
            self.assertEqual(code, 0)
            self.assertFalse(result['groups'])
            self.assertEqual(result['unranked'][0]['price_freshness']['status'], 'older_than_limit')

    def test_search_retains_source_time_and_export_exclusion(self):
        row = offer(marketplace='blibli', item_id='APF-70017-00964',
                    url='https://www.blibli.com/p/iphone/ps--APF-70017-00964', observed_at='2026-10-20T17:00:00Z')
        source = {'status': 'ok', 'source_mode': 'guest_api', 'items': [row]}
        with patch('china_deals.guest.search_guest', return_value=source):
            result, _ = self.invoke(['search', 'iPhone 17 Pro Max', '--markets', 'blibli', '--fresh-only',
                                     '--include-offers', '--currency', 'native', '--as-of', NOW])
        # The old source timestamp must never be replaced with fetch time.
        self.assertFalse(result['groups'])
        self.assertEqual(result['offers'][0]['observed_at'], '2026-10-20T17:00:00Z')
        self.assertIn('price_freshness_older_than_limit', result['offers'][0]['ranking_exclusions'])

    def test_brazil_compare_never_fetches_fx(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'cases.json'
            path.write_text(json.dumps(payload()))
            with patch('socket.socket', side_effect=AssertionError('offline command attempted network')):
                result, code = self.invoke(['brazil-compare', str(path)])
            self.assertEqual(code, 0)
            self.assertEqual(result['cases'][0]['savings_amount_brl'], '85.00')

    def test_cli_coupons_default_requires_fresh_primary_evidence(self):
        campaign = {'id': 'old', 'marketplace': 'jd', 'currency': 'CNY', 'discount': {'amount': '10'},
                    'confirmed': True, 'eligibility': 'confirmed', 'source_url': 'https://item.jd.com/123.html',
                    'observed_at': '2026-10-01T12:00:00Z'}
        with TemporaryDirectory() as directory:
            offers = Path(directory) / 'offers.json'
            rules = Path(directory) / 'rules.json'
            offers.write_text(json.dumps([offer()]))
            rules.write_text(json.dumps({'campaigns': [campaign]}))
            result, _ = self.invoke(['coupons', str(offers), '--rules', str(rules), '--currency', 'native', '--as-of', NOW])
            estimate = result['offers'][0]['coupon_estimates']
            self.assertIsNone(estimate['best_eligible'])
            self.assertEqual(estimate['campaigns'][0]['status'], 'potential')

    def test_refresh_cli_decorates_real_items_and_history_is_offline(self):
        from tests.test_refresh import NOW as REFRESH_NOW
        from tests.test_refresh import quote, receipt
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'watch.json'
            store = Path(directory) / 'history.sqlite'
            path.write_text(json.dumps([quote()]))
            with patch('china_deals.guest.get_guest_item', return_value=receipt()):
                result, code = self.invoke(['refresh', str(path), '--currency', 'native', '--store', str(store),
                                           '--fresh-only', '--as-of', REFRESH_NOW])
            self.assertEqual(code, 0)
            self.assertEqual(result['status'], 'ok')
            self.assertEqual(result['items'][0]['price']['amount'], '100')
            self.assertTrue(result['items'][0]['price_freshness_policy']['required'])
            with patch('socket.socket', side_effect=AssertionError('history must stay offline')):
                result, code = self.invoke(['history', '--store', str(store)])
            self.assertEqual(code, 0)
            self.assertEqual(len(result['observations']), 1)

    def test_promotion_capture_import_preserves_time_without_network(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'capture.json'
            text = 'Voucher 10% minimum spend 100000 IDR; members only'
            path.write_text(json.dumps({'url': 'https://www.blibli.com/promosi', 'capturedAt': NOW,
                                       'visibleText': text, 'visibleTextBytes': len(text.encode()), 'visibleTextTruncated': False}))
            with patch('socket.socket', side_effect=AssertionError('capture import must stay offline')):
                result, code = self.invoke(['promotions', 'blibli', 'https://www.blibli.com/promosi', '--from-browser-json', str(path)])
            self.assertEqual(code, 0)
            self.assertEqual(result['observed_at'], NOW)
            self.assertTrue(result['snippets'])
            self.assertNotIn('campaigns', result)
