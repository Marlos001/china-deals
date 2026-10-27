"""Real HTTP framing and synthetic login surfaces, without network access."""

import http.client
import io
import time
import unittest
from unittest.mock import Mock, patch

from china_deals import guest
from china_deals.china_capture import parse_capture
from china_deals.marketplaces import item_url
from tests.test_china_capture import capture


class AcquisitionCompletionTests(unittest.TestCase):
    def test_login_metadata_is_rejected_and_gates_same_host(self):
        for market in ('tmall', '1688', 'weidian'):
            for marker in ('请登录后继续', '<title>登录</title>请先登录',
                           'sign in to continue', '登录后查看'):
                with self.subTest(market=market, marker=marker):
                    cap = capture(market)
                    cap['html'] = cap['html'].replace('商品</body>', marker + '</body>')
                    cap['htmlBytes'] = len(cap['html'].encode())
                    with self.assertRaises(ValueError):
                        parse_capture(cap, market, cap['url'])
                    with guest.access_session(), patch.object(
                        guest, '_fetch', side_effect=lambda url, *_: (cap['html'], url)
                    ) as fetch:
                        first = guest.get_guest_item(market, '123')
                        second = guest.get_guest_item(market, '124')
                    self.assertEqual(first['error']['code'], 'challenge')
                    self.assertEqual(first['items'], [])
                    self.assertEqual(second['error']['code'], 'skipped_after_challenge')
                    self.assertEqual(fetch.call_count, 1)

    def test_real_http_response_framing(self):
        url = item_url('weidian', '123')
        body = capture('weidian')['html'].encode()
        for mode in ('complete', 'truncated', 'eof', 'chunked', 'truncated_chunked'):
            with self.subTest(mode=mode):
                headers = b'Content-Type: text/html; charset=utf-8\r\n'
                wire_body = body
                if mode in ('complete', 'truncated'):
                    declared = len(body) + (100 if mode == 'truncated' else 0)
                    headers += f'Content-Length: {declared}\r\n'.encode()
                elif 'chunked' in mode:
                    headers += b'Transfer-Encoding: chunked\r\n'
                    wire_body = f'{len(body):x}\r\n'.encode() + body + b'\r\n'
                    if mode == 'chunked':
                        wire_body += b'0\r\n\r\n'
                wire = b'HTTP/1.1 200 OK\r\n' + headers + b'\r\n' + wire_body

                class Socket:
                    def makefile(self, *_args, **_kwargs):
                        return io.BytesIO(wire)

                response = http.client.HTTPResponse(Socket())
                response.begin()
                response.geturl = lambda: url
                opener = Mock()
                opener.open.return_value = response
                with patch.object(guest.urllib.request, 'build_opener', return_value=opener):
                    if mode.startswith('truncated'):
                        with self.assertRaises(guest._Failure) as failure:
                            guest._fetch(url, {'weidian.com'}, time.monotonic() + 30)
                        self.assertIn(failure.exception.code, ('incomplete_response', 'network_error'))
                    else:
                        result, final = guest._fetch(url, {'weidian.com'}, time.monotonic() + 30)
                        self.assertEqual(result.encode(), body)
                        self.assertEqual(final, url)


if __name__ == '__main__':
    unittest.main()
