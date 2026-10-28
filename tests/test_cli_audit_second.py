import io
import json
import os
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from china_deals.cli import build_parser, main, run
from tests.test_freshness import NOW, offer


class SecondCliAuditTests(unittest.TestCase):
    def test_all_effective_queries_validate_before_any_adapter(self):
        for option in (['--query-for', 'jd=bad\x7fquery'], ['--zh-query', 'bad\nquery']):
            with self.subTest(option=option), patch('china_deals.adapters.search_marketplace') as adapter:
                args = build_parser().parse_args(['search', '示例', '--markets', 'taobao,jd', '--access', 'native', '--currency', 'native'] + option)
                with self.assertRaises(ValueError):
                    run(args)
                adapter.assert_not_called()

    def test_markdown_exposes_escaped_source_error_and_warnings(self):
        source = {'status': 'error', 'items': [], 'error': {'code': 'denied', 'message': 'Try [login](https://evil.test)'},
                  'warnings': ['<img src=x>'], 'marketplace': 'jd'}
        output = io.StringIO()
        with patch('china_deals.adapters.search_marketplace', return_value=source), redirect_stdout(output):
            code = main(['search', '示例', '--markets', 'jd', '--access', 'native', '--currency', 'native', '--format', 'markdown'])
        self.assertEqual(code, 3)
        self.assertIn('denied: Try \\[login\\]\\(https://evil.test\\)', output.getvalue())
        self.assertIn('&lt;img src=x&gt;', output.getvalue())

    def test_detail_fresh_only_retains_excluded_observation(self):
        rows = [offer(), offer(item_id='456', url='https://item.jd.com/456.html', observed_at='2026-10-20T17:00:00Z'),
                offer(item_id='789', url='https://item.jd.com/789.html', source_mode='search_index')]
        source = {'marketplace': 'jd', 'status': 'ok', 'items': rows, 'warnings': [], 'access': {'attempts': ['receipt']}}
        with patch('china_deals.guest.get_guest_item', return_value=source):
            result, code = run(build_parser().parse_args(['detail', 'jd', '123', '--currency', 'native', '--fresh-only', '--as-of', NOW]))
        self.assertEqual(code, 0)
        self.assertEqual([x['item_id'] for x in result['items']], ['123'])
        self.assertEqual([x['price_freshness']['status'] for x in result['freshness_excluded_items']],
                         ['older_than_limit', 'cached_or_aggregated_source'])
        self.assertEqual(result['freshness_excluded_items'][0]['price']['amount'], '7999')
        self.assertEqual(result['access']['attempts'], ['receipt'])

    def test_offline_commands_ignore_invalid_config_and_explicit_missing_errors(self):
        with TemporaryDirectory() as directory:
            config = Path(directory) / 'config.json'
            config.write_text('{invalid')
            with patch.dict(os.environ, {'CHINA_DEALS_CONFIG': str(config)}), patch('socket.socket', side_effect=AssertionError('network')):
                for argv in (['restrictions'], ['estimate', '--goods-cny', '100', '--freight-cny', '20', '--cny-brl', '1', '--usd-brl', '5', '--icms-rate', '.2'], ['doctor']):
                    with self.subTest(argv=argv):
                        _, code = run(build_parser().parse_args(argv))
                        self.assertEqual(code, 0)
                config.unlink()
                output = io.StringIO()
                with redirect_stdout(output):
                    code = main(['config', 'show'])
                self.assertEqual(code, 2)
                self.assertIn('does not exist', json.loads(output.getvalue())['error']['message'])

    def test_ram_limit_accepts_128_and_rejects_out_of_range(self):
        parser = build_parser()
        self.assertEqual(parser.parse_args(['compare', 'input.json', '--min-ram-gb', '128']).min_ram_gb, 128)
        for value in ('0', '4097'):
            with self.subTest(value=value), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                parser.parse_args(['compare', 'input.json', '--min-ram-gb', value])
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'offers.json'
            path.write_text('[]')
            with patch('socket.socket', side_effect=AssertionError('network')):
                result, code = run(parser.parse_args(['compare', str(path), '--min-ram-gb', '128', '--currency', 'native']))
            self.assertEqual(code, 0)
