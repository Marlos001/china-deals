# Blibli deeper validation — 27 October 2026

**Useful source-bound candidates were recovered, but no current checkout was verified.** Connector-readable Blibli product pages and indexed primary-product blocks can support a source-claimed candidate even when the interactive site gates. Preserve that evidence tier: a fresh retrieval of an old crawl does not refresh price or inventory. This pass used 12 connector search queries and 3 exact native product opens; it ended once sufficient bounded evidence was available. No application code, commits, purchases, carts, accounts, messages or CAPTCHA interaction.

## Evidence and access

Research date: **2026-10-27**, Brazil/East. Retention/retrieval timestamps are UTC in the private receipts. Initial discovery and the successful AirPods open were retained at **16:28:22Z**; their exact retrieval instants were not separately logged. Subsequent open results were recorded at **16:28:23Z**, exact-product index results at **16:28:40Z**, and specification/coupon results at **16:28:50Z**. These timestamps describe this research, not source updates. Crawl ages below are the connector's literal relative ages; exact crawl times are unavailable.

`preview_status` reported no attached tab and listed an incognito profile. The prior direct Blibli challenge was already known from [v2](../research/zephyrus-g16-blibli-v2.md); it was not retried. No browser tab was opened, so none required closing. One connector open returned readable cached product content. Two other exact products, submitted in the same batch, returned **403 Forbidden**. No subsequent native opens were made; independent indexed-search evidence remained readable. This is not browser success or a bypass.

Private receipts: [preview status](../../.local/deeper-validation/blibli/01-preview-status.json), [Chinese-query discovery](../../.local/deeper-validation/blibli/02-discovery-zh.json), [AirPods search and successful open](../../.local/deeper-validation/blibli/03-airpods-discovery-open.json), [two failed opens](../../.local/deeper-validation/blibli/04-new-product-opens.json), [exact-product index](../../.local/deeper-validation/blibli/05-exact-product-index.json), [specification and campaign index](../../.local/deeper-validation/blibli/06-spec-coupon-index.json). Raw responses remain Git-ignored; no client IP is included in this report.

Chinese discovery used `AirPods Max USB C 全新 现货 价格` and `华硕 ROG 幻16 Zephyrus G16 RTX 5070 harga stok`, scoped to Blibli product pages. Exact IDs and Indonesian terminology then refined the results. Blibli is an Indonesian marketplace; Chinese queries do not establish Chinese domestic inventory.

## Product-bound candidates

All amounts below are **source-displayed IDR prices**, without extra coupon deductions. Stock is a cached source claim, not current availability. Condition, authenticity and checkout acceptance remain unverified. A list of color options does not establish the selected color or its inventory.

| Exact product / source | Observed configuration and seller | Price / comparison | Source stock and freshness | BRL product reference |
| --- | --- | --- | --- | ---: |
| [AirPods Max 2024, HEO-70120-00970][A1] | Hello Flagship Store, Uptown Mall BSB City, Semarang. Primary description explicitly says USB-C, H1 and up to 20 hours; box includes headphones, Smart Case and charging cable. Blue/Midnight/Orange/Purple/Starlight options; selected color unknown. | **Rp8,799,000** / Rp8,999,000, displayed 2% reduction | **1 remaining**, indexed product block, **2 weeks ago**. Native connector open: 403. | **R$2,707.34** |
| [AirPods Max, BLS-70244-00413][A2] | Blibli Store Flagship Store, TSM Cibubur, Depok. Primary specification claims one-year official warranty. Space Grey/Green/Pink/Silver/Sky Blue options. Connector and selected color **not established**. | **Rp8,799,000** / Rp9,499,000, displayed 7% reduction | **1 remaining**, readable product-page connector open, **3 months ago**. | **R$2,707.34** |
| [Airpods Max 2, APF-70017-00964][A3] | Blibli – Apple Authorized Reseller Flagship Store, Gudang Blibli. Primary title/description claims Max 2 and H2. Blue/Midnight/Orange/Purple/Starlight options; selected color and connector unknown in retained primary excerpt. | **Rp10,499,000**; comparison amount not observed | **2 remaining**, indexed product block, **2 weeks ago**. No native open. | **R$3,230.41** |
| [Zephyrus G16 GU605CP-I957OL1G-HM, ITG-70010-02072-00002][Z1] | IT Galeri Flagship Store, Tangerang. **+ANTIVIRUS** in exact variant title; Ultra 9-285H, RTX 5070 8GB, RAM 32GB, SSD 1TB, 16-inch 2560×1600 OLED 240Hz, Windows 11 Home. | **Rp60,249,000**; comparison amount not observed | **1 remaining**, indexed product block, **last week**. Native connector open: 403. Seller asks buyers to confirm stock before ordering. | **R$18,537.84** |

