"""Offline capture/CLI import preserves source time without acquisition or FX."""

import json
import unittest
from unittest.mock import patch

from china_deals.china_capture import parse_capture
from china_deals.cli import build_parser, run
from china_deals.marketplaces import item_url

STAMP = '2026-10-27T12:00:00Z'


def capture(market, **changes):
    url = item_url(market, '123')
    body = ('<html><head><link rel="canonical" href="' + url + '">'
            '<meta property="og:url" content="' + url + '">'
            '<meta property="og:type" content="product">'
            '<meta property="og:title" content="Sony WH-1000XM6">'
            '<meta property="product:price:amount" content="100"></head><body>商品</body></html>')
    return {'url': url, 'capturedAt': STAMP, 'html': body,
            'htmlBytes': len(body.encode('utf-8')), 'htmlTruncated': False, **changes}


class ChinaCapture(unittest.TestCase):
    def test_exact_capture_identity_and_historical_time_remain_unpriced(self):
        for market in ('tmall', '1688', 'weidian'):
            with self.subTest(market=market):
                row = parse_capture(capture(market), market, item_url(market, '123'))
                self.assertEqual(row['item_id'], '123')
                self.assertEqual(row['observed_at'], STAMP)
                self.assertIsNone(row['price'])
                self.assertFalse(row['source_detail']['capture_provenance']['network_request_performed'])
                self.assertNotIn('html', row['source_detail'])

    def test_invalid_capture_cannot_mint_identity_or_current_time(self):
        for market in ('tmall', '1688', 'weidian'):
            for changes in ({'url': item_url(market, '456')}, {'capturedAt': None},
                            {'capturedAt': '2026-10-27T12:00:00'}, {'htmlTruncated': True},
                            {'htmlTruncated': None}, {'htmlBytes': True}, {'htmlBytes': 1}):
                with self.subTest(market=market, changes=changes), self.assertRaises(ValueError):
                    parse_capture(capture(market, **changes), market, item_url(market, '123'))

    def test_captured_challenge_is_not_a_product(self):
        body = '<html><title>Security verification</title><body>Please verify you are human</body></html>'
        cap = capture('weidian', html=body, htmlBytes=len(body.encode()))
        with self.assertRaises(ValueError):
            parse_capture(cap, 'weidian', item_url('weidian', '123'))

    def test_default_cli_import_is_offline_including_coupon_decoration(self):
        for market in ('tmall', '1688', 'weidian'):
            for currency in ([], ['--currency', 'native']):
                def read(path):
                    return {'campaigns': []} if path == 'rules.json' else {'value': capture(market)}
                with patch('socket.socket', side_effect=AssertionError('capture attempted network')), \
                        patch('china_deals.fx.fetch_rates', side_effect=AssertionError('capture fetched FX')), \
                        patch('china_deals.cli.read_json', side_effect=read) as reader:
                    args = build_parser().parse_args(['detail', market, '123', '--from-browser-json', 'capture.json',
                                                      '--coupons-from-json', 'rules.json', *currency])
                    result, code = run(args)
                self.assertEqual(code, 0)
                self.assertEqual(reader.call_count, 2)
                row = result['items'][0]
                self.assertEqual(row['observed_at'], STAMP)
                self.assertIsNone(row['price']['amount'])
                self.assertIn('coupon_estimates', row)
                self.assertEqual(result['access']['attempts'], [])
                json.dumps(result, allow_nan=False)
