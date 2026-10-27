# Fresh acquisition validation — 2026-10-27

This update replaces a dependence on indexed leads with exact-link first-party refresh attempts, explicit observation age, local history and separate promotion evidence. It does not claim universal guest access or verified checkout.

## Fresh source observations

| Source | Acquisition | Observed price | Preserved limits |
| --- | --- | --- | --- |
| [Goofish iPhone 17 Pro Max 1 TB silver](https://www.goofish.com/item?id=1092800987315) | Actual T3 incognito main-item DOM at **17:08:36.022Z**, followed by actual offline capture CLI import | **¥7,499**, **R$6,014.29** product reference | 90% battery, replaced outer screen and wholesale-price claims. Stock, exact unit, Fansbuy procurement and import eligibility unverified. |
| [Blibli AirPods Max 2024](https://www.blibli.com/p/airpods-max-2024/ps--HEO-70120-00970) | Actual public HTTP response at server-date claim **17:16:19 GMT**; retained-file write **17:16:20.102769Z**; new primary-state parser replayed offline | **Rp8,799,000**, **R$2,594.03** product reference; selected **Midnight / HEO-70120-00970-00001 / PP-3460337** | Source claims stock 1; **delivery unavailable, pickup available/selected**. Listed reference Rp8,999,000 and advertised 2% discount are source claims, not measured historical savings. Condition, checkout and procurement unverified. |

BRL references use retained ECB 2026-10-27 cross-rates, excluding freight, payment FX/spreads, fees and taxes. Blibli international freight follows the user's excluded policy; that does not mean tax or transport is zero.

Blibli's price was present in an embedded **first-party product summary**, not its JSON-LD. The previous reader accepted only JSON-LD and missed this format. The new reader binds parent product, selected child SKU, option attributes, native URL and pickup point before emitting a price. It refuses contradictory selections and duplicate/ambiguous state. The read response hash is `1a2defd15c7a301920caf43f1097acefb277ad1360db9fae9ca2cdd7107c464e` (235,341 UTF-8 bytes). Its server date is a source claim, not an independently verified price-update timestamp.

[Public normalized Blibli observation](../../examples/blibli-primary-observation-2026-10-27.json). Raw response and tool captures stay private under `.local/freshness-release/`. The retained file timestamp records the write after the successful request; it is not represented as a browser screenshot. A subsequent T3 Blibli open reached `/challenge/landing/` and was stopped; no new request was made to validate the integrated reader after that challenge. This is **actual public HTTP acquisition plus offline extraction/integration checks**, not new post-integration live transport proof.

## Live CLI refresh and promotion checks

A real HTTP `refresh` invocation with JD `100214660452` and the Blibli parent URL completed with exit **3 / partial** and retained two SQLite receipts. JD loaded but its price stayed null. The then-existing JSON-LD-only Blibli reader returned `item_schema_unverified` and no price. Both failures remained unpriced; no cached amount was substituted. The retained Blibli response inspection then led to the new state reader above.

A real `promotions` read of that Blibli product returned `empty_unverified`, no visible coupon snippets. The embedded state has product-price claims but no campaign rules. This is not evidence that no coupons exist. No extra coupon discount was applied.

Actual `history` CLI readback returned the stored receipts without network access. A masked, failed or stale refresh keeps prior observations separate. Observation time and retrieval/attempt time remain distinct. No scheduler, login, account, cart, purchase, message, voucher claim, redemption or shipment was created.

## Brazil references and decisions

See [Brazil primary-price research](brazil-price-references.md). Apple Max 2 A3454 showed a fresh R$5,931 cash reference. The foreign Max 2 source remains cached with unconfirmed identity/condition; the exact 2024 Brazilian comparator was unavailable, and another merchant's connector identity conflicted. Used/repaired phones and mismatched G16 configurations do not establish comparable savings.

The real [comparison input](../../examples/brazil-references-2026-10-27.json) therefore produces `needs_review`. Synthetic complete cases demonstrate all financial outcomes and incomplete-cost budgets; they are explicitly fake. Unknown freight, fees, delivery or taxes never become zero. Observed freight expiry/age, price age and FX date hold financial decisions. No tax-engine estimate or import-eligibility assertion is treated as legal clearance.

## Offline checks

Regression coverage includes cached-source exclusion, future/stale timestamps, strict age policy through exported arrays, transaction/variant evidence through repeated ranking, product URL and stock binding, independent exclusions, coupon windows/account conditions, source-reader challenges, history dedup/concurrency and failed-price suppression. Independent Astra reviews and their exact scope are recorded in [VALIDATION](../VALIDATION.md). Fixtures and local green tests do not establish live source access.
