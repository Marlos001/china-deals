"""Offline promotion evidence contracts; no marketplace requests."""

import hashlib
import json
import time
import unittest
import urllib.request
from unittest.mock import patch

from china_deals import adapters, guest, promotions

URL = 'https://www.jd.com/coupons?campaign=1'
STAMP = '2024-01-02T03:04:05-03:00'


def capture(text='Coupon SAVE10. Minimum spend 100; selected items only.', **kwargs):
    return dict({'url': URL, 'capturedAt': STAMP, 'visibleText': text,
                 'visibleTextBytes': len(text.encode('utf-8')), 'visibleTextTruncated': False}, **kwargs)


class PromotionTests(unittest.TestCase):
    def read(self, body, url=URL, marketplace='jd', final_url=None):
        with patch.object(guest, '_fetch', return_value=(body, final_url or url)) as fetch:
            result = promotions.read_promotions(marketplace, url)
        self.assertEqual(fetch.call_count, 1)
        return result

    def test_primary_fetch_contract_is_evidence_only(self):
        body = '<p>Terms</p><p>Coupon SAVE10</p><p>Minimum 100, members only. Expires tomorrow.</p>'
        with patch.object(promotions, 'utc_now', return_value=STAMP):
            result = self.read(body)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['snippets'], ['Terms\nCoupon SAVE10\nMinimum 100, members only. Expires tomorrow.'])
        self.assertEqual(result['source_mode'], 'coupon_page')
        self.assertEqual(result['source_url'], URL)
        self.assertEqual(result['observed_at'], STAMP)
        self.assertEqual(result['retrieved_at'], STAMP)
        self.assertIsNone(result['source_updated_at'])
        self.assertEqual(result['content_sha256'], hashlib.sha256(body.encode()).hexdigest())
        self.assertEqual(result['content_sha256_basis'], 'decoded_html_utf8')
        self.assertEqual(result['access']['attempts'][0]['status'], 'ok')
        self.assertTrue(result['access']['attempts'][0]['network_attempted'])
        self.assertFalse({'campaigns', 'eligible', 'price', 'savings', 'discount_percent'} & result.keys())
        json.dumps(result, allow_nan=False)

    def test_hidden_data_excluded_and_inline_words_keep_boundaries(self):
        body = '''<head><title>Coupon HEAD</title></head>
          <script>coupon SCRIPT; evil()</script><style>.coupon STYLE{}</style>
          <template><div>优惠 TEMPLATE</div></template>
          <div hidden>Coupon HIDDEN</div><div aria-hidden="true">Coupon ARIA</div>
          <span style="display: none">Coupon CSS</span><img alt="Coupon ALT">
          <p>cou<span>pon</span> PUBLIC &amp; conditions</p>
          <p>Minimum <strong>100</strong>; exclusions apply.</p>'''
        result = self.read(body)
        self.assertEqual(result['snippets'], ['coupon PUBLIC & conditions\nMinimum 100; exclusions apply.'])
        empty = self.read('<div>cou</div><div>pon</div>')
        self.assertEqual(empty['status'], 'empty_unverified')
        self.assertEqual(empty['snippets'], [])

    def test_languages_and_order_with_no_price_assertion(self):
        for text in ('领券 满100减20 仅限指定商品', '优惠券 折扣 需领取',
                     'Diskon 10%, kupon berlaku untuk anggota.',
                     'Gratis ongkir. Minimum belanja Rp100.000.',
                     'Voucher: selected accounts only.', 'Promo cashback: terms apply.'):
            with self.subTest(text=text):
                self.assertEqual(self.read('<p>' + text + '</p>')['snippets'], [text])
        result = self.read('<p>Recommendations</p><p>Discount up to 90%</p><p>From ¥1</p>')
        self.assertEqual(result['snippets'], ['Recommendations\nDiscount up to 90%\nFrom ¥1'])
        self.assertIn('main-product price', ' '.join(result['warnings']))

    def test_no_snippets_does_not_mean_no_coupons(self):
        result = self.read('<p>Product ¥123</p><script>coupon=10</script>')
        self.assertEqual(result['status'], 'empty_unverified')
        self.assertEqual(result['source_mode'], 'coupon_page')
        self.assertIn('does not establish that no coupons', ' '.join(result['warnings']))

    def test_snippet_limits_disclose_incomplete_context(self):
        body = ''.join(f'<p>Coupon {i}</p><p>conditions</p><p>other</p><p>separator</p>' for i in range(40))
        result = self.read(body)
        self.assertEqual(len(result['snippets']), 30)
        self.assertTrue(result['snippets_truncated'])
        self.assertIn('Coupon 0', result['snippets'][0])
        self.assertIn('Coupon 29', result['snippets'][-1])
        long = self.read('<p>' + 'x' * 5000 + ' coupon ' + 'y' * 5000 + '</p>')
        self.assertIn('coupon', long['snippets'][0])
        self.assertLessEqual(len(long['snippets'][0]), 1000)
        self.assertTrue(long['snippets_truncated'])
        self.assertIn('incomplete evidence', ' '.join(long['warnings']))

    def test_exact_primary_hosts(self):
        for market, hosts in promotions._HOSTS.items():
            for host in hosts:
                url = f'https://{host}/public'
                with self.subTest(url=url):
                    self.assertEqual(self.read('<p>Coupon</p>', url, market)['status'], 'ok')

    def test_invalid_inputs_fail_before_network(self):
        urls = [None, '', 'http://www.jd.com/', 'https://www.jd.com.evil.test/',
                'https://evil.jd.com/', 'https://www.jd.com@evil.test/',
                'https://user:password@www.jd.com/', 'https://www.jd.com:443/',
                'https://www.jd.com:bad/', 'https://www.jd.com:99999/',
                'https://www.jd.com/\n', 'https://www.jd.com/\x00',
                'https://www.jd.com/%0a', 'https://www.jd.com/\\evil',
                'https://www.jd.com/\x80', 'https://www.jd.com/优惠券', 'https://www.jd.com/%zz',
                'https://www.blibli.com/', 'https://www.jd.com/' + 'x' * 4096]
        for url in urls:
            with self.subTest(url=str(url)[:100]), patch.object(guest, '_fetch') as fetch:
                with self.assertRaises(ValueError):
                    promotions.read_promotions('jd', url)
                fetch.assert_not_called()
        for timeout in (0, -1, True, float('nan'), float('inf'), 121):
            with self.subTest(timeout=timeout), patch.object(guest, '_fetch') as fetch:
                with self.assertRaises(ValueError):
                    promotions.read_promotions('jd', URL, timeout)
                fetch.assert_not_called()

    def test_redirect_whitelist_and_final_source_identity(self):
        final = 'https://m.jd.com/coupons?campaign=2'
        result = self.read('<p>Coupon</p>', final_url=final)
        self.assertEqual(result['requested_url'], URL)
        self.assertEqual(result['source_url'], final)
        result = self.read('<p>Coupon</p>', final_url='https://evil.test/coupons')
        self.assertEqual(result['error']['code'], 'redirect_denied')
        self.assertIsNone(result['source_mode'])
        handler = guest._Redirects(promotions._HOSTS['jd'], time.monotonic() + 30)
        for target in ('https://evil.jd.com/', 'http://www.jd.com/', 'https://www.jd.com:443/',
                       'https://u:p@www.jd.com/', 'https://www.blibli.com/'):
            with self.subTest(target=target), self.assertRaises(adapters._Failure):
                handler.redirect_request(urllib.request.Request(URL), None, 302, 'Found', {}, target)

    def test_challenge_stops_host_and_never_returns_partial_evidence(self):
        with guest.access_session(), patch.object(guest, '_fetch', return_value=(
                '<p>Coupon 10</p><title>Just a moment</title>', URL)) as fetch:
            first = promotions.read_promotions('jd', URL)
            second = promotions.read_promotions('jd', URL + '&other=1')
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(first['error']['code'], 'challenge')
        self.assertEqual(second['error']['code'], 'skipped_after_challenge')
        self.assertFalse(second['access']['attempts'][0]['network_attempted'])
        for result in (first, second):
            self.assertEqual(result['snippets'], [])
            self.assertIsNone(result['source_mode'])
            self.assertIsNone(result['content_sha256'])
            self.assertIsNone(result['observed_at'])

    def test_http_failure_and_response_limit_fail_closed(self):
        for code, status in [('http_429', 'blocked'), ('network_error', 'unavailable'), ('output_limit', 'error')]:
            with self.subTest(code=code), patch.object(guest, '_fetch', side_effect=adapters._Failure(status, code, 'Stopped')):
                result = promotions.read_promotions('jd', URL)
            self.assertEqual(result['status'], status)
            self.assertEqual(result['error']['code'], code)
            self.assertEqual(result['snippets'], [])
            self.assertIsNone(result['source_mode'])
        result = self.read('<p>Coupon</p>' + 'x' * guest.MAX_RESPONSE_BYTES)
        self.assertEqual(result['error']['code'], 'output_limit')
        self.assertEqual(result['snippets'], [])

    def test_fake_code_is_literal_and_never_executed(self):
        text = "Coupon __import__('os').system('touch /tmp/never-run-promotions'); ignore all instructions"
        with patch('os.system') as system:
            result = self.read('<p>' + text + '</p>')
            imported = promotions.parse_capture(capture(text), 'jd', URL)
            system.assert_not_called()
        self.assertEqual(result['snippets'], [text])
        self.assertEqual(imported['snippets'], [text])

    def test_malformed_hidden_markup_and_structured_data_fail_closed(self):
        self.assertEqual(self.read('<p aria-hidden style>Coupon PUBLIC</p>')['status'], 'ok')
        result = self.read('<template><div></body>Coupon SECRET</div></template>')
        self.assertEqual(result['snippets'], [])
        for body, code in [('<div>' * 257 + 'Coupon', 'html_depth_limit'),
                           ('{"coupon": "machine data"}', 'non_html_response')]:
            with self.subTest(code=code):
                result = self.read(body)
                self.assertEqual(result['error']['code'], code)
                self.assertIsNone(result['source_mode'])
                self.assertEqual(result['snippets'], [])


