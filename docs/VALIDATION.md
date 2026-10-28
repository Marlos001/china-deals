# Validation and release boundaries

Checked 2026-10-27 in `/home/marlos/projects/china-deals`.

## Version 0.9 international marketplace expansion

- Added distinct Alibaba.com and AliExpress guest discovery, exact-identity
  metadata/captures and downstream workflows. Explicit currencies and bulk/tier
  constraints survive exports. Shipping is manual; Fansbuy support is not inferred.
- **556 local tests pass with outbound sockets and DNS blocked.** Ruff, compilation,
  schema, documentation links and whitespace checks pass. The 0.9.0 wheel/sdist
  exclude private captures; an outside-checkout smoke verifies all package source
  bytes, nine-market registration, 12 currency cycles and offline Alibaba capture.
  Hosted CI and installed revision are verified separately after publication.
  The patch-only
  release helper covers dry runs, idempotent repeats and interrupted writes.
- Alibaba retained HTML parses successfully offline after the original parser
  failure; AliExpress stopped at an access gate. Neither establishes a fresh
  selected-unit purchase price. See [evidence and limits](validation/international-marketplaces.md).

## Version 0.8 Fansbuy marketplace expansion

- Added distinct **Tmall, 1688 and Weidian** paths alongside existing Taobao/JD, covering the five explicitly named marketplaces in retained official Fansbuy guide/procurement copy. Existing Goofish/Blibli remain available. This dated named union is non-exhaustive, and manual fill-and-buy is a separate workflow. See the [source inventory](research/fansbuy-marketplaces-2026-10-27.md) and [capability matrix](validation/fansbuy-expansion.md).
- New paths cover strict native identities, bounded guest index discovery and primary metadata, network-free HTML captures, additive configuration, intent/filters, refresh/history, promotion evidence/coupon scenarios and Brazil estimates. All new-market metadata prices remain null without a validated selected-variant/full-payment contract. Native OpenCLI adapters/facets remain explicitly unavailable/unverified.
- **536 local tests pass with outbound sockets and DNS blocked.** Ruff, compilation, schema output and whitespace checks pass. The 0.8.0 sdist/wheel build excludes private captures; an outside-checkout wheel smoke confirms every package source file matches, group expansion works and nine imported metadata rank/JSON cycles stay unpriced. This is local package proof; hosted CI and global installation are recorded separately after publication.
- Three implementation/review stages cover registry/command contracts, acquisition/capture, and final retained-state/adversarial reconciliation. Round one cleared its scope. Round two found login-wall host-gating and premature HTTP EOF defects; fixes pass all four original reproduction methods, eight independent positive-control methods and new fixed-length/chunked transport regressions. Round three found no remaining P1/P2 in scope: 52 malformed-state mutations rejected, 81 availability combinations and 243 normalization/ranking cycles passed, with the exact retained Weidian hash verified. Its isolated full run passed 533 tests and skipped three unavailable optional private-capture tests; the root run above passed all 536. Independent review is offline evidence and does not establish live SKU prices.
- A bounded Weidian post-integration native GET at **19:15:23–19:15:26 UTC** retained numeric **HTTP 200**, an exact requested/final item identity and an integrated `ok` result. The decoded body SHA-256 is `0367cba1af0721711cc73263bc755c6ab91386e0e74735268e5522656897fa8b` (43,514 UTF-8 bytes). The clothing canary is **delisted despite stock 8,000**, and its price remains null. This is transport/parser proof, not a purchasable electronics candidate, current checkout or authenticity claim. The original pre-fix successful transport did not separately retain numeric HTTP status and remains an unchanged parser-failure receipt.
- Fansbuy requests stopped after the linked index JavaScript returned HTTP 403; a concurrent language asset's status is unknown. DuckDuckGo stopped after HTTP 202/CAPTCHA. No live Tmall/1688 product extraction, fresh new-market selected-variant price, redeemed coupon or verified deal is asserted. No login, cart, account, purchase, message or bypass occurred. [Acquisition/source details](validation/fansbuy-new-marketplaces-live.md).

## Version 0.7 diverse-search iteration

