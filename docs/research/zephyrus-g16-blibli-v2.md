# Zephyrus G16 on Blibli — v2 research

Researched **27 October 2026** (Brazil/East). Scope: five exact supplied listing URLs, public seller descriptions and official coupon rules. This note supersedes the **comparison arithmetic** in [v1](zephyrus-g16-blibli.md), while preserving that earlier evidence. No login, account creation, cart, checkout, purchase, contact or challenge bypass was performed.

## Screenshot update supplied later in the session

The user's two screenshots confirm P1's **Rp25,218,992** and P2's **Rp38,023,030** displayed amounts. Both show a voucher tile reading **Diskon 3% (hemat Rp2.000.000)** and **Min. transaksi Rp4.000.000**. That differs from the minimum on the separately indexed LAPORIN campaign below; **the screenshot does not identify a coupon code or establish that the two campaigns are the same**. The advertised Rp2,000,000 benefit is modeled as a provisional cap, pending the full `Info` terms. A voucher icon is displayed next to the price; whether the listed amount already includes this voucher remains unresolved. No second 3% is deducted.

P2's screenshot explicitly shows **Stoknya lagi habis** (out of stock), with **LAPTOP ONLY** selected and a similar-products button. **Exclude that selected variant from available deals**; retain its amount as reference only. P1 shows buy/cart controls, which do not prove checkout acceptance. The screenshots carry no independently established capture time or URL bar; their model/seller/title evidence is consistent with the supplied listing mapping. They are user-supplied evidence, not a successful CLI fetch. Full source images and a hash/transcription manifest are retained privately, excluded from Git.

The reusable [observations JSON](../../examples/g16-user-observations-2026-10-27.json) preserves these distinctions. [Coupon research rules](../../examples/blibli-coupons-research-2026-10-27.json) keep screenshot and official campaign leads separate and unconfirmed. No account, payment method, quota, stacking or extra-discount entitlement is established.

## Updated comparison: user-observed prices

**All ten numbers in the next table are supplied by the user in this task.** The first is the user's current displayed amount; the second is the user's comparison/struck-through amount. Neither has been independently verified as a current payable offer. Do not interpret the second number as a historical transaction price. Cached sources below are configuration evidence and have older, conflicting prices.

| Listing / exact native ID | User-observed current IDR | User-supplied comparison IDR | BRL reference equivalent of current amount |
| --- | ---: | ---: | ---: |
| [GU603ZU-I745J6G-O][P1] — `ps--MAP-60071-00253` | Rp25,218,992 | Rp25,999,000 | R$7,759.56 |
| [GA605KM-R7N56OL6G-HM, LAPTOP ONLY][P2] — `is--BEO-60066-07913-00001` | Rp38,023,030 | Rp39,199,000 | R$11,699.20 |
| [GU605CM / RTX 5060][P3] — `ps--DWJ-29772-01622` | Rp54,029,000 | Rp58,900,000 | R$16,624.03 |
| [GU605CP / RTX 5070][P4] — `ps--DWJ-29772-01620` | Rp58,189,330 | Rp66,000,000 | R$17,904.11 |
| [GU605 / RTX 5070 Ti][P5] — `ps--DWJ-29772-01621` | Rp55,193,000 | Rp58,900,000 | R$16,982.17 |

Conversions use the **retained ECB XML dated 2026-10-26**, EUR 1 = BRL 6.2523 and IDR 20,320.32: `BRL = IDR × 6.2523 / 20320.32`, rounded once to cents. [Copied dated file](../../.local/access-v2/blibli/ecb-fx-2026-10-26.xml), [original retained file](../../.local/guest-research/ecb-fx.xml), [ECB source URL](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml). This is reuse of the dated file, not a fresh FX fetch. Amounts exclude domestic/international freight, forwarding, spread, payment fees, IOF and import taxes. They are reference conversions, not landed costs or Fansbuy quotes. [Inputs and exact calculations](../../.local/access-v2/blibli/comparison.json).

## What each seller actually claims

These are **seller-written claims from cached first-party listing content**, retrieved through web search on 2026-10-27. Search crawl ages are reported verbatim because exact crawl dates were not supplied. No hardware was inferred from a model code, product family, related product or power-adapter wattage.

