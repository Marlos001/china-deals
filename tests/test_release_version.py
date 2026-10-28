"""Release retries and patch-only progression, using disposable repositories."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.bump_version import bump, next_patch


class ReleaseVersionTests(unittest.TestCase):
    def root(self, path, metadata='0.9.0', runtime='0.9.0'):
        root = Path(path)
        (root / 'china_deals').mkdir()
        (root / 'pyproject.toml').write_text('[project]\nname = "synthetic"\nversion = "' + metadata + '"\n')
        (root / 'china_deals/__init__.py').write_text('__version__ = "' + runtime + '"\n')
        return root

    def test_next_patch_never_rolls_minor_and_validates_versions(self):
        for old, new in (('0.9.0', '0.9.1'), ('0.9.9', '0.9.10'), ('0.9.99', '0.9.100')):
            self.assertEqual(next_patch(old), new)
        for bad in ('0.9', '0.09.0', '0.9.1rc1', None):
            with self.assertRaises(ValueError):
                next_patch(bad)

    def test_dry_run_and_explicit_repeat_are_safe(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.root(folder)
            self.assertEqual(bump(root)['version'], '0.9.1')
            self.assertIn('0.9.0', (root / 'pyproject.toml').read_text())
            with self.assertRaises(ValueError):
                bump(root, write=True)
            first = bump(root, '0.9.0', True)
            second = bump(root, '0.9.0', True)
            self.assertEqual(first, second)
            self.assertIn('0.9.1', (root / 'pyproject.toml').read_text())
            self.assertEqual(bump(root)['version'], '0.9.2')

    def test_half_written_release_reconciles_without_second_increment(self):
        for a, b in (('0.9.1', '0.9.0'), ('0.9.0', '0.9.1')):
            with tempfile.TemporaryDirectory() as folder:
                root = self.root(folder, a, b)
                with self.assertRaises(ValueError):
                    bump(root)
                bump(root, '0.9.0', True)
                self.assertIn('0.9.1', (root / 'pyproject.toml').read_text())
                self.assertIn('0.9.1', (root / 'china_deals/__init__.py').read_text())

    def test_os_failure_can_be_retried_at_same_base(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.root(folder)
            import os
            replace = os.replace
            count = 0
            def fail_second(*args):
                nonlocal count
                count += 1
                if count == 2:
                    raise OSError('synthetic interruption')
                return replace(*args)
            with patch('scripts.bump_version.os.replace', side_effect=fail_second), self.assertRaises(OSError):
                bump(root, '0.9.0', True)
            bump(root, '0.9.0', True)
            self.assertIn('0.9.1', (root / 'china_deals/__init__.py').read_text())
            self.assertFalse(list(root.rglob('.version-*')))

    def test_stale_base_does_not_overwrite_other_versions(self):
        with tempfile.TemporaryDirectory() as folder:
            root = self.root(folder, '0.9.5', '0.9.5')
            before = (root / 'pyproject.toml').read_text()
            with self.assertRaises(ValueError):
                bump(root, '0.9.0', True)
            self.assertEqual(before, (root / 'pyproject.toml').read_text())


if __name__ == '__main__':
    unittest.main()