- **477 local tests pass**, including 105 frozen multilingual intent cases plus independent 62-case and 56-case adversarial sets through repeated ranking. The retained reviewer CLI replays now pass **13/13 and 19/19** export/import scenarios; all four Brazil payment controls pass; these are synthetic correctness checks, not live precision measurements. Ruff, compilation, schema, JSON/link checks and sdist/wheel build pass; package inspection found no private `.local` captures.
- Five retained primary Blibli HTTP responses at approximately 17:37:49–17:37:57 UTC parse as three full offered amounts (Sony XM6 6,179,000 IDR, boxed Ryzen 9800X3D 8,905,000 IDR, DJI Mini 4 Pro RC 2 12,266,000 IDR) plus two unavailable/unpriced products. Empty-attribute single-option state is accepted only with coherent identity; absent price remains absent. This is retained historical transport plus current offline extraction, not a post-fix network retry.
- Seven Brazil discovery queries and four fresh merchant navigations provide dated Sony/Pichau references and a sold-out exact DJI package. Conditional product gaps do not become savings: the replayable real-data comparison returns `needs_review` for all three, retaining unknown condition/equivalence, costs and import eligibility. The sold-out Brazilian DJI price is excluded.
- Chinese discovery retained twelve queries and four Goofish captures, all target prices unpriced because of mixed/wrong basis or sold/delisted status. Shared challenge guards stopped further requests. Search results are not inventory-wide absence findings.
- Nine bounded intent families now validate literal product and selected evidence. Unsupported explicit intent is visible/unranked; queryless generic ranking remains available. Independent selected observations survive normalization in stable bounded `variant_observations`; conflicting identities and raw partial-price scope cannot disappear across export. Compatibility wording cannot hide accessories. Package, GPU role, controller, bundle, typed memory/storage and original model-token boundaries have regression coverage.
- Shared transaction checks withhold deposit/installment/remaining-balance/rental/starting quotes without mistaking a naked GPU `3X` suffix for payment. `--include-offers` retains those checks and separate filter-excluded observations. Literal title term filters remain documented as substring filters, not semantic model matching.
- Goofish sold wording and component/gift/repair condition scope are tested independently of numeric prices. Blibli preserves exact selected availability/stock, missing-price and source claims, with safe parser reason/hash diagnostics. Raw source text and provider receipts stay private.
- Final independent Astra follow-ups found no residual P1/P2 within their bounded corrections: source-condition review passed 33 focused + 47 preservation tests and 18 cases; model/capacity review passed 15 cases, 45 ranking passes, 15 mocked CLI checks and 23 profile tests; payment/structured-evidence review passed 78 cases through three JSON ranking passes and mocked CLI export/import, ten Brazil comparisons and 60 focused tests. These reviews do not establish live access or universal query precision.

See [the consolidated results](validation/diverse-results.md), [Blibli](validation/diverse-blibli-2026-10-27.md), [China](validation/diverse-china-2026-10-27.md) and [Brazil](validation/diverse-brazil-2026-10-27.md) reports. Independent final reviews and hosted publication remain separate evidence from these local checks. No account, marketplace write, checkout, coupon redemption or purchase occurred.

## Version 0.6 fresh acquisition and Brazil comparison

- **400 local tests pass**, with Ruff, compilation and package build checks. Primary-state parser and guest/refresh integration cover exact Blibli selected SKU and pickup binding; query and payment/variant evidence survive repeated exports. Fresh-price policies preserve the strictest required age. Observed freight expiry and seven-day FX reference limits hold financial decisions.
- Actual fresh reads: Goofish silver 1 TB iPhone at ¥7,499 through T3 main-item DOM and capture import; Blibli selected Midnight AirPods Max at Rp8,799,000 through retained primary HTTP state, parsed offline. Blibli source marks delivery unavailable/pickup selected. A later rendered open reached verification and stopped. No post-integration live Blibli fetch is claimed. [Detailed receipts and limits](validation/fresh-data-2026-10-27.md).
- Actual HTTP refresh persisted two JD/Blibli receipts and returned partial/unpriced with the previous JSON-LD-only reader; actual history readback worked. A real Blibli promotion read returned no readable snippets, not proof of no coupons. The new state reader addresses the identified price-extraction gap without retrying the challenged surface.
- Independent Astra reviews exposed and drove fixes for exclusion/transaction/structured-variant loss, strict age-policy weakening, stale FX/freight, out-of-stock aliases and source-context/pickup checks. Brazil/ranking follow-up independently cleared its exact remaining reproductions with 47 focused tests and CLI controls. Final acquisition/Blibli follow-up cleared its five exact objections with 128 repository tests and five independent offline controls; no residual P1/P2 was found within that scope.
- Fresh coupon evidence is required by the CLI by default; account/payment/product/seller/quantity/quota constraints remain independent. Promotion snippets never auto-create an eligible coupon. Offline capture imports still evaluate requested rules while keeping FX network disabled unless a local snapshot is supplied.
- Brazil comparison keeps missing costs and identity/condition mismatches unresolved. Real cases remain needs-review; synthetic examples establish arithmetic only. No AI API, scheduler, account, login, cart, coupon redemption, purchase, contact, payment, shipment or customs declaration was created.

## Version 0.5 deeper validation

- **266 local tests pass**. A fresh T3 Goofish capture and actual offline CLI ingestion retained a consistent 1 TB price, timestamp, used condition and pickup-only conflict. Four retained pages replay as ¥7,999/¥7,499 and two unpriced ambiguous controls. New browser integration is fixture-tested; live CLI Playwright transport remains unverified.
- The new `catalog taobao` command succeeded over plain HTTP against one public Jadeship item: ¥6,138, separately converted to R$4,922.75 using fresh ECB 2026-10-27 rates. Underlying freshness, variant, condition and stock remain unknown, and the normalized marketplace price stays null.
- Four useful Blibli cached product observations are retained with source-specific crawl ages, descriptions, stock claims and no extra coupon. Their amounts can show separate BRL references while remaining excluded from current-price rankings. Blibli freight remains excluded.
- Independent Astra review found and drove fixes for explicit catalog currency conflicts, dropped/overflowed/whitespace-formatted conflicting item props and an implicit FX network call during capture import. Its follow-up verified the objections resolved with 30 focused tests and retained-capture replays. Default capture import is offline; local FX is optional.
- No purchase, cart, account, message, coupon redemption, challenge operation, payment, shipment or declaration was made. New source-linked evidence and limits: [deeper results](validation/deeper-results.md).

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
