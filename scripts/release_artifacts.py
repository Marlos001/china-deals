"""Build artifacts from a Git commit and record their SHA-256 digests."""
import argparse
import hashlib
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def build(commit, output):
    root = Path(__file__).resolve().parents[1]
    sha = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--verify', f'{commit}^{{commit}}'], text=True).strip()
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / 'source.tar'
        with archive.open('wb') as stream:
            run('git', '-C', str(root), 'archive', '--format=tar', sha, stdout=stream)
        source = Path(tmp) / 'source'
        source.mkdir()
        # git archive contains repository paths only; use the safe data filter on Python 3.12+.
        with tarfile.open(archive) as tar:
            if sys.version_info >= (3, 12):
                tar.extractall(source, filter='data')
            else:
                # Validate paths and links before extraction on Python 3.11.
                for member in tar.getmembers():
                    if member.issym() or member.islnk() or member.name.startswith('/') or '..' in Path(member.name).parts:
                        raise ValueError(f'unsafe archive member: {member.name}')
                tar.extractall(source)
        run(sys.executable, '-m', 'build', '--outdir', str(output), str(source))
    artifacts = sorted(p for p in output.iterdir() if p.is_file())
    if len(artifacts) != 2 or not any(p.name.endswith('.whl') for p in artifacts) or not any(p.name.endswith('.tar.gz') for p in artifacts):
        raise RuntimeError('Expected exactly one wheel and one sdist')
    receipt = {'commit': sha, 'artifacts': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts}}
    (output / 'SHA256.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--output', required=True, type=Path, help='New directory for artifacts and receipt')
    args = parser.parse_args()
    build(args.commit, args.output)


if __name__ == '__main__':
    main()
