# Alibaba.com and AliExpress — 0.9.0

The registry now has nine distinct marketplaces. Alibaba.com (`alibaba`) is
separate from 1688. AliExpress is `aliexpress`. Neither is added to the five
platforms explicitly named by the retained Fansbuy evidence.

## Implemented contract

- Guest HTTP/browser index discovery, exact native product routes, primary
  metadata, offline HTML captures, refresh/history and promotional evidence.
- English/localized queries; Chinese overrides apply only to Chinese platforms.
- Native OpenCLI operations explicitly unavailable; no invented native facets.
- Public metadata remains unpriced. JSON-LD amounts, price tiers, MOQ and stock
  claims do not establish a selected, single-unit full-payment purchase quote.
- Imported numeric prices require an explicit supported currency. Conflicts,
  missing currency, unsupported codes and bulk/tier constraints remain unpriced
  through repeated JSON normalization/ranking. Regional AliExpress hosts remain
  bound to their source context; unverified SKU/quantity URL bindings reject.
- Manual shipping. Brazil comparisons require applicable freight, taxes,
  insurance, fees, equivalence, condition and fresh evidence before savings.
  A missing FX cross-rate leaves the BRL amount unknown.

## Bounded live evidence — 2026-10-28

One Alibaba guest detail attempt returned a complete decoded HTML response for
[product 1601604728918](https://www.alibaba.com/product-detail/Wesdar-Factory-Wireless-Headphones-Fabric-Headsets_1601604728918.html).
The requested and final URLs agreed. Numeric HTTP status was not separately
retained. Observation: `2026-10-28T11:32:48.705491+00:00`; 420,978 UTF-8 bytes;
SHA-256 `95ee75008d8bf68a63b879bea187e1854e652829903d2d434fb599fcd8ef8fcb`.

The original acquisition receipt records the initial parser rejection and is
unchanged. A later **offline replay** of those exact bytes succeeds with an
exact product identity, localized native OG URL, USD source claims and no ranked
price. This is not a second live request or post-fix transport verification.

One [AliExpress US detail attempt](https://www.aliexpress.us/item/3256808715119298.html)
stopped with `blocked / redirect_denied`. No product body or selected-price
verification was obtained. No alternate regional route, login or challenge retry
was used. Index snippets remain discovery only.

Private bodies and original/replay receipts are in
`.local/international-expansion/`; package builds exclude that directory.
No checkout, stock, authentic seller, eligible coupon or purchasable deal was
verified for either new marketplace.

## Verification and release policy

556 local tests pass with outbound sockets and DNS blocked. Regressions cover
four-pass currency/quantity provenance, exact route identity, offline capture
coupons, guest/browser dispatch, shared challenge guards, refresh/history,
manual costs and international FX/coupon arithmetic.

Release 0.9.0 is followed by 0.9.1, 0.9.2 and subsequent patch increments unless
the user explicitly requests otherwise. `scripts/bump_version.py` defaults to a
dry run. Writes require an explicit `--from BASE`; retrying that base reconciles
both version files to the same target, including interrupted partial writes.
