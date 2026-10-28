"""Run the distributed test bundle against an installed distribution."""
import argparse
import importlib.metadata
import os
import subprocess
import sys
import sysconfig
import tomllib
import unittest
from pathlib import Path


def verify_version(bundle):
    expected = tomllib.loads((bundle / 'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
    import china_deals
    executable = Path(sysconfig.get_path('scripts')) / ('china-deals.exe' if os.name == 'nt' else 'china-deals')
    actual = {
        'runtime': china_deals.__version__,
        'metadata': importlib.metadata.version('china-deals'),
        'cli': subprocess.check_output([str(executable), '--version'], text=True).strip(),
        'module CLI': subprocess.check_output([sys.executable, '-m', 'china_deals', '--version'], text=True).strip(),
    }
    if any(value != expected for value in actual.values()):
        raise RuntimeError(f'version mismatch: pyproject={expected!r}, {actual!r}')
    origin = Path(china_deals.__file__).resolve()
    if bundle.resolve() in origin.parents:
        raise RuntimeError(f'package imported from test bundle: {origin}')
    print(f'Version {expected}; installed package: {origin}', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    os.chdir(bundle)
    sys.path.insert(0, str(bundle))
    verify_version(bundle)
    suite = unittest.defaultTestLoader.discover(str(bundle / 'tests'), top_level_dir=str(bundle / 'tests'))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    for test, reason in result.skipped:
        print(f'SKIPPED {test.id()}: {reason}', flush=True)
    print(f'Skip count: {len(result.skipped)}', flush=True)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
