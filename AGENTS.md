# Release versioning

The Alibaba.com/AliExpress release is **0.9.0**. Every subsequent release must
increment the **patch** component: `0.9.1`, `0.9.2`, ..., `0.9.10`.
Do not increment the minor or major component unless the user explicitly asks.

Preview with `python scripts/bump_version.py`. Apply one release with
`python scripts/bump_version.py --from 0.9.0 --write` (substitute the actual base).
Reusing the same `--from` value is safe after interruption or uncertain success:
it reconciles both version files to that one target and never advances twice.
Keep `pyproject.toml` and `china_deals/__init__.py` aligned; complete the tests,
package and exact-commit installation checks before claiming a release complete.
