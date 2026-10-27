# Stronger verification and usable candidates — 2026-10-27

This follow-up recovered useful source-bound candidates after the 0.4 pass. **Two Goofish phone pages were freshly readable with consistent 1 TB descriptions/attributes and displayed prices. Four Blibli candidates have cached, exact-product evidence. A public Taobao proxy-catalog price was reproduced by the actual CLI over plain HTTP.** No checkout, purchase, seller contact or marketplace registration was performed.

## Product references in BRL

All conversions here use one freshly retrieved **ECB snapshot dated 2026-10-27**: [portable snapshot](../../examples/fx-reference-2026-10-27.json), [ECB source](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml). BRL amounts are product references only. Freight, import taxes, spread, payment fees and IOF are excluded. Blibli freight is deliberately excluded. Native source prices and evidence tiers remain separate.

| Product/source | Source amount | BRL reference | What was actually established / material limitation |
| --- | ---: | ---: | --- |
| [iPhone 17 Pro Max 1 TB, silver — Goofish](https://www.goofish.com/item?id=1092800987315) | ¥7,499 | R$6,014.29 | Fresh main page; 1 TB consistent; seller claims 90% battery and replaced outer screen. Wholesale-price qualifier; minimum/eligibility and shipping unknown. Used/repaired. |
| [iPhone 17 Pro Max 1 TB, orange — Goofish](https://www.goofish.com/item?id=1096499480089) | ¥7,999 | R$6,415.30 | Fresh main page; 1 TB consistent; seller claims 91% battery and cosmetic wear. **Pickup only in Qingdao Chengyang**, despite generic free-shipping badge. |
| [iPhone 17 Pro Max title — Jadeship/Taobao 982744194230](https://www.jadeship.com/item/taobao/982744194230) | ¥6,138 | R$4,922.75 | Fresh proxy-catalog display and successful CLI HTTP read. Variant, condition, stock and underlying fetch time absent. **Not a verified new/1 TB handset price.** |
| [AirPods Max 2024 USB-C — Blibli](https://www.blibli.com/p/airpods-max-2024/ps--HEO-70120-00970) | Rp8,799,000 | R$2,594.03 | Exact-product cached block, crawl “2 weeks ago”; USB-C/H1 description, one-unit stock claim. Present stock, selected color and condition unknown. |
| [AirPods Max — Blibli](https://www.blibli.com/p/airpods-max/ps--BLS-70244-00413) | Rp8,799,000 | R$2,594.03 | Readable cached product open, crawl “3 months ago”; connector not established. Same displayed amount does not prove the same revision. |
| [AirPods Max 2 — Blibli](https://www.blibli.com/p/airpods-max-2/ps--APF-70017-00964) | Rp10,499,000 | R$3,095.21 | Exact-product cached block, crawl “2 weeks ago”; source claims Max 2/H2 and two units. Selected color/connector, authenticity and current stock unverified. |
| [Zephyrus G16 GU605CP, RTX 5070, 32 GB, 1 TB +ANTIVIRUS — Blibli](https://www.blibli.com/p/asus-rog-zephyrus-g16-gu605cp-i957ol1g-hm-intel-core-ultra-9-285h-rtx5070-8gb-ram-32gb-ssd-1tb-16-inch-2-5k-oled-240hz-windows-11-home/is--ITG-70010-02072-00002?pickupPointCode=PP-3557967) | Rp60,249,000 | R$17,762.02 | Exact-variant cached block, crawl “last week”; Ultra 9 285H, OLED 240 Hz, one-unit claim at the specified pickup context. TGP/condition and current stock unverified. |

These are a practical shortlist, not equivalent configurations or universal best-value winners. The phone price differences include repair, condition and fulfillment differences. Used consumer imports require the [Brazil import review](../research/shipping-brazil.md); a Fansbuy quote or sea transport does not establish legal eligibility. Pickup-only is a substantial obstacle for a link-based buying-agent workflow.

The Blibli report uses an older saved 2026-10-26 FX snapshot, so its BRL numbers differ from this common-date table. This report does not refresh its cached prices or inventory. No new source supersedes the user's older out-of-stock G16 screenshot. Earlier user prices and cached historical prices remain separate observations.

## What improved in the CLI

`catalog taobao ID_OR_URL` reads Jadeship's publicly delivered, item-bound catalog props, with no account, AI API, browser or new runtime dependency. It decodes literal JSON without running scripts and rejects mismatched/contradictory item prices. It returns a separate `catalog_observations` quote and BRL reference; the normal marketplace `price.amount` remains null. This is an optional third-party information path, not Taobao guest catalog coverage.

```sh
china-deals catalog taobao 982744194230
china-deals catalog taobao 'https://item.taobao.com/item.htm?id=982744194230' --currency native
china-deals rank examples/deeper-candidates-2026-10-27.json \
  --fx-from-json examples/fx-reference-2026-10-27.json --format markdown
```

Cached/product-index/category/proxy modes remain unpriced for fresh-offer rankings. Their exact source observations can still show a native amount, separate BRL reference and crawl age. Re-ranking/importing cannot silently turn these values into current marketplace prices. No extra coupon is deducted from them.

The Goofish primary-DOM reader now has tests for the two consistent listings, two ambiguous controls, requested/final ID binding and recommendation exclusion. Its fixed capture expression was run on the orange listing in T3 at **2026-10-27T16:46:50.751Z**: one main/info/price/description/labels region, 31,637 UTF-8 bytes. Actual CLI capture import retained ¥7,999, R$6,415.30, the exact capture time, used condition and pickup-only conflict, with no network access. This verifies T3 capture plus CLI ingestion, not a successful live Playwright CLI fetch. The wired fresh-browser backend has offline integration coverage.

```sh
china-deals detail goofish 1096499480089 --guest-engine browser
china-deals detail goofish 1096499480089 --from-browser-json capture.json \
  --fx-from-json examples/fx-reference-2026-10-27.json
```

Capture imports stay offline: without a local FX snapshot, native amounts remain and a warning explains how to get BRL. Browser-capture authenticity/time are caller-supplied; importing does not authenticate a file or refresh its observation. Price binding currently recognizes phone-style model/storage evidence; other product families remain unpriced until a suitable contract is validated. No main-page data is inferred from recommendation cards.

## Other avenues checked

- **Fansbuy:** its guest homepage and ordinary search input loaded. Root entered a Chinese laptop query. A human-control interruption occurred before a reliable search-result capture; a later passive status was on Google sign-in. This does **not** establish a clean guest-search outcome or attribute the later OAuth navigation to the automated search. A direct static-asset request returned 403 and was not retried. No account was created or Google consent granted by the agent.
- **Extension route:** [easyupoo](https://github.com/1etu/easyupoo) is MIT and reads Jadeship prices using a public page selector. This demonstrates an alternate catalog, not recovery of server-withheld Taobao prices. Source was inspected; the extension was not installed or executed and no extension code was copied.
- **External dealer context:** [the Zephyrus report](zephyrus-deeper.md) found 11 priced ordering rows for G14/G16/Duo on an accessible dealer page. They are **outside the requested marketplaces**. Visible ordering text conflicts with schema stock claims and one G14 code is ambiguous; those references do not become JD/Taobao/Goofish offers or verified stock.
- **JD/Taobao:** additional exact JD discovery hit verification/login; bounded Taobao discovery did not yield another usable direct handset link. No inventory-wide absence is inferred. Existing service-login/risk pages were not operated or circumvented.

Details: [phones and DOM boundaries](iphone-deeper.md), [Blibli product/coupon evidence](blibli-deeper.md), [broader Zephyrus price context](zephyrus-deeper.md). No additional eligible coupon was established. Root's Jadeship HTML, DOM screenshot, HTTP provenance, live CLI output and original FX snapshot are retained privately under `.local/deeper-validation/catalogs/`; public examples contain source facts and links, not credentials or browser sessions.

## Release verification

Root ran **266 tests**, Ruff, compilation, whitespace/link checks and a 0.5.0 wheel/sdist build. Independent Astra review and follow-up verified the reported catalog currency/ambiguity/overflow/whitespace and offline-import objections resolved. All four retained Goofish captures replay correctly; a fresh T3 capture also matched actual CLI ingestion. These are code/capture checks, not checkout or live Playwright-transport proof. Hosted CI and an exact GitHub-commit installation are checked separately after publication.
