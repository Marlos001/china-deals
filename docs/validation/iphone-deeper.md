# iPhone 17 Pro Max: deeper public-source validation

Research on **2026-10-27**, following 0.4.0; starting repository HEAD `eafc55fb59173ddd1227bb2933788e97de2c3001`, initially clean. Scope: research only, no application/catalog changes, no commit/push, account, cart, purchase, coupon redemption or seller contact. Primary observations below are freshly rendered public pages, not cached search prices. All observation times are UTC.

## What can be verified without checkout

Two useful **source-claimed 1TB listings** have consistent product descriptions, storage attributes and displayed prices. Public inspection verifies what those pages say and that they display a purchase control; it does **not** verify remaining inventory, authenticity, seller performance, payment eligibility or checkout totals. Neither page exposed a selected SKU ID. These are single-listing configurations, not proof of an interactive SKU selection. No claim of marketplace-wide availability, lowest price or best deal is made.

### Candidate A: orange 1TB, China mainland, ¥7,999

[Goofish item 1096499480089](https://www.goofish.com/item?id=1096499480089&categoryId=0), observed **16:29:23.028Z**. Seller `strong8888`, location Qingdao.

- Main title/description and structured attributes agree on iPhone 17 Pro Max, **1TB, mainland China**; description specifies orange and dual SIM. Displayed price is **CNY 7,999**, with no deposit or monthly-payment qualifier observed.
- Used: description discloses frame impacts and screen scratches; battery health claimed **91%**. Structured condition indicates minor dents/scratches and no repairs. Original condition/no repair is a seller claim, not independently inspected.
- Seller explicitly restricts fulfillment to **pickup in Qingdao Chengyang** and accepts trade-in. This restriction conflicts with the generic free-shipping badge; the reader must retain the conflict and must not promise shipping. Unsuitable for a shipping-dependent buyer without further confirmation.
- Public page displays an immediate-purchase control and offers the unit for sale. **Source-listed availability**, quantity unknown; no sold/deleted notice in the captured main item. No coupon, coupon eligibility, minimum spend or expiry observed. No warranty term observed in the main description.

Private evidence: `.local/deeper-validation/iphone/goofish-1096499480089.json`.

### Candidate B: silver 1TB, China mainland, ¥7,499, repaired screen

[Goofish item 1092800987315](https://www.goofish.com/item?id=1092800987315&categoryId=0), observed **16:29:42.755Z**. Seller `靓机汇啊东`, location Guangzhou; seller's unit reference **7161#**.

- Main description and attributes agree on iPhone 17 Pro Max, **1TB, mainland China**; silver and dual SIM are stated in the description. **CNY 7,499** appears both in the price region and as the seller's wholesale price. Wholesale eligibility/minimum quantity is not specified, so preserve that qualifier.
- Battery health claimed **90%**, cosmetic condition seller-rated 95-new; attributes disclose minor dents/scratches. **Outer screen replacement** is explicitly disclosed; structured repair attribute also says screen repaired. This is a repaired used candidate, not an unrepaired/new equivalent to Candidate A.
- Seller says full payment or installments are possible; ¥7,499 is not described as a deposit/monthly amount. No installment schedule, financing eligibility or fee was observed.
- Pickup available; shipping costs and delivery destination remain unknown. Public purchase control and sale description support **source-listed availability**, quantity unknown. No coupon terms observed. Conditional platform return badge is not an independent device warranty.

Private evidence: `.local/deeper-validation/iphone/goofish-1092800987315.json`.

## Leads that must remain unpriced for an exact 1TB configuration

[Goofish item 1093271890833](https://www.goofish.com/item?id=1093271890833&categoryId=0), observed **16:29:08.593Z**: recommendation card advertised ¥6,699 and a 1TB silver title. The actual main item displays **an activity-price range of ¥6,699–9,399**, covering **17 Pro Max / 17 Pro**, **256GB / 512GB / 1TB**, three colors, and battery health **92–100%**. The seller asks buyers wanting 100% battery to leave a customer-service note. Attributes identify only the Pro Max model, not capacity. No selected SKU was observed. Range endpoints cannot be bound to the title's 1TB unit. Free shipping, original/no-repair claims, and a seven-day quality-problem return with intact seal are seller claims; promotion eligibility/expiry and exact inventory are unknown. Retain as a mixed-variant lead, not a ¥6,699 1TB deal.

[Goofish item 1023378656793](https://www.goofish.com/item?id=1023378656793), refreshed **16:28:38.369Z**: **¥6,999** displayed; title says 1TB, attributes 512GB, description 256GB. Description gives blue ¥6,999, orange ¥7,099, white ¥7,499 and surcharges of ¥1,000 for 512GB / ¥1,800 for 1TB, then requests a quote by capacity/color. Preserve the schedule as text; do not turn arithmetic into an observed selected-variant price. US-unlocked and drilled dual-SIM wording remains alongside new/unopened/no-repair claims. Six-month seller warranty has intact-seal and damage/wear exclusions. No selected SKU, inventory quantity or checkout price was established. No 1TB price winner can be extracted from this page.

Private evidence: `goofish-1093271890833.json`, `goofish-1023378656793.json`, and `goofish-main-structure.json` under the private evidence directory.

## JD and Taobao coverage

Fresh exact [JD link for a silver 1TB, opened-box/self-operated-return listing](https://item.jd.com/product/wUwp2jcFEokrBKat_LGgeg.html) was discovered by connector search. Its indexed title includes `MG094CH/A`; the connector said it was crawled last month. That is a discovery title, not a verified current variant or manufacturer identity.

The one native open first reached a JD verification destination on `cfe.m.jd.com` with title `京东验证`; no interaction/retry occurred. A subsequent passive read at **16:30:10.682Z** found that the page had automatically become the JD login page. No main product price, stock, selected variant or coupon was read. Stop status: **verification/login gate**. Private receipt: `jd-verification.json`. The previously blocked JD `6QDM9CaD9ZAa0SxjEPbKrg` link was not retried.

Taobao/Tmall discovery used exact product-route queries and a separate domain-filtered Chinese query. The bounded results supplied no usable exact target handset link; returned home/shop/general pages are not product evidence. No native Taobao product was opened, no access-gate claim is made for Taobao, and this says nothing about its actual inventory. JD search excerpts also mixed recommendation prices and other capacities/models; those amounts were not attributed to the linked main products.

## Concrete reader improvements for root

The rendered Goofish DOM provides enough evidence for a **browser-backed, exact-listing reader**, including useful source-listed candidates. It does not provide evidence that raw HTTP HTML alone or an embedded product JSON reader will work.

1. Bind each capture to requested and final numeric `id`, final URL, page title and UTC capture time. Require one loaded main item. A `loading:false` navigation receipt initially had a generic title on fresh Goofish pages, so it is insufficient as a product-ready signal. Wait boundedly for the main item, a deleted state or a gate; do not retry a gate.
2. Restrict extraction to `[class^="item-main-container--"]`, then `[class^="item-main-info--"]`. Across these four retained pages, this main container **excludes recommendations**. Treat CSS prefixes as observed implementation details, not a guaranteed API. Fail to an unpriced lead if cardinality/structure changes. Main outerHTML was fully retained: 32,792 / 24,262 / 31,380 / 29,478 characters, all below the 35,000-character capture bound.
3. Price: scope `[class^="price--"]` to main info. Preserve the literal string before normalization, including `6699 - 9399`. Do not collapse ranges to minima; retain activity-price wording separately without inventing coupon terms.
4. Description: inside main info, scope to `[class^="notLoginContainer--"] [class^="main--"]`. **Do not use the first `[class^="desc--"]`**: on the silver listing that matched the platform's return-policy copy instead of the product description. Retain structured attributes separately from prose.
5. Attributes: read children of `[class^="labels--"]`; split each label/value at the colon and remove presentation whitespace from the label only. The DOM renders storage/repair labels as separate characters and lines. Preserve value text, repair negation and exact unit. Parse title, prose and attributes independently before reconciling.
6. Configuration binding: the two single 1TB listings have consistent prose and attribute evidence; keep `configuration_binding=single_listing_consistent`, `selected_sku_id=null`. The range listing is mixed-model/mixed-capacity and the older listing has capacity conflict. Neither should gain an exact SKU price from its title or recommendation card.
7. Availability: retain `availability_evidence=public_listing_with_purchase_control` and `stock_quantity=null`; no checkout required to show this useful evidence. A visible purchase control supports listing status, **not verified stock**. Preserve explicit sold/deleted/out-of-stock states when present. Distinguish the source claim, binding quality and checkout status instead of dropping all publicly readable candidates.
8. Fulfillment and condition are first-class filters: pickup-only Qingdao overrides any assumption from the generic free-shipping badge; repaired screen and wholesale qualifier must survive normalization. Financing availability does not by itself make a separately stated full price a deposit.
9. Embedded-data result: inspected inline JSON/JSON-LD script candidates and the public `window.__ICE_APP_CONTEXT__`. The observed context has `appData:null`, empty item/layout `pageConfig`, `/item`, and `renderMode:CSR`; no product or selected-SKU payload was exposed there. Do not invent an internal API/signature/session flow. Recommendation anchors can supply discovery URLs only; open each separately before using its price.

An **offline research probe**, `.local/deeper-validation/iphone/extract_retained.py`, reads only the four saved main DOM fragments with Python's standard-library HTML parser. `extracted-primary.json` contains the independently isolated price, description, attributes, shipping badge and purchase control. This demonstrates selector feasibility on retained observations; it is not an application patch, live CLI success, production selector guarantee or checkout test. No codebase symbol discovery was needed because this task did not inspect or edit application implementation.

## Budget, provenance and handoff

- **7 connector search queries**, retained in `search-01.json` (3), `search-02.json` (3), `search-03.json` (1). Chinese domestic-market terms were used. Cached crawl recency is separate from fresh browser observation timestamps.
- **5 native product opens**: four Goofish items (one explicitly authorized refresh plus three fresh recommendation-linked listings) and one fresh JD link. Deleted Goofish item `1087872356879` was not revisited. Product-open cap reached; no more navigation/search was needed for the shortlist.
- Called T3 `preview_status`, created one owned incognito/background tab, used its exact ID on all calls, then closed it successfully. No CAPTCHA operation, identity rotation, proxy change, account/cart/message, hidden API call or manual session fabrication. JD's gate was not retried.
- Evidence is DOM/tool-output evidence, **not screenshots**. Main-item captures exclude recommendation content; the known-page discovery receipt keeps card links in a separate field. Private raw receipts stay under `.local/deeper-validation/iphone/`; public report contains no client IP or challenge reference token.
- A local optional BeautifulSoup probe failed because `bs4` was absent; nothing was installed. The retained-DOM probe uses the standard library. No network-bearing CLI search or application tests were run, and no claim is made that 0.4.0 itself extracted these offers.
- Only this report and the private owned directory were written. Root owns catalog/schema/reader integration. Next useful implementation step is explicit browser-capture ingestion with configuration/availability provenance, followed by offline replay of these two consistent listings and the two ambiguous controls.
