# Three-product search validation — 2026-10-27

Three GPT-6 Astra validation agents independently exercised **iPhone 17 Pro Max**, **AirPods Max**, and **ASUS ROG Zephyrus across model families**. They used guest CLI searches, bounded source discovery, and T3 browser inspection where an exact link was available. Reports distinguish the published 0.3.0 baseline, evolving code, synthetic reproductions, and live evidence.

## Follow-up: diverse searches and exact-page prices

The [diverse-search iteration](diverse-results.md) expands coverage to six further families, fixes real single-option Blibli parsing and records three exact-page prices plus fresh Brazil retail references. Its dated source observations supersede older cache-only evidence for those exact products; incomplete equivalence/costs still prevent a verified winner.

## Follow-up: stronger results

The subsequent [deeper verification pass](deeper-results.md) recovered two freshly readable, consistent Goofish 1 TB phone listings, four cached Blibli product candidates and an account-free public Taobao proxy-catalog quote. Version 0.5 adds bounded Goofish primary capture parsing/import, a Jadeship catalog command and visible-but-unranked cached observations. This supersedes the initial pass's zero-candidate outcome; it does not turn source claims into checkout verification. The original reports below retain their historical scope.

## What the live searches established

- [iPhone 17 Pro Max](iphone-17-pro-max.md): the all-market CLI search returned zero offers after index/API verification responses. Four product links were opened in the browser: a deleted Goofish item, JD login, a Blibli case behind verification, and a readable Goofish listing with contradictory storage/variant prices. **¥6,999 is not a verified 1 TB payable price.**
- [AirPods Max](airpods-max.md): guest search was blocked across the four markets. Twelve independent discovery queries found no verified current headphone offer in this pass; no marketplace product was opened. Apple's identification source distinguishes revisions without proving a seller's exact product.
- [ROG Zephyrus](rog-zephyrus-all.md): all four guest source searches were blocked. ASUS sources established G14/G15/G16/M16/Duo/S17 family context; no marketplace product link or deal was verified. Legacy coverage and secondary-display binding remain unresolved.

**No purchasable best-deal winner, live coupon eligibility, current BRL landed price, or account-free full-catalog coverage was established.** The challenged host in several CLI attempts was the search index, not the marketplace. A failed bounded search does not establish missing inventory. Browser observations are retained DOM/accessibility records unless a report explicitly identifies a screenshot.

## Changes made from the findings

- Offline `plan` suggestions preserve explicit model, storage, connector and accessory scope; broad Zephyrus plans offer bounded family queries. Chinese-market requests continue to require Chinese text supplied by the external agent.
- Query-aware ranking checks title and selected variant independently. Explicit accessories, other models, repair/replica/dummy listings and uncertain matches cannot win; deposit/monthly amounts remain unpriced. Query intent survives rank/coupon round-trips and bare exported offer arrays. Model tokens retain separators before capacities/years; selected iPhone shorthand is checked independently.
- Numeric JD mobile identities and nested Offer identities must agree with product URLs; contradictions remain unpriced after repeated normalization. Opaque JD product routes stay discovery-only without invented numeric SKUs. Unsupported-route counts disclose discovery omissions.
- One command shares verification gates by actual host. Later requests to that host are recorded as skipped without network access, while independent hosts remain available. A new invocation gets a fresh scope.
- Hydration retains per-target status/error/access receipts. Successful detail keeps original discovery evidence; failed detail keeps its unpriced lead and warnings. Verification stops further detail attempts for that source.
- Blibli JSON-LD stock/condition claims are retained. OutOfStock/SoldOut/Discontinued suppress ranking; InStock is a source claim, not verified checkout stock. Conflicting claims remain visible.
- Laptop comparison preserves negated facts, separates explicit family/chassis/code/year identities, normalizes bounded AMD/Chinese/ASUS typography, and rejects the copied-spec charger fixture. Direct comparison also checks accessory selections and monthly amounts without imported query intent. Generic identity and multiple-display binding remain incomplete.

## Verification of the revised code

At the close of the original 0.4 pass, **233 tests passed**. Current checks are recorded in [release validation](../VALIDATION.md). Ruff and whitespace checks pass. New synthetic regressions cover classifier, selected variants, identity round-trips, host-level request counts/reset, browser late challenges, stock claims, hydration, opaque routes, and coupon intent. These tests make no marketplace or account requests.

Seven retained AirPods classifier regressions pass against current code. Four retained Zephyrus examples were rerun through the actual current CLI with `--currency native`: accessory → zero groups; mixed families → four separate groups plus incomplete Duo; negated TGP → incomplete; AMD aliases → one shared group. The original frozen baseline evidence was preserved. Private current-code receipts are under `.local/search-validation/integrated-v04/`.

A follow-up Astra integration review confirmed the three reported redirect-attribution, exported-array and hydration-origin reproductions are resolved. A separate Astra product/comparison follow-up confirmed all four model-token, iPhone-shorthand, accessory-selection and monthly-price reproductions are resolved. Those reviewers ran focused offline tests and positive controls; the root ran the full suite. Local fixture passes and review findings do not establish live marketplace accessibility. Package/build/hosted checks are recorded in [release validation](../VALIDATION.md).

No marketplace account, fake identity, cart, purchase, coupon redemption, seller message, payment, shipment or customs declaration was created. No AI API credentials are used by the CLI. Private raw captures and provider receipts stay outside Git.
