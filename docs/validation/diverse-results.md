# Diverse-search iteration — 27 October 2026

This pass expanded the original phone/headphone/laptop searches to Steam Deck OLED, Sony WH-1000XM6, Ryzen 9800X3D, RTX 5070 Ti, DJI Mini 4 Pro and Nintendo Switch 2. It produced three exact-page foreign price observations and useful Brazil references. **No complete landed-cost winner, checkout stock or additional redeemable coupon was verified.**

## Actual source reads

Five Blibli product pages returned HTTP 200 at approximately **17:37:49–17:37:57 UTC**. These retained response bodies differ from earlier search-index cache observations. Four previously unhandled single-option pages exposed empty variant attributes; the parser now accepts that shape only with one coherent selected option and an explicitly empty attribute catalogue.

| Exact source product | Offered IDR | Product-only BRL reference | Brazil reference and implication |
| --- | ---: | ---: | --- |
| Sony WH-1000XM6 Platinum Silver | 6,179,000 | R$1,821.63 | R$2,609.10 Pix/boleto; conditional nominal gap R$787.47 before unresolved costs/equivalence. |
| Ryzen 7 9800X3D Box | 8,905,000 | R$2,625.28 | R$2,199.99 Pix; foreign product reference already R$425.29 higher. |
| DJI Mini 4 Pro with RC 2 | 12,266,000 | R$3,616.14 | Exact Standard RC 2 Brazil reference is sold out; no available comparison. |
| Steam Deck OLED White Limited Edition 1TB | unknown | unknown | Price absent, selected option unavailable despite a positive stock field. |
| Gigabyte RTX 5070 Ti Gaming OC 16G | unknown | unknown | Price absent, stock zero, selected option unavailable. |

BRL arithmetic uses the [dated ECB snapshot](../../examples/fx-reference-2026-10-27.json), not payment FX. The [Blibli report](diverse-blibli-2026-10-27.md) retains native URLs, response hashes, exact selection/fulfillment claims and limitations. The [Brazil report](diverse-brazil-2026-10-27.md) records four merchant navigations at **17:53:55–17:54:47 UTC**, full payment conditions, stock conflicts and package differences. [Normalized foreign observations](../../examples/diverse-fresh-observations-2026-10-27.json) support offline replay; replay does not renew their age.

Condition remains unknown on the foreign rows. Regional package/warranty equivalence and all applicable import charges/payment fees remain unresolved. Blibli freight follows the user's exclusion policy; that does not assert zero transport or tax costs. Sony's advertised 18% reduction is already reflected in the offered amount, and was not deducted again. No additional campaign or voucher savings were asserted.

The [China pass](diverse-china-2026-10-27.md) used twelve discovery queries and retained four Goofish captures. They exposed mixed-capacity price basis, wrong indexed models, sold and delisted items. All four target-price fields remain null. A failed bounded search does not establish absent marketplace inventory. Search challenges stopped further acquisition on affected surfaces; no alternate transport was used to evade them.

The [replayable Brazil input](../../examples/diverse-brazil-comparison-2026-10-27.json) deliberately leaves costs and equivalence unresolved:

```sh
china-deals brazil-compare examples/diverse-brazil-comparison-2026-10-27.json
```

All three cases return `needs_review` with null savings. Sony/Ryzen product subtotals remain visible; the sold-out Brazilian DJI amount is excluded. The frozen `as_of` reproduces the historical comparison. For a decision now, refresh the source observations and use the current time and current cost/FX evidence.

## Changes driven by these searches

- Nine bounded intent families now have local relevance checks and offline query plans. Plans preserve explicit scope; unfamiliar intent stays visible and unranked until supported. They do not perform AI calls or promise catalogue coverage.
- Title and independent selected observations retain identity, accessory and refinement conflicts through normalization/export/reranking. Compatible model facts can resolve a mixed title; generic color alone cannot. Literal CPU package, GPU role, controller/bundle and typed memory/storage evidence remain separate. Complete advertised model/suffix pairs must agree with a selection; independently consistent selected fields may still combine. Explicit numeric unit fields such as `ram_gb` and `storage_tb` retain their meaning.
- Compatibility wording cannot turn replacement accessories into full devices. A genuine complete device bundled with an accessory remains eligible when source identity is sufficient.
- Transaction checks inspect retained selected/payment evidence and bounded raw-price scope. Deposit, monthly installment, remaining balance, rental and starting prices cannot win as full-item amounts. A naked model suffix such as GPU `3X` does not establish installment scope.
- `--include-offers` exports the same assessed transaction/relevance holds as ranking. Filter failures remain available separately as `filter_excluded_offers`; reranking retains their holds. Term filters remain literal title substrings, not model-aware filters.
- Blibli preserves missing price, selected availability, stock/fulfillment conflicts, campaign/installment/preorder claims and merchant-location basis. Parser diagnostics include a safe reason and response-text hash without returning the full body.
- Goofish recognizes explicit sold wording, preserves unresolved capacity context, and withholds qualified base/reference amounts. Condition claims are bound to the main product; a new replacement screen or gifted case cannot mark the device new.

## Verification boundaries

The committed synthetic fixtures retain the original **105-case** multilingual corpus plus the independent reviewers' **62-case and 56-case adversarial sets**, exercised through repeated ranking. They are selected regression cases, not a random sample or a live accuracy measure. Mocked CLI export/import checks exercise the production normalization boundary without marketplace requests.

Full-suite, package, independent review and release receipts are recorded in [VALIDATION](../VALIDATION.md). Retained captures prove historical source observations and offline extraction. They do not prove current checkout, coupon redemption, authentication, seller reliability or universal marketplace access. Raw bodies, browser records and provider receipts remain private under `.local/diverse-search/`.