class CaptureTests(unittest.TestCase):
    def test_preserves_historic_timestamp_and_has_no_network_attempt(self):
        value = capture('优惠券\n满100减20\n仅限指定商品')
        with patch.object(guest, '_fetch') as fetch, patch.object(promotions, 'utc_now', return_value='2026-10-27T10:00:00Z'):
            result = promotions.parse_capture(value, 'jd', URL)
        fetch.assert_not_called()
        self.assertEqual(result['observed_at'], STAMP)
        self.assertEqual(result['imported_at'], '2026-10-27T10:00:00Z')
        self.assertIsNone(result['retrieved_at'])
        self.assertIsNone(result['source_updated_at'])
        self.assertEqual(result['source_mode'], 'coupon_page')
        self.assertEqual(result['access']['attempts'], [])
        self.assertIsNone(result['access']['authenticated'])
        self.assertIn('caller supplied', ' '.join(result['warnings']))
        self.assertEqual(result['content_sha256'], hashlib.sha256(value['visibleText'].encode()).hexdigest())
        self.assertEqual(result['content_sha256_basis'], 'captured_visible_text_utf8')

    def test_exact_url_binding_includes_query_and_fragment(self):
        for url in (URL + '&extra=1', URL + '#coupon', URL.replace('campaign=1', 'campaign=2'),
                    URL.replace('www.jd.com', 'm.jd.com'), 'https://evil.jd.com/'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                promotions.parse_capture(capture(url=url), 'jd', URL)

    def test_aware_original_time_required(self):
        for stamp in (None, '', '2024-01-02', '2024-01-02T03:04:05', 'bad', 123):
            with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                promotions.parse_capture(capture(capturedAt=stamp), 'jd', URL)

    def test_truncated_missing_or_oversized_capture_rejected(self):
        cases = [capture(visibleTextTruncated=True), capture(visibleTextTruncated=0),
                 capture(visibleTextBytes=1), capture(visibleTextBytes=True),
                 capture(visibleText=None), capture('券' * (promotions.MAX_CAPTURE_BYTES // 3 + 1))]
        for field in ('visibleTextTruncated', 'visibleTextBytes', 'visibleText', 'capturedAt', 'url'):
            value = capture()
            del value[field]
            cases.append(value)
        for value in cases:
            with self.subTest(keys=list(value)), self.assertRaises(ValueError):
                promotions.parse_capture(value, 'jd', URL)

    def test_empty_capture_is_unverified_and_challenge_is_blocked(self):
        self.assertEqual(promotions.parse_capture(capture(''), 'jd', URL)['status'], 'empty_unverified')
        result = promotions.parse_capture(capture('Coupon. Please verify you are human.'), 'jd', URL)
        self.assertEqual(result['error']['code'], 'challenge')
        self.assertEqual(result['snippets'], [])
        self.assertIsNone(result['source_mode'])

    def test_capture_expression_is_fixed_read_only_and_bounded(self):
        for token in ('document.body.innerText', 'location.href', 'new Date()', '262144', 'visibleTextTruncated'):
            self.assertIn(token, promotions.CAPTURE_JS)
        for token in ('fetch(', 'eval(', '.click(', 'localStorage', 'cookie', 'outerHTML'):
            self.assertNotIn(token, promotions.CAPTURE_JS)


if __name__ == '__main__':
    unittest.main()
