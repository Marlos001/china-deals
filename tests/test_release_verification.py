"""Tests for installed-distribution version verification."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.verify_installed import verify_version


class InstalledVersionTests(unittest.TestCase):
    def test_all_version_surfaces_must_agree_and_import_must_be_installed(self):
        with tempfile.TemporaryDirectory() as folder:
            bundle = Path(folder)
            (bundle / 'pyproject.toml').write_text('[project]\nversion = "0.9.1"\n')
            package = SimpleNamespace(__version__='0.9.1', __file__='/installed/china_deals/__init__.py')
            with patch.dict('sys.modules', {'china_deals': package}), \
                 patch('scripts.verify_installed.importlib.metadata.version', return_value='0.9.1'), \
                 patch('scripts.verify_installed.subprocess.check_output', return_value='0.9.1\n') as cli:
                verify_version(bundle)
                self.assertEqual(cli.call_count, 2)
                cli.return_value = '0.9.0\n'
                with self.assertRaisesRegex(RuntimeError, 'version mismatch'):
                    verify_version(bundle)
                cli.return_value = '0.9.1\n'
                package.__file__ = str(bundle / 'china_deals/__init__.py')
                with self.assertRaisesRegex(RuntimeError, 'test bundle'):
                    verify_version(bundle)


if __name__ == '__main__':
    unittest.main()
