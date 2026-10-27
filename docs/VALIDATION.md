# Validation and release boundaries

Checked 2026-10-27 in `/home/marlos/projects/china-deals`.

## Version 0.4 product validation update

- Three GPT-6 Astra validation agents tested iPhone 17 Pro Max, AirPods Max and broad Zephyrus searches. All bounded live CLI searches met index/API verification; the browser found no verified purchasable exact-variant winner. See the [validation summary](validation/README.md) and its source-specific reports.
- **233 local tests pass**, including selected-variant/accessory/monthly-price classification, Product/Offer/mobile-JD identity, invocation host gates, hydration provenance, Blibli stock claims, opaque JD discovery and coupon intent round-trips. Ruff and whitespace checks pass.
- Seven retained AirPods regressions pass on current code. Actual offline CLI replays of four retained Zephyrus fixtures yield zero accessory groups, four separate family groups plus incomplete Duo, incomplete negated TGP and one AMD alias group.
- `plan` is offline; it neither runs searches nor establishes comprehensive inventory. Family/chassis/code/year partition comparisons; absent identities and multi-display binding remain incomplete. All masked/index prices remain unknown. Blibli freight remains excluded.
- Astra follow-up reviews verified the three integration and four product/comparison reproductions resolved. Compilation and 0.4.0 sdist/wheel builds pass. Implementation and independent review are separate from live-access evidence. No further blocked-surface request was made to test these fixes. No marketplace write, registration or purchase occurred.

## Version 0.3 coupon and screenshot update

- `python -m unittest discover -s tests -q`: **168 passed**. `uvx ruff check china_deals tests`, compilation, package build and whitespace checks passed.
- Added deterministic imported coupon scenarios: fixed/percentage discounts, caps, minimum spend, dates, product/seller scope, explicit account/payment requirements, unknown eligibility, cashback separation, ties and no inferred stacking. Base listing prices remain unchanged. Caller-confirmed eligibility is not independently verified checkout acceptance.
- Coupon CLI/FX integration, capped discounts on large laptop amounts, contradictory product IDs/URLs and native guest detail URL hydration have regression coverage. Independent Terra review found the product-restricted Blibli coupon binding issue; the fix validates identity in normalization and coupon evaluation.
- User screenshots support the first two displayed Blibli prices and a voucher summary (3%, advertised Rp2,000,000 benefit, Rp4,000,000 minimum). Its code/full terms and whether the displayed amount already includes it remain unknown. The selected second listing is visibly out of stock and excluded from purchase candidates.
- All five reported amounts are retained in a public example with `user_observation` provenance; older cached seller hardware descriptions remain a distinct evidence source. No additional eligible coupon was established by the example evaluation.
- The broader Goofish pass retained 68 search queries; no new currently available G16 offer was validated. It distinguished an HP main item from contaminating G16 recommendation text. This is not an inventory-wide absence claim.
- A single public legacy JD price request reset the connection. Superbuy's guest homepage loaded, but its target keyword search reached security verification. No price bypass or full guest catalog success is claimed. No marketplace account, cart, coupon claim, checkout, purchase or message was created.

See [updated Blibli evidence](research/zephyrus-g16-blibli-v2.md), [Goofish evidence](research/zephyrus-g16-goofish-v2.md) and [access solutions](research/access-solutions-v2.md). Local checks and hosted CI remain separate evidence.

## Version 0.2 guest-access update

- **139 local tests pass** with `python -m unittest discover -s tests -q`; `uvx ruff check china_deals tests` passes. The update adds Chinese-query enforcement, guest HTTP/browser contracts, native/local filter disclosure, per-market policies, dated ECB BRL estimates, hardware conflicts and comparison provenance checks.
- Optional Playwright/Chromium is tested with offline page fixtures and real fresh browser contexts. Live rendered searches encountered verification for all four marketplaces; no bypass or successful full guest catalog search is claimed.
- A fresh JD guest HTTP detail for SKU `100214660452` succeeded with explicit hardware text but no numeric price.
- A live Fansbuy 3kg / 45×35×15cm Electric+Brand scenario yielded four accepted routes, with freight reference conversions R$259.80–647.80. These are hypothetical package inputs, not measured laptop packaging or import acceptance.
- Blibli cached/index leads remain separate from current offers. Freight is excluded for Blibli; no current global best-deal winner or laptop landed total was established.
- Two new independent Terra review rounds found product-route admission, discarded contradictory observations, lost listing provenance, and dropped structured hardware evidence. Fixed with CLI and comparison regression coverage.
- `uv build --out-dir .local/dist` built the 0.2.0 sdist and wheel; final GitHub CI is checked separately after publication.

See the [G16 test notes](research/zephyrus-g16-test.md), [Blibli candidates](research/zephyrus-g16-blibli.md) and [guest browser contract](research/browser-guest.md).

## Baseline 0.1 completed checks

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

- `china-deals doctor --live`: daemon running, **extensionConnected=false**. No authenticated Taobao/JD/Goofish product search or end-to-end price/stock result was established here. OpenCLI native mode needs a bridge/session for the checked adapters. Version 0.2 defaults to guest engines and reports unavailable/blocked access without requesting a marketplace account.
- Blibli public API returned **HTTP403**; the browser showed its human-verification page. No challenge was operated. Optional OpenCLI browser fallback is implemented and fixture-tested, but successful live product extraction remains unverified.
- Blibli's prices are IDR and its goods originate in Indonesia. No Indonesia→China/Fansbuy or Indonesia→Brazil freight path was verified.
- Freight quotes and current policy documents do not prove item import eligibility, seller authenticity, payable checkout price, final shipping cost, tax treatment or delivery. The restrictions command returns manual_review.
- No order, cart modification, seller message, payment, shipment submission or customs declaration was made. No AI API was called by the CLI.

Raw captures and provider outputs are under the ignored `.local/` directory. The committed public carrier fixture is credential-free. GitHub CI is a separate check; local passes do not imply hosted CI completion.
