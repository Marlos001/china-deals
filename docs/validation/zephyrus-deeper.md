# Zephyrus deeper public-source research — 2026-10-27

## Result

**Useful source-claimed leads were found: 11 whole-laptop configurations in a Chinese domestic dealer's current public price sheet. No checkout, transaction, or confirmed physical stock was verified.** These are priced ordering leads, not a cheapest-deal claim or a verified-purchasable result. Exact ASUS and Suning product links were also recovered, with narrower evidence described below.

Research used 12 Chinese-language connector search queries and five native page navigation attempts, counting the dealer catalog against the product-open allowance. Search/page observation window: approximately **16:27–16:31 UTC on 2026-10-27**. No Goofish or DDG retry, CAPTCHA operation, session fabrication, proxy rotation, login, cart, purchase, account, or messages. The owned incognito tab was closed. Research ended when the navigation/query budgets were exhausted.

Only this report and `.local/deeper-validation/zephyrus/` are owned. Baseline HEAD: `eafc55fb59173ddd1227bb2933788e97de2c3001`. Initial tracked worktree status was clean; peer `docs/validation/blibli-deeper.md` appeared during research and was preserved. No application code edits, commit, push, or application test claims.

## Live dealer observations

Source: [华强北商行 ASUS ordering price sheet](https://www.hqbnb.com/asus), which automatically resolved to [its English rendering](https://www.hqbnb.com/en/asus). Chinese source names remain in the page's embedded JSON-LD. **Observed 2026-10-27T16:30:57.349Z**; page update label **2026.10.21 11:41** (timezone unspecified); schema validity **2026-10-21 through 2026-10-28**. The earlier connector excerpt was a September snapshot; it is superseded here by the fresh browser observation.

All rows below belong to the main `article .entry-content`, not sidebars or recommendations. Prices are CNY. Every row claims Ultra 9 386H and 1 TB storage. GPU notation below preserves the dealer's shorthand; complete RTX model naming/TGP is not independently established for these exact offerings.

| Claimed family / literal model code | RAM | GPU shorthand / VRAM | Color | Source price |
| --- | --- | --- | --- | ---: |
| G14 / GA403AM386 | 32 GB | 5060 / 8 GB | 日蚀灰 | 20,100 |
| G14 / GA403AM386 | 32 GB | 5060 / 8 GB | 铂月白 | 20,100 |
| G14 / GA403AP386 | 32 GB | 5070 / 8 GB | 铂月白 | 21,900 |
| G14 / GA403AR386 | 64 GB | 5070TI / 12 GB | 铂月白 | 28,700 |
| G16 / GU606AM386 | 32 GB | 5060 / 8 GB | 灰 | 22,800 |
| G16 / GU606AM386 | 32 GB | 5060 / 8 GB | 白 | 22,800 |
| G16 / GU606AP386 | 32 GB | 5070 / 8 GB | 白 | 23,800 |
| G16 / GU606AR386 | 64 GB | 5070TI / 12 GB | 白 | 30,400 |
| G16 / GU606AX386 | 64 GB | 5090 / 24 GB | 白 | 42,000 |
| Duo / GX651AR386 | 64 GB | 5070TI / 12 GB | unspecified | 37,600 |
| Duo / GX651AX386 | 64 GB | 5090 / 24 GB | unspecified | 47,600 |

These are **catalog-row links**, all at the same source URL; the source did not supply a unique product URL per row. Do not fabricate individual item IDs. Retained JSON-LD positions 67–77 distinguish the observed rows; they are snapshot positions, not durable seller SKUs. Display claims: G14 14-inch 2.8K OLED 120 Hz; G16 2.5K OLED 120 Hz; Duo 16-inch 2.8K OLED 120 Hz. Preserve these literally pending hardware confirmation. In particular, the dealer's Intel G14 `GA403…386` coding needs checking against the [ASUS 2026 GU405 identity discovered by connector](https://rog.asus.com.cn/laptops/rog-zephyrus/rog-zephyrus-g14-2026-gu405/); do not silently correct the code or merge it into an official SKU.

**Availability:** visible rows say “to order” / Chinese names contain 订货. Each matching JSON-LD Offer says `https://schema.org/InStock`; its templated description also mentions Shenzhen in-stock quotes. Preserve the inconsistency as **source availability ambiguous: ordering lead, physical stock unknown**, not confirmed availability and not delisted. No stock quantity or delivery lead time was observed.

**Terms and condition:** the page states CNY, EXW Shenzhen pickup terms, a bilingual shipping receipt, and CN meaning mainland-China warranty version. Actual warranty, merchant reliability, condition/newness, taxes, forwarding, shipping to Brazil and final costs were not verified. No per-row condition or coupon terms were observed. The label `GB` is retained without interpretation; no subsidy/coupon deduction is applied. These observations make the leads useful without requiring account/cart access.

## Exact native product links and family coverage

| Family | Exact source link | Evidence and limit |
| --- | --- | --- |
| G14 | [ASUS 幻14 Air 2025 GA403 WTB](https://rog.asus.com.cn/laptops/rog-zephyrus/rog-zephyrus-g14-2025/wtb/) | Live browser main content and SKU columns read at 16:28:53 UTC. Includes GA403WW370-0GDHXHBAX20, GA403WR370-0ECHXHBBX20 and GA403WP370-0ECHXHB8X20; whole-laptop CPU/GPU/RAM/storage evidence. No numeric price; family JSON-LD says InStock with an empty price. |
| G14 store destination | [ASUS productId 42244700703929](https://www.asus.com.cn/store/goods/detail?productId=42244700703929) | Followed the literal WTB link; resolved to the generic wap.asus.com.cn homepage, losing product identity. Homepage prices are excluded. A second [literal destination 42244700704283](https://www.asus.com.cn/store/goods/detail?productId=42244700704283) was captured but not opened. |
| G15 | [JD mixed-family listing](https://item.jd.com/product/HITZiatMif0FyxsS8Mng-g.html) | Connector-only discovery from Chinese GA503/幻15 searches; main indexed title selects a used G14 R9-4900/2060, 16+512 GB, 95成新. This is **not a verified G15 offer**. Recommendation prices in its snippet are excluded. No exact G15 product with bound price/stock was established within this budget. |
| G16 AMD | [ASUS GA605 2025 WTB CDN link](https://vangen-cdn-rog.asus.com.cn/laptops/rog-zephyrus/rog-zephyrus-g16-2025-ga605/wtb/) | Connector showed CNY 16,999 and RTX5060. Native attempt failed to a browser error page; indexed amount is a discovery lead only, not a fresh observed product price. |
| G16 Intel | [Suning SKU 12444155294](https://product.suning.com/0000000000/12444155294.html) | Connector title specifies 幻16 Air 2025 GU605CM, U9-285H, 32 GB/1 TB, RTX5060, 2.5K 240 Hz, 日蚀灰. Native navigation reached 用户登录 at 16:30:06 UTC; stopped immediately. No live price/stock extracted. Snippet 门店现货 is conditional store-pickup boilerplate, not selected-store stock. |
| M16 | [ASUS 幻16 星空版/经典版 GU604 WTB](https://rog.asus.com.cn/laptops/rog-zephyrus/rog-zephyrus-m16-2023-series/wtb/) | Connector-only primary discovery names exact GU604 configurations, i9-13900H and 4070/4080/4090 alternatives. No fresh bound price or availability. Do not merge all 幻16 into G16. |
| Duo | [ASUS 冰刃7 双屏 GX650 WTB](https://rog.asus.com.cn/laptops/rog-zephyrus/rog-zephyrus-duo-16-2023-series/wtb/) and [2026 幻16 双屏 GX651 WTB](https://rog.asus.com.cn/laptops/rog-zephyrus/rog-zephyrus-duo-2026/wtb/) | Connector-only primary identities; 2026 snippet showed starting price 39,999, not an exact-variant live price. Fresh dealer GX651 ordering rows are separately recorded above. |
| S17 | [ASUS 冰刃5 Plus / S17](https://rog.asus.com.cn/laptops/rog-zephyrus/2021-rog-zephyrus-s17-series/) | Connector-only primary identity. GX703 Chinese searches also found ZOL comparison/reference pages; their reference/dealer-aggregate prices were not admitted as native product stock offers. |

The successful ASUS G14 reading exposed a concrete hardware caveat: **GA403WW370-0GDHXHBAX20 appears twice in separate columns with different storage/memory details**. One column says 64 GB/2 TB and another says maximum 32 GB/1 TB. Do not resolve that duplicate by choosing the larger capacity. The GA403WP370-0ECHXHB8X20 column separately states Ryzen AI 9 HX 370, RTX5070 8 GB, onboard 32 GB LPDDR5X 7500, 1 TB, OLED 120 Hz and 90 W Turbo GPU wording. This is manufacturer configuration evidence, not stock/price evidence.

## Concrete reusable extractor route

**Public browser extraction proved on the dealer page:** inspect `article script[type="application/ld+json"]`, parse `@graph`, traverse `ItemList.itemListElement[].item`, and isolate Zephyrus rows by exact family/model evidence. Match each selected Product name to the corresponding visible `article .entry-content > div` row using code, RAM/storage, GPU and color; retain source update and schema validity dates. On this capture, 11 rows agree on price and basic configuration. No HTTP-only extractor or production CLI adapter was implemented or tested.

Actionable CLI changes for the root:

1. Support nested ItemList → Product → Offer with **one record per matched row**. Do not use the first price in a multi-product document or conflate seller identity with hardware brand. This source's schema brand is the dealer name.
2. Use a boundary-aware Chinese model matcher. A broad `幻` test also captured two **TUF 天选** entries because their color is **魔幻青**. The retained selection audit rejects those two and keeps only the 11 Zephyrus rows.
3. Split `source_price_claim`, `source_availability_claims`, `condition`, `checkout_verified`, `identity_confidence`, and `comparison_readiness`. Ordering/stock ambiguity and missing TGP must remain visible without erasing the useful priced lead. Condition unknown is not new; “InStock” is not a cart check.
4. Preserve `requested_url` and `final_url`. ASUS product detail → generic homepage is **identity loss**, even if the final document is rich in product prices. Keep the original lead unpriced. Suning → passport is a login gate and terminates that surface.
5. For ASUS WTB, retain the individual `[role="row"]` / `[role="gridcell"]` column topology and exact SKU labels before parsing specs or links. Do not flatten neighboring models into one laptop; retain duplicate-SKU conflicts. Ignore family-level InStock with empty price for priced-deal admission.
6. Treat connector excerpts as discovery provenance with their crawl age. Native browser observation time and seller-declared price validity are separate timestamps. A starting price, reference quote, recommendation or conditional pickup sentence cannot supply an exact variant's price/stock.

## Private evidence and validation

Ignored evidence directory: `.local/deeper-validation/zephyrus/`. `search1.json`–`search4.json` retain connector batches; `g14.json` and `g14Structure.json` retain bounded primary text, schema and column fragments; `shopSnapshot.json`, `g16.json` and `suning.json` retain redirect/error/gate results. `dealerSchema.json` retains observed DOM rows and schema offers; `candidate-claims.json` is a conservative derived export; `manifest.json` hashes the evidence files. Captures are DOM/structured records, **not screenshots**. Public report contains no client IP, cookies or session tokens.

Offline validation checks the 11 dealer row prices against retained DOM text, asserts exact-family selection and CNY, preserves the source stock/ordering conflict, and leaves checkout false and condition unknown. This checks extraction consistency only. No assertion is made about marketplace-wide inventory, best price, merchant trust, or actual fulfillment.