The USB-C/H1 evidence makes A1 the more specific 2024 lead than A2, despite the same displayed amount. Neither is a proven newly sealed unit: no primary condition field was recovered. For A3, reviews claiming sealed goods or a Rp9,550,000 flash sale are historical customer statements and are excluded from its current product price/condition. The seller's Max 2 label is retained without independently authenticating the model.

Z1's price includes Indonesian PPN according to the seller. The retained material calls the store official and goods original; these are seller assertions. No laptop TGP, VRAM type, warranty duration or explicit condition was recovered for this exact variant. A **base-title listing card with no selected variant established** at Rp59,999,000 on a [category page](https://www.blibli.com/jual/laptop-rog-zephyrus), crawled four days ago, has weaker variant binding: it must not overwrite the +ANTIVIRUS amount. No seller contact was performed.

FX is the **existing saved ECB XML dated 2026-10-26**, not a fresh fetch: EUR 1 = BRL 6.2523 and IDR 20,320.32. Formula: `BRL = IDR × 6.2523 / 20320.32`, rounded once to cents. [Retained source copy](../../.local/deeper-validation/blibli/ecb-fx-2026-10-26.xml); [original source URL](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml). Freight, forwarding, spread, payment fees, IOF and import taxes are excluded. These are product reference conversions, not landed or payable quotations.

## Reconciliation with the five older leads

The [v2 five-link record](../research/zephyrus-g16-blibli-v2.md) remains authoritative for what the user previously supplied, not for current live prices. P1/P2/P4/P5 were not reopened. P2's previously supplied selected-variant screenshot said out of stock; no new evidence supersedes it.

