# Fansbuy marketplace inventory — 2026-10-27

**The observed union of explicitly named marketplaces is five: Taobao, Tmall, 1688, Weidian, and JD.** This is a source-backed minimum from two cached official Fansbuy pages, **not an exhaustive platform list, a live integration test, or proof that every product can be purchased/shipped**. The relevant copy uses “like” and “including”; neither source declares a closed enumeration. No additional platform is admitted through generic manual-buy copy, logos, social links, or another agent's claims.

Research-only handoff against the initially clean `b7c3c9b` checkout. Owned outputs: this document and `.local/fansbuy-expansion/inventory/`. No application/test changes, accounts, authentication, carts, orders, purchases, uploads, proxies, bypasses, commits, or pushes were performed by this researcher.

## Named platform inventory and capability boundaries

“Named” below means explicitly advertised in the cited first-party copy. “Not established” means the reviewed evidence does not establish that capability; it does **not** mean unsupported.

| Platform | Fansbuy keyword/catalog recommendations | Native product-link input in guide | Named procurement advertising | Source |
| --- | --- | --- | --- | --- |
| Taobao | Named | Named | Named | S05, S06 |
| Tmall | Named | Not established separately | Not named in S06; guide supports product selection | S05 |
| 1688 | Named | Named | Named | S05, S06 |
| Weidian | Not established | Named | Named | S05, S06 |
| JD / JD.com | Not established | Not established | Named | S06 |

Counts, with overlaps deliberately preserved:

- Explicit keyword/recommendation platforms: **3** — Taobao, Tmall, 1688.
- Explicit native-link examples: **3** — Taobao, 1688, Weidian.
- Explicit procurement-advertising platforms: **4** — Taobao, 1688, JD, Weidian.
- Deduplicated union: **5**. Verified live marketplace searches, product extractions, or purchases in this research: **0**.

The guide describes a purchase-request workflow after product selection. That supports the advertised intent of the selection paths; it does not independently verify stock, variants, automated SKU extraction, account-free access, fulfillment, or backend coverage. In particular, JD's procurement mention must not become a claim of native Fansbuy JD keyword search. These Fansbuy capabilities also do not prove this CLI has working adapters for those platforms.

## Literal first-party evidence

### S05 — official Beginner Guide, cached extraction

Native URL: <https://fansbuy.com/beginnerGuide>. Parent's connector search on **2026-10-27** reported **“Crawled: last week”**; an exact crawl/retrieval timestamp was not supplied. This researcher inspected the retained extraction at `2026-10-27T18:52:41.887444+00:00`. The URL was **not reopened** after the access gate.

The link-input instructions name **“platforms like Taobao, 1688, or Weidian”**. The separate keyword method names **“recommended Taobao, Tmall, and 1688 products”**. Manual **“fill&buy”** uses customer-supplied product/order details rather than establishing another native marketplace integration.

Exact retained excerpts and their hashes remain in the private inventory. These methods add no further named marketplaces.

### S06 — official mobile homepage copy exposed on a promo route, cached extraction

Native URL: <https://m.fansbuy.com/user/promo>. Parent's connector search on **2026-10-27** reported **“Crawled: 2 weeks ago”**; an exact crawl/retrieval timestamp was not supplied. This researcher inspected the retained extraction at `2026-10-27T18:52:41.887362+00:00`. The URL was **not reopened**. Only the platform procurement excerpt is used; no coupon, promotion, or eligibility claim is used.

Under “Full-Platform Procurement”:

> Complete access to all product categories across leading platforms including Taobao, 1688, JD, and Weidian

This is Fansbuy's advertising claim, not independently validated category coverage. “Including” makes it non-exhaustive. It supplies the JD name missing from S05's two explicit selection lists.

## Native domains, aliases, and route examples

The following are conventional marketplace identity/URL-format references for implementation planning. **The Fansbuy excerpts above name platforms, not these domain allowlists. These formats were not independently fetched or validated in this research**, and placeholder URLs are not live product evidence. Keep provenance for domain recognition separate from Fansbuy-support evidence. Avoid wildcard host acceptance or treating every route on a recognized host as a product page.

| Inventory key | Names / aliases | Canonical host reference | Conventional product route template |
| --- | --- | --- | --- |
| `taobao` | Taobao, 淘宝 | `taobao.com`; product host `item.taobao.com` | `https://item.taobao.com/item.htm?id=<item_id>` |
| `tmall` | Tmall, 天猫 | `tmall.com`; product host `detail.tmall.com` | `https://detail.tmall.com/item.htm?id=<item_id>` |
| `1688` | 1688, 阿里巴巴1688 | `1688.com`; product host `detail.1688.com` | `https://detail.1688.com/offer/<offer_id>.html` |
| `weidian` | Weidian, 微店 | `weidian.com` | `https://weidian.com/item.html?itemID=<item_id>` |
| `jd` | JD, JD.com, Jingdong, 京东 | `jd.com`; product host `item.jd.com` | `https://item.jd.com/<sku_id>.html` |

Alias boundaries:

