import io
import os
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.request import HTTPSHandler, build_opener
from urllib.response import addinfourl

from china_deals import config, fx, shipping

XML = (b'<Envelope><Cube><Cube time="2026-10-26">'
       b'<Cube currency="BRL" rate="6"/><Cube currency="CNY" rate="8"/>'
       b'<Cube currency="IDR" rate="20000"/><Cube currency="USD" rate="1.2"/>'
       b'</Cube></Cube></Envelope>')


class FakeHTTPS(HTTPSHandler):
    def __init__(self, routes, seen):
        super().__init__()
        self.routes, self.seen = routes, seen

    def https_open(self, request):
        url = request.full_url
        self.seen.append((url, request.get_method()))
        status, location, body = self.routes[url]
        headers = Message()
        if location:
            headers['Location'] = location
        response = addinfourl(io.BytesIO(body), headers, url, status)
        response.msg = 'Found' if status == 302 else 'OK'
        return response


def opener_factory(routes, seen):
    def factory(redirects):
        return build_opener(redirects, FakeHTTPS(routes, seen))
    return factory


class NetworkSecurityTests(unittest.TestCase):
    def test_ecb_redirects_denied_before_target_request(self):
        for target in ('https://attacker.invalid/x', 'http://www.ecb.europa.eu/x',
                       'https://www.ecb.europa.eu:444/x',
                       'https://user@www.ecb.europa.eu/x',
                       'https://www.ecb.europa.eu.attacker.invalid/x'):
            with self.subTest(target=target):
                seen = []
                routes = {fx.ECB_URL: (302, target, b'')}
                with patch.object(fx, 'build_opener', side_effect=opener_factory(routes, seen)):
                    with self.assertRaisesRegex(ValueError, 'redirect denied'):
                        fx.fetch_rates()
                self.assertEqual(seen, [(fx.ECB_URL, 'GET')])

    def test_ecb_same_host_redirect_and_limit(self):
        target = 'https://www.ecb.europa.eu:443/new.xml'
        seen = []
        routes = {fx.ECB_URL: (302, target, b''), target: (200, None, XML)}
        with patch.object(fx, 'build_opener', side_effect=opener_factory(routes, seen)):
            self.assertEqual(fx.fetch_rates()['rate_date'], '2026-10-26')
        self.assertEqual(seen, [(fx.ECB_URL, 'GET'), (target, 'GET')])
        seen = []
        routes = {fx.ECB_URL: (302, '/loop0', b'')}
        routes.update({f'https://www.ecb.europa.eu/loop{i}': (302, f'/loop{i + 1}', b'')
                       for i in range(5)})
        with patch.object(fx, 'build_opener', side_effect=opener_factory(routes, seen)):
            with self.assertRaisesRegex(ValueError, 'redirect denied'):
                fx.fetch_rates()
        self.assertEqual(len(seen), 6)

    def test_fansbuy_post_denies_redirect_and_direct_post_succeeds(self):
        source = shipping._API + 'estimatesTest'
        target = 'https://attacker.invalid/collect'
        seen = []
        with patch.object(shipping, 'build_opener', side_effect=opener_factory({source: (302, target, b'')}, seen)):
            with self.assertRaisesRegex(ValueError, 'Fansbuy request failed'):
                shipping._post('estimatesTest', {'weight': 1000}, 2)
        self.assertEqual(seen, [(source, 'POST')])
        seen = []
        with patch.object(shipping, 'build_opener', side_effect=opener_factory({source: (200, None, b'{"code":0}')}, seen)):
            self.assertEqual(shipping._post('estimatesTest', {}, 2), {'code': 0})
        self.assertEqual(seen, [(source, 'POST')])

    def test_config_size_and_regular_files(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            path.write_bytes(b'{}' + b' ' * (65536 - 2))
            self.assertEqual(config.load_config(path)['schema_version'], 1)
            path.write_bytes(b'{}' + b' ' * 65535)
            with self.assertRaisesRegex(ValueError, '64 KiB'):
                config.load_config(path)
            with self.assertRaisesRegex(ValueError, 'regular file'):
                config.load_config(directory)
            if hasattr(os, 'mkfifo'):
                fifo = Path(directory) / 'fifo'
                os.mkfifo(fifo)
                with self.assertRaisesRegex(ValueError, 'regular file'):
                    config.load_config(fifo)
            with self.assertRaisesRegex(ValueError, 'does not exist'):
                config.load_config(Path(directory) / 'missing')
            path.write_bytes(b'{')
            with self.assertRaises(ValueError):
                config.load_config(path)

    def test_config_read_is_bounded_and_io_errors_propagate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'config.json'
            path.write_bytes(b'{}')
            real_fdopen = os.fdopen
            reads = []

            class TrackingStream:
                def __init__(self, stream):
                    self.stream = stream

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    self.stream.close()

                def read(self, size):
                    reads.append(size)
                    return self.stream.read(size)

            with patch.object(config.os, 'fdopen', side_effect=lambda *a, **kw: TrackingStream(real_fdopen(*a, **kw))):
                config.load_config(path)
            self.assertEqual(reads, [65537])
            with patch.object(config.os, 'open', side_effect=PermissionError('denied')):
                with self.assertRaises(PermissionError):
                    config.load_config(path)

    def test_fansbuy_timeout_rejects_float_overflow_before_network(self):
        with patch.object(shipping, '_post') as post:
            for timeout in ('1e9999', '1e-9999'):
                with self.assertRaisesRegex(ValueError, 'timeout'):
                    shipping.fansbuy_quotes(1000, timeout=timeout)
            post.assert_not_called()


if __name__ == '__main__':
    unittest.main()