| Exact source | CPU | GPU / seller-stated GPU power | RAM / SSD | Display | Cache age reported |
| --- | --- | --- | --- | --- | --- |
| [P1][P1], Macikomp | Core i7-12700H; 2.3–4.7GHz, 14 cores | RTX 4050 Laptop, 6GB GDDR6; **120W**, split 100W + 20W Dynamic Boost | 16GB DDR4 onboard; one DDR4 SO-DIMM slot, seller maximum 48GB / 512GB PCIe 4.0 NVMe M.2, two slots, seller maximum 2TB | 16-inch 1920×1200, IPS-level, 165Hz, 250 nits, 100% sRGB | **2 weeks ago** |
| [P2][P2], KomputerMedan Flagship Store | Ryzen AI 7 350; 2.0–5.0GHz, 8 cores / 16 threads | RTX 5060 Laptop, 8GB; seller writes GDDR6. **TGP not found in retrieved description** | 32GB LPDDR5X onboard / 1TB PCIe 4.0 NVMe M.2; two M.2 slots | 16-inch 2560×1600 OLED, 240Hz, 100% DCI-P3 | **2 weeks ago** |
| [P3][P3], DWI JAYA MAKMUR Flagship Store | Core Ultra 9 285H; 2.9–5.4GHz, 16 cores / 16 threads | RTX 5060 Laptop, 8GB; seller writes GDDR6. **TGP not found in retrieved description** | 32GB LPDDR5X / 1TB PCIe 4.0 NVMe M.2; two slots | 16-inch 2560×1600 OLED, 240Hz, 100% DCI-P3 | **4 months ago** |
| [P4][P4], same named store | Core Ultra 9 285H; 2.9–5.4GHz, 16 cores / 16 threads | RTX 5070 Laptop, 8GB GDDR7; **105W**, split 90W + 15W Dynamic Boost | 32GB LPDDR5X 7467 onboard / 2TB PCIe 4.0 NVMe M.2; two slots | 2560×1600 OLED in description; title says 16-inch / 240Hz | **2 weeks ago** |
| [P5][P5], same named store | Core Ultra 9 285H; 2.9–5.4GHz, 16 cores / 16 threads | RTX 5070 Ti Laptop, 12GB GDDR7; **105W**, split 90W + 15W Dynamic Boost | 32GB LPDDR5X 7467 onboard / 2TB PCIe 4.0 NVMe M.2; two slots | 2560×1600 OLED in description; title says 16-inch / 240Hz | **4 months ago** |

**GU603ZU description matters:** its introductory marketing contains “up to” i9-13900H, RTX 4070 and QHD/240Hz family features. Its specific configuration block instead identifies the i7/4050/16GB/512GB/FHD+165Hz configuration above. The family maxima are not this offer. [Exact listing content retained](../../.local/access-v2/blibli/hardware-targeted.json), [GPU-power extraction](../../.local/access-v2/blibli/gu603zu-description-search.json).

P2's description requires retaining the box for a warranty claim, requests stock confirmation, recommends wooden packing with JNE and refers to separate checkout for packing. Those are seller conditions, not actions taken here. The cache labels this selected variant **LAPTOP ONLY** and **Stok Habis**; this establishes only the cached observation, not present unavailability. Its photo-slide terms were not inspected. [P2 evidence](../../.local/access-v2/blibli/hardware-targeted.json).

The GDDR6 wording for P2/P3 is retained as written and needs exact-SKU validation; it is not silently corrected. The identical 105W claims in P4/P5 are also unverified seller statements, not independently measured limits or performance. P5's retrieved title does not identify a full GU605 model suffix; none is guessed. Flagship-store labels and warranty wording do not independently prove ASUS authorization or warranty service in Brazil. [P3 description](../../.local/access-v2/blibli/listing-page-retrievals.json), [P4/P5 descriptions](../../.local/access-v2/blibli/5070-page-search.json).

## Access result and price freshness

An **owned, separate T3 preview tab**, `tab_m_4cac2679-3846-4860-a3d7-8c794cdb6e4b`, opened P1 and reached **Just a moment...** verification. No control on that challenge was operated. [Snapshot receipt](../../.local/access-v2/blibli/gu603zu-preview.json). Search-service direct opens of P1/P2/P4/P5 returned **403 Forbidden**; P3 returned a cached page. Targeted search queries then exposed the exact first-party descriptions for all five. These are search-cache extractions, not live browser success or independent current-price verification.

Older cached current amounts were P1 Rp25,998,960; P2 Rp39,199,000; P3 Rp43,800,000; P4 Rp59,989,000; P5 Rp56,900,000. P3's older cache has a Rp45,500,000 comparison amount; it does not establish today's Rp58,900,000 comparison. Prior cross-recommendation prices also differ. None replaces the user's newer observations. Source ages: P1/P2/P4 two weeks; P3/P5 four months. A cached stock count or buy button does not establish present stock.

## Coupon claim, apply and eligibility rules