- Tmall remains a separate named platform in this inventory even where item IDs or infrastructure resemble Taobao. A Taobao short URL alone does not identify the destination platform.
- 1688 does not mean every Alibaba service, Alibaba.com, or AliExpress.
- Weidian is not an alias for WeChat/Weixin or every WeChat mini-program.
- Xianyu / Goofish / 闲鱼 is a separate marketplace identity, not a support implication of the Taobao name or a legacy Taobao-hosted URL. It is **not named by S05/S06**; the repo's existing Goofish support is a separate fact.
- Social/app names such as Douyin/TikTok, Xiaohongshu/RED/RedNote, WeChat, WhatsApp, and Discord must not become marketplace entries merely because they appear in a footer, sharing feature, app link, or customer-service workflow. These sources establish no additional platform-specific procurement capability for them.
- Pinduoduo, Dewu/Poizon, AliExpress, Alibaba.com, and Blibli are also **not established by these excerpts**. This is an evidence limit, not a declaration of rejection by Fansbuy.

## Static frontend evidence and the generic/manual distinction

S04 is a previously retained local `/tmp/fansbuy_index.js`, copied unchanged into the private inventory. Its original network retrieval receipt is unavailable. Its file mtime is `2026-10-27T13:24:15.033144+00:00`, **not a proven retrieval time**. A prior local research draft associates the index asset with <https://fansbuy.com/assets/js/index.Do6R0FaM.js>, and S01 currently imports that URL, but the copy is not cryptographically bound to the current origin response. Treat these findings as supplemental static evidence, not current live verification.

The retained code contains:

- Short-link dispatch checks for literal `https://e.tb.cn/`, `https://m.tb.cn`, and `https://qr.1688.com`, passed to `/web/taobaoOrder`. This is code-path evidence only; redirects, destination identity, and service success were not tested. Its substring checks are not a safe canonical-domain policy to copy.
- Generic HTTP(S) input sent to `/web/promote/getPromoteUrl`; an `/expertbuy?` response can lead to `/fillbuy?fillUrl=...`.
- Non-URL input routed to `/productlist?keyWork=...`; the route alone says nothing about the backend's complete platform set.
- Separate navigation to `/fillbuy` (manual ordering) and `/forwarding` (transfer-order label). Forwarding is a distinct service, **not evidence that Fansbuy can search or purchase on every origin website**.

No endpoint above was invoked by this researcher. Generic URL acceptance is not a successful product conversion. A manual form is not a native catalog integration. International forwarding is not proof of an Indonesia-to-China leg or any other origin route.

## Three research passes and access ledger

1. **Fresh first-party surface and gate audit.** S01 `https://fansbuy.com/` returned HTTP 200 at `2026-10-27T18:49:43.372886+00:00`, exposing the SPA imports but no enumerated marketplace copy. S02, the linked `index.Do6R0FaM.js`, returned **HTTP 403**. S03, the concurrently launched `en.BzTs3T_3.js`, has **unknown HTTP outcome** because the first future raised before its result was inspected. No response bodies or exact request timestamps were retained for S02/S03. Neither was retried. All further Fansbuy-host requests stopped; no browser fallback, alternate host, proxy, or bypass was used.
2. **Retained frontend and source-quality audit.** Recovered S04, retained exact bytes/hash and byte-offset excerpts, separated search/URL/manual/forwarding paths. The earlier Gemini draft's five-platform table was rejected as primary proof because it had no source-bound excerpt; it is not a source for the final count.
3. **Cached official-page reconciliation and completeness audit.** Root supplied already-retained connector results for S05/S06. Exact first-party excerpts establish the five-name union and the distinct 3/3/4 capability subsets. Audited aliases, app/service ambiguity, retrieval provenance, and non-exhaustive wording without further network requests.

These are **three research iterations**, not three application implementation/review cycles. New external HTTP source URLs attempted by this researcher: **3**. Additional cached official page URLs used: **2**. S04's candidate asset URL duplicates S02. Thus **5 distinct native URLs** underlie this report, below the ten-source bound; no unselected result in the parent's larger search response is used as support evidence. No FAQ, complete public backend configuration, or exhaustive allowlist was obtained.

## Evidence receipts and handoff

Private evidence lives under `.local/fansbuy-expansion/inventory/` (ignored by Git):

- `01-home.html` and `01-home.meta.json`: origin bytes, native/final URL, exact retrieval time, HTTP headers, and SHA-256.
- `request-log.json`: attempted URLs and the confirmed/unknown outcome distinction.
- `04-prior-index.js`, `04-prior-index.meta.json`, `04-excerpts.json`: recovered bytes, prior-path/mtime caveats, SHA-256, exact excerpts and byte offsets.
- `05-06-official-cached-excerpts.json`: selected native URLs, relative crawl labels, inspection timestamps, exact excerpts, excerpt SHA-256 values, and SHA-256 of the root-owned full connector response.
- `inventory.json`: five-platform machine-readable evidence classification and completeness flags.
- `sha256-manifest.json`: hashes for the retained inventory artifacts.

The parent-owned connector response is `.local/fansbuy-expansion/root-discovery/official-index-response.json`; its SHA-256 at inspection is `946bfff3a1c9f6a955912829cc0cd77f451797857132170c09f8df991b4ef42d`. The private excerpt receipt binds to those exact retained bytes. Search cache age remains a material limit even when the originating page is first-party.

Implementation may use these five as the **observed, explicitly named Fansbuy platform scope**, while exposing the differing evidence levels. It cannot truthfully label this inventory “every Fansbuy-supported marketplace” without a complete authoritative enumeration. Additional platforms and live integration status remain unknown; no manual-buy fallback or generic “buy anywhere” sentence closes that gap.
