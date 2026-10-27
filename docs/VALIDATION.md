# Validation and release boundaries

Checked 2026-10-27 in `/home/marlos/projects/china-deals`.

## Completed checks

- `python3 -m unittest discover -s tests -q`: **65 passed**. Tests cover real bounded subprocesses, synthetic adapter boundaries, normalization/currency/identity, detail-table integration, exact-match ranking, captured-request binding, carrier filters, rounded cost arithmetic and current PRC threshold/deduction.
- `uvx ruff check china_deals tests`: passed.
- `python3 -m compileall -q china_deals`: passed.
- `uv build --out-dir .local/dist`: sdist and wheel built successfully.
- `uv tool install --editable /home/marlos/projects/china-deals`: local `china-deals` executable installed.
- OpenCLI `@jackwener/opencli@2.0.2` installed separately with lifecycle scripts disabled. Basic `china-deals doctor` confirms exact version. A current package adapter subset was checked against pinned source; see [adapter evidence](research/blibli.md).
- Fansbuy's public country and estimate endpoints succeeded without credentials. A public 1,000g, 20×20×15cm Brazil capture contains 15 records; the ordinary-goods filter admits 14 and rejects the explicitly disabled record. [Portable raw evidence](../tests/fixtures/fansbuy-estimates-2026-10-27.json).
- CLI shipping accepted that captured response only with matching destination, weight, dimensions, categories and timestamp metadata. Freshness/authenticity of caller-supplied captures remain unverified.
- Direct first-party Receita/CONFAZ retrieval and excerpt/hash audit established the consulted policy snapshot. The manual's current PRC rule is effective for qualifying DIR registered from 2026-05-12; historic 20%/USD20 rules were removed. See [source audit](research/shipping-brazil.md).

## Independent reviews

AGY **1.4.7**, actual CLI, requested and initialization-observed model `claude-opus-5-5-high`, completed a supplied-text review with terminal status `SUCCESS` and process exit 0. It did not run authenticated-site checks. Private raw output and runner receipt are retained locally, excluded from Git.

Accepted fixes include URL parser/browser disagreement, explicit currency conflicts, minimum-of-range prices, source-ID/URL binding, condition visibility, timestamp provenance, package binding for imported quotes, positive-only freight, bounded network output, domestic freight in customs value, rounded line totals and category-specific review topics.

A subsequent **GPT 6.1 Terra** read-only review of integrated code found two reproducible issues: JD detail's unbound page price and deduplication before term filters. Both were fixed with regressions. Taobao/JD detail page amounts remain visible as raw evidence but unranked. Only identical eligible observations are deduplicated; differing prices/titles are retained. Independent review is separate from test and live-access evidence.

## Current access limits

- `china-deals doctor --live`: daemon running, **extensionConnected=false**. No authenticated Taobao/JD/Goofish product search or end-to-end price/stock result was established here. The OpenCLI Browser Bridge and user-controlled login/verification are still needed.
- Blibli public API returned **HTTP403**; the browser showed its human-verification page. No challenge was operated. Optional OpenCLI browser fallback is implemented and fixture-tested, but successful live product extraction remains unverified.
- Blibli's prices are IDR and its goods originate in Indonesia. No Indonesia→China/Fansbuy or Indonesia→Brazil freight path was verified.
- Freight quotes and current policy documents do not prove item import eligibility, seller authenticity, payable checkout price, final shipping cost, tax treatment or delivery. The restrictions command returns manual_review.
- No order, cart modification, seller message, payment, shipment submission or customs declaration was made. No AI API was called by the CLI.

Raw captures and provider outputs are under the ignored `.local/` directory. The committed public carrier fixture is credential-free. GitHub CI is a separate check; local passes do not imply hosted CI completion.