Official indexed Blibli help describes saving a seller voucher with **Simpan**, selecting products from that seller, and applying the saved voucher or entering a code in **Voucher** at checkout. General code instructions cover desktop, mobile web and app. These steps were read only. Saving a voucher does **not** reserve quota: the [saved-voucher FAQ](https://www.blibli.com/faq/voucher/jika-voucher-telah-disimpan-apakah-voucher-bisa-langsung-dipakai/) says quota must remain when used. [Seller-voucher help](https://www.blibli.com/faq/topic/voucher/voucher-toko/) (crawl: last week); [general use](https://www.blibli.com/faq/topic/voucher/penggunaan-voucher/) (today); [retained rules](../../.local/access-v2/blibli/coupon-rules-search.json).

Only **one voucher from one seller** can be used under the [seller-voucher FAQ](https://www.blibli.com/faq/voucher/berapa-jumlah-voucher-toko-yang-dapat-digunakan-pada-saat-pembayaran/) (crawl: two weeks ago). It says seller vouchers can combine with Blibli promotions. The [general-use help](https://www.blibli.com/faq/topic/voucher/penggunaan-voucher/) says ordinary voucher combinations depend on each voucher's terms. Therefore no blanket stacking entitlement follows; the specific offer's exclusions control. Minimum spend, cap, eligible SKU/seller/category, account, payment method, platform, dates and available quota must all match. [Terms lookup help](https://www.blibli.com/faq/topic/voucher/page/2/) (today) points to the actual voucher/email terms; it supplies no universal product-discount threshold.

The following are **official promotional leads, not verified usable coupons for these five offers**:

| Official source / lead | Publicly indexed terms | Material unknowns / treatment |
| --- | --- | --- |
| [LAPORIN / LAPTOP4-2JT](https://www.blibli.com/promosi/kga-laporin) — crawled last week | 3%, **cap Rp2,000,000**, minimum **Rp3,000,000**, selected Intel-processor laptops; stated **1 Oct–31 Dec 2026**; page describes app or website | Introductory copy emphasizes ADVAN/POLYTRON/AXIOO. Exact ASUS SKU/seller participation, payment restrictions, stackability, user quota and available quota not proven. AMD P2 does not meet the stated Intel condition. Direct page open returned 403. |
| Same LAPORIN page: **MEGA-KGA500** | 5%, cap Rp500,000, minimum Rp3,000,000; Mega credit card, full payment or 3/6/12-month installments; until **31 Jan 2027** | Exact five-listing eligibility, remaining quota and stacking unknown. No matching payment capability established. |
| Same LAPORIN page: **PL-KGA12** | 10%, cap Rp1,500,000, minimum Rp1,000,000; Blibli Tiket PayLater powered by Indodana, 12/24-month installments; until **31 Dec 2026** | Financing eligibility, quota, stacking, costs and these SKU bindings unknown. Not a cash-price reduction established here. |
| [BNI / BNIDB-11](https://www.blibli.com/promosi/bank-promo-bni) — crawled two weeks ago | Rp110,000 off, minimum Rp1,500,000; **BNI Mastercard debit, full payment only**; 40 transactions/day, one/card/account/day; app/web/Tukar Tambah; says no combination with other promotions/vouchers | No definite start/end dates recovered; cannot call it currently active. Card eligibility, remaining quota and SKU applicability unknown. |
| [New-member zone](https://www.blibli.com/promosi/zona-member-baru) — crawl two weeks ago; alternate parameterized cache six months ago | Advertises Rp25,000 benefit on selected products; claim stores voucher in the account; qualifying new-member status and a voucher-specific minimum required | Exact code, minimum, cap definition, dates, quota, payment, app requirement, stacking and laptop eligibility unresolved. Copy inconsistently describes cashback/free shopping and reinstalling the app; reinstalling does not prove new-member eligibility. |

[LAPORIN evidence](../../.local/access-v2/blibli/terms-forwarder.json), [bounded eligibility follow-up](../../.local/access-v2/blibli/laporin-terms.json), [BNI terms](../../.local/access-v2/blibli/bni-terms.json), [new-member evidence](../../.local/access-v2/blibli/forwarder-newmember.json), [older parameterized cache](../../.local/access-v2/blibli/promo-pages.json). No specific seller voucher for Macikomp, KomputerMedan or DWI JAYA MAKMUR was verified.

**Do not subtract 3% again.** P5's cached Rp56,900,000 already reflects a displayed 3% listing reduction against Rp58,900,000; it is not evidence of an extra coupon. The supplied Rp55,193,000 is also exactly 97% of that older Rp56,900,000, and supplied P4 Rp58,189,330 is 97% of cached Rp59,989,000. This arithmetic does not identify the mechanism, prove a coupon was applied, or establish eligibility for another 3%. The LAPTOP4-2JT lead could overlap an already displayed adjustment. **No coupon is deducted from any table amount.**

[Official domestic freight help](https://www.blibli.com/faq/?p=59) (crawl: four days ago) describes shipping-voucher caps, not free international forwarding: Rp50,000/150,000/300,000 spend tiers with Rp15,000/25,000/40,000 caps, additional offers including up to Rp40,000 without minimum through **13 Jan 2027**, phone verification, weekly quota reset Monday, and exclusions including seller-shipped/economy/BOPIS. Spend is after product discounts and excludes freight. The multiple schemes require the actual assigned voucher. No domestic or Brazil freight subsidy is assumed.

## Customer account versus Fansbuy/forwarder account

**Whether Fansbuy can buy these Blibli offers, and use this customer's coupon on a distinct purchasing account, remains unknown.** The public [Fansbuy homepage](https://fansbuy.com/) yielded only an image to the search-page extractor; targeted public searches did not establish a Blibli purchase workflow or coupon-transfer policy. This limited result is not proof that the service is unavailable. [Retained access/search](../../.local/access-v2/blibli/forwarder-newmember.json), [follow-up](../../.local/access-v2/blibli/terms-forwarder.json).

Blibli's saved-voucher workflow binds the selection to the purchasing account. A customer's saved/personal/new-member entitlement is not established for a forwarder's separate account. A generally published code might work only if that purchasing account, SKU, payment and quota satisfy its own terms; no such acceptance was tested. These are conditional implications of the cited rules, not a verified Fansbuy capability or a universal prohibition on sharing every code.

[Blibli terms §9](https://www.blibli.com/faq/tentang-blibli/syarat-ketentuan/) (crawl: today) specify one user/account and promo participation limits, identify repeated delivery/payment identities among potential misuse indicators, and allow withdrawal of benefits. Thus a shared forwarder address/payment method can require eligibility review; it does not by itself establish automatic rejection. Do not create alternate accounts to claim new-member benefits. [Retained source](../../.local/access-v2/blibli/terms-forwarder.json). No credentials or accounts were requested or shared.

## Conditional value insight at the supplied prices

- **P5 / 5070 Ti merits verification before P4 / 5070:** Rp2,996,330 less (**5.15%**, about **R$921.93**) for the seller-claimed 12GB versus 8GB GPU memory, with the same claimed CPU/RAM/SSD/display class. Paying more for P4 has no demonstrated benefit in this evidence.
- **P5 is only Rp1,164,000 above P3 / Intel 5060** (**2.15%**, about **R$358.15**), while claiming a higher GPU tier, 12GB rather than 8GB VRAM and 2TB rather than 1TB SSD. If current stock, exact configuration, condition, warranty, seller terms and payable price match, this is the strongest apparent incremental value among those Intel offers.
- **P2 / AMD 5060 is an out-of-stock reference, not an available deal:** Rp16,005,970 below P3 (P3 costs **42.10%** more), with both sellers claiming 32GB/1TB and 2560×1600 OLED 240Hz. This does not establish equal CPU/GPU performance or power.
- **P1 is the budget entry**, but moving to P2 costs Rp12,804,038 (**50.77%**). The screenshot shows P2 out of stock. P1's specific description establishes why it is not configuration-equivalent: 4050 6GB, 16GB/512GB and FHD+ IPS rather than the newer listings' claimed capacities and OLED display.

These are price/configuration comparisons, not measured performance-per-real results or a final purchase recommendation. Current payable prices, inventory, exact ASUS part numbers, condition, Brazil warranty, coupon eligibility, forwarding acceptance and landed cost remain unverified.

[P1]: https://www.blibli.com/p/asus-rog-zephyrus-g16-gu603zu-i745j6g-o-eclipse-gray/ps--MAP-60071-00253
[P2]: https://www.blibli.com/p/laptop-asus-rog-zephyrus-g16-ga605km-r7n56ol6g-hm-rtx-5060-8gb-ryzen-7-ai-350-ram-32gb-ssd-1tb-16-oled-wqxga-240hz-win-11-home-ohs-eclipse-gray/is--BEO-60066-07913-00001
[P3]: https://www.blibli.com/p/asus-rog-zephyrus-g16-oled-gu605cm-ultra-9-285h-rtx5060-8gb-32gb-1tb-w11-ohs-m365b-16-0wqxga-240hz-garansi-resmi/ps--DWJ-29772-01622
[P4]: https://www.blibli.com/p/asus-rog-zephyrus-g16-oled-gu605cp-ultra-9-285h-rtx5070-8gb-32gb-2tb-w11-ohs-m365b-16-0wqxga-240hz-garansi-resmi/ps--DWJ-29772-01620
[P5]: https://www.blibli.com/p/asus-rog-zephyrus-g16-oled-gu605-ultra-9-285h-rtx5070ti-12gb-vram-32gb-2tb-w11-ohs-m365b-16-0wqxga-240hz-garansi-resmi/ps--DWJ-29772-01621
