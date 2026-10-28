# Contributing

Thanks for helping improve china-deals. Bug reports, documentation fixes, tests and code changes are welcome. If you are planning a large change, opening an issue first can help settle the approach before you spend time on it.

## Get started

You need Python 3.11 or newer and Git. Clone the repository and create a virtual environment:

```sh
git clone https://github.com/Marlos001/china-deals.git
cd china-deals
python -m venv .venv
. .venv/bin/activate  # On Windows: .venv\Scripts\activate
python -m pip install -e .
china-deals --help
```

The core package has no runtime dependencies. Browser support is optional; see the [browser setup](docs/REFERENCE.md#optional-fresh-guest-browser) if your change needs it. You do not need marketplace accounts or AI API credentials for the normal development setup.

## Make and check a change

Create a branch, make a focused change and add tests when they help establish the behavior. The `china_deals/` directory contains the application, `tests/` contains the test suite and fixtures, and `docs/` contains guides and research.

Run the test suite before submitting:

```sh
python -m unittest discover -s tests -v
china-deals schema
python -m compileall -q china_deals
```

To run a single test file while working, for example:

```sh
python -m unittest discover -s tests -p 'test_brazil.py' -v
```

CI runs these checks on Python 3.11, 3.13 and 3.14. If you have [uv](https://docs.astral.sh/uv/) installed, you can also run `uvx ruff check china_deals tests` for linting. Tests should not require live network access or credentials. Some tests use optional private captures and may skip when those captures are unavailable; report skips and any checks you could not run.

## Marketplace and price changes

This project handles incomplete and changing marketplace data. Please keep these distinctions clear:

- Keep adapters read-only. Preserve source IDs, currencies, timestamps and access failures; represent missing or uncertain information as unknown.
- Search snippets, synthetic fixtures, affiliate pools and empty responses do not establish a current offer or complete marketplace coverage. Separate mocked, captured and live evidence in tests and reports.
- Add focused tests for changes to prices, shipping, taxes, source contracts or command execution. Use sanitized fixtures and cover missing or conflicting inputs as well as successful cases.
- Link research claims to primary sources and pin repository revisions where relevant. Check the license before copying third-party code, and update [third-party notices](THIRD_PARTY.md) when appropriate.
- Do not add automatic CAPTCHA solving, credential collection, hidden AI calls or transaction commands. Do not commit cookies, browser profiles, tokens, private captures or user searches.

See the [validation notes](docs/VALIDATION.md) for the existing evidence and its limits.

## Open an issue or pull request

For a bug report, include the command, expected and actual behavior, Python and china-deals versions, and a minimal reproduction. Remove personal information and credentials from logs or examples.

For a pull request, describe the problem and your change, list the checks you ran and note any known limitations. Link the relevant issue if there is one. Update the documentation when behavior or setup changes. Maintainers can then review the change and discuss any adjustments.

Contributions are made under the project's [MIT License](LICENSE).