A new exact-ID index query for **P3 / DWJ-29772-01622** returned the same **four-month-old** primary product block: Rp43,800,000, comparison Rp45,500,000, and 5 remaining. That is a repeated cached observation, **not an improvement in freshness**. A [category page crawled today](https://www.blibli.com/jual/asus-rog-zephyrus-gu605) instead contains a matching-title P3 card at Rp55,700,000 against Rp58,900,000. The user had supplied Rp54,029,000. Preserve all three observations separately; the category card does not refresh the old product's stock, prove its selected variant, or verify the user's payable amount. No old lead is relabeled live.

Other search results included AirPods prices inside iPhone recommendation sections, and a merchant page crawled 1.4 years ago showing Rp8,499,000. Neither is used as a primary-product candidate. No claim is made about marketplace-wide cheapest pricing or absence of better inventory.

## Coupons

The [LAPORIN campaign](https://www.blibli.com/promosi/kga-laporin), newly retrieved through the index with crawl age **last week**, advertises `LAPTOP4-2JT`: 3%, cap Rp2,000,000, minimum Rp3,000,000, selected Intel laptops, **1 Oct–31 Dec 2026**. Its surrounding campaign promotes ADVAN/POLYTRON/AXIOO. Exact ASUS SKU/seller participation, remaining quota, stacking and actual purchasing-account eligibility are unknown. **No extra discount is applied.**

The same page advertises `MEGA-KGA500` (5%, cap Rp500,000, minimum Rp3,000,000, Mega credit card, full payment or 3/6/12-month installments, until 31 Jan 2027), and `PL-KGA12` (10%, cap Rp1,500,000, minimum Rp1,000,000, Indodana-powered Blibli Tiket PayLater, 12/24-month installments, until 31 Dec 2026). Payment eligibility, costs, quota and SKU applicability remain unresolved. These are campaign leads, not validated cash discounts. No AirPods-specific extra coupon was established. Listing percentages are already displayed reductions and are not subtracted again. A customer's entitlement is not evidence for a distinct forwarder's purchasing account.

## Concrete extraction improvements for the root agent

These are implementation recommendations from evidence, **not code changes or a new CLI regression test**. The current README already keeps index prices unranked; preserve that guarantee while making useful source claims visible.

1. Add an explicit **source-claimed candidate view** alongside ranked results. Separate source mode (`connector_product_open_cached`, `indexed_product_block`, `category_card`, `user_observation`) from access outcome and checkout verification. A native 403 must not erase a retained, exact-product index observation. Such records stay outside current-deal winners.
2. Record `retrieved_at`, raw `crawl_age`, nullable exact `crawled_at`, native product ID, seller, variant ID and pickup-point context per observation. Never timestamp a cached stock statement as fresh inventory. Keep conflicting prices as separate observations with evidence IDs; do not merge category freshness with product stock.
3. Bound primary content by product identity and section. A2's successful open places its own title/price/stock at lines 42–47, seller at 65–71, specifications at 81–87 and own total at 103–107; unrelated footer blocks start after line 109. For indexed responses, require the exact `/p/` URL plus matching product-ID heading and isolate its main price/stock/description. Exclude reviews, recommendations, category price minima, navigation and other product headings. Missing trustworthy boundaries mean discovery only.
4. Preserve variant uncertainty. `ps--` product pages with color lists are not selected-color offers. Z1's `is--...-00002` and +ANTIVIRUS title establish a narrower scope than the unselected category card. Retain `pickupPointCode=PP-3557967`; do not infer all-region stock. A URL is an identity anchor, not proof of completeness or live availability.
5. Normalize **Tersisa N Produk** as `source_claimed_in_stock`, retaining quantity N and literal evidence; use `checkout_verified=false`. Condition remains unknown unless a primary condition statement is bound. Reviews saying sealed/new cannot populate it. Store badges do not prove authenticity; buy buttons do not verify stock or payment acceptance.
6. Extract exact descriptive hardware evidence, not family maxima or adjacent offers: A1's USB-C/H1 is supported; A2 connector remains unknown; Z1 TGP remains unknown. Keep incomplete hardware groups separate. Numeric prices in recommended iPhones, accessories or financing text must not establish the requested whole product's price.
7. Keep raw display price, comparison amount and advertised sale percent separate from coupon reductions. Coupon eligibility needs the exact purchasing account, product/seller, dates, payment method, quota and stacking terms. Preserve dated FX provenance and explicitly exclude Blibli freight.

Suggested offline acceptance fixtures are the four retained candidates plus P3's old/product versus fresh/category conflict: assert that useful candidates survive a native gate while no cache becomes a live winner, no review price is imported, no selected color or condition is invented, and no +ANTIVIRUS price is replaced by an unselected category-card amount. This research pass did not execute those tests or call the application CLI.

## Handoff

Owned artifacts: this report and `.local/deeper-validation/blibli/` only. Private `candidates.json` holds normalized research observations (not a CLI-compatible import contract); `manifest.json` records query/open budgets and hashes. Application code and other agents' work were preserved. No processes or tabs remain running. The next authorized implementation step belongs to the root agent: expose these evidence levels without loosening current-price verification. Further native Blibli retries are not justified by this pass.

[A1]: https://www.blibli.com/p/airpods-max-2024/ps--HEO-70120-00970
[A2]: https://www.blibli.com/p/airpods-max/ps--BLS-70244-00413
[A3]: https://www.blibli.com/p/airpods-max-2/ps--APF-70017-00964
[Z1]: https://www.blibli.com/p/asus-rog-zephyrus-g16-gu605cp-i957ol1g-hm-intel-core-ultra-9-285h-rtx5070-8gb-ram-32gb-ssd-1tb-16-inch-2-5k-oled-240hz-windows-11-home/is--ITG-70010-02072-00002?pickupPointCode=PP-3557967
