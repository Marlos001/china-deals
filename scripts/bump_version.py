"""Patch-only release versioning. Dry-run by default; retries target one version."""

import argparse
import os
import re
import tempfile
import tomllib
from pathlib import Path


def next_patch(version):
    if not isinstance(version, str) or not re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", version):
        raise ValueError("Expected an X.Y.Z release version without leading zeros")
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def bump(root, expected=None, write=False):
    """Reconcile both version files to the next patch after one explicit base.

    An interrupted write may leave one file at the target. Repeating the same
    --from base completes it; a completed repeat does not increment again.
    """
    root = Path(root)
    paths = (root / "pyproject.toml", root / "china_deals/__init__.py")
    texts = [p.read_text() for p in paths]
    metadata = tomllib.loads(texts[0])["project"]["version"]
    match = re.search(r'^__version__ = "([^"]+)"$', texts[1], re.M)
    if not match:
        raise ValueError("Missing unique runtime version")
    runtime = match[1]
    if expected is None:
        if write:
            raise ValueError("Writing requires --from VERSION so retries cannot create another release")
        if metadata != runtime:
            raise ValueError("Version files disagree; specify the intended --from base to reconcile")
        expected = metadata
    target = next_patch(expected)
    if any(v not in {expected, target} for v in (metadata, runtime)):
        raise ValueError("Version files differ from the requested base/target; no files changed")
    replacements = []
    for text, pattern, replacement in (
        (texts[0], r'^version = "[^"]+"$', f'version = "{target}"'),
        (texts[1], r'^__version__ = "[^"]+"$', f'__version__ = "{target}"'),
    ):
        value, count = re.subn(pattern, replacement, text, flags=re.M)
        if count != 1:
            raise ValueError("Expected one version declaration per file; no files changed")
        replacements.append(value)
    if write:
        for path, original, replacement in zip(paths, texts, replacements, strict=True):
            if path.read_text() != original:
                raise ValueError("File changed during release preparation; rerun the same --from base")
            if original == replacement:
                continue
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                                 prefix=".version-", delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(replacement)
                    stream.flush()
                    os.fsync(stream.fileno())
                temporary.chmod(path.stat().st_mode & 0o777)
                os.replace(temporary, path)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
    return {"base": expected, "version": target, "written": write}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="expected", help="Explicit base version, e.g. 0.9.0; required with --write")
    parser.add_argument("--write", action="store_true", help="Apply the proposed patch version to both version files")
    args = parser.parse_args()
    try:
        result = bump(Path(__file__).resolve().parents[1], args.expected, args.write)
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))
    print(f"{result['base']} -> {result['version']} ({'written' if result['written'] else 'dry run'})")


if __name__ == "__main__":
    main()
