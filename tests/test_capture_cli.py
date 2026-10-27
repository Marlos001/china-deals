"""Public primary-DOM capture import and browser integration, network-free."""
import unittest
from unittest.mock import patch

from test_browser_guest import Context, Page, session
from test_goofish_public import URL, capture

from china_deals import browser_guest
from china_deals.cli import build_parser, run


class CaptureCliTests(unittest.TestCase):
    def test_import_retains_capture_time_and_makes_no_network_request(self):
        value = capture()
        with patch('china_deals.cli.read_json', return_value={'structuredContent': {'value': value}}), \
             patch('china_deals.guest._fetch') as fetch, patch.object(browser_guest, '_browser_context') as browser:
            data, code = run(build_parser().parse_args(['detail', 'goofish', '1096499480089',
                             '--from-browser-json', 'file', '--currency', 'native']))
        self.assertEqual(code, 0)
        self.assertEqual(data['dataset_origin'], 'caller_supplied_browser_capture')
        self.assertEqual(data['access_mode'], 'capture')
        self.assertEqual(data['items'][0]['observed_at'], value['capturedAt'])
        self.assertEqual(data['items'][0]['price']['amount'], '7999')
        self.assertFalse(data['access']['attempts'])
        fetch.assert_not_called()
        browser.assert_not_called()

    def test_default_capture_import_does_not_fetch_fx(self):
        with patch('china_deals.cli.read_json', return_value=capture()), patch('china_deals.fx.fetch_rates') as fx, \
             patch('china_deals.guest._fetch') as fetch:
            data, code = run(build_parser().parse_args(['detail', 'goofish', '1096499480089', '--from-browser-json', 'file']))
        self.assertEqual(code, 0)
        self.assertEqual(data['items'][0]['price']['amount'], '7999')
        self.assertTrue(any('--fx-from-json' in warning for warning in data['warnings']))
        fx.assert_not_called()
        fetch.assert_not_called()

    def test_wrong_id_and_unsupported_market_cannot_import_capture(self):
        for market, item_id in [('goofish', '123'), ('jd', '1096499480089')]:
            with patch('china_deals.cli.read_json', return_value=capture()), patch('china_deals.guest._fetch') as fetch:
                with self.assertRaises(ValueError):
                    run(build_parser().parse_args(['detail', market, item_id, '--from-browser-json', 'file', '--currency', 'native']))
                fetch.assert_not_called()

    def test_browser_uses_bounded_primary_dom_and_preserves_full_price(self):
        value = capture()
        page = Page(URL, html=value['mainHtml'], title=value['title'])
        context = Context([page])
        with patch.object(browser_guest, '_browser_context', return_value=session(context)):
            result = browser_guest.get_browser_guest_item('goofish', URL)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['items'][0]['price'], '7999')
        self.assertTrue(page.closed)
        self.assertTrue(context.closed)
        self.assertFalse(result['items'][0]['checkout_verified'])


if __name__ == '__main__':
    unittest.main()
