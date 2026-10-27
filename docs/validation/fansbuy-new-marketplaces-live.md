# New marketplace public parser — 2026-10-27

Tmall, 1688 and Weidian have a conservative **metadata-only parser**, now including the native Weidian state observed in root's retained first-party HTML. Offline replay of that exact body returns item `7287460067`, literal title `BALENCIAGA SIZE:S-XL  ` (two trailing spaces), and **delisted** availability. Every price remains unpriced. Root performed the one native guest GET; this follow-up performed **zero network/browser/Fansbuy requests**.

The first worker's DuckDuckGo query encountered a challenge and stopped. Root subsequently found the exact Weidian URL through an independent public connector index, without retrying DuckDuckGo. The original retained result records a successful transport attempt followed by the previous parser's `item_schema_unverified`; its numeric HTTP status was not separately retained. That historical receipt remains unchanged. The worker validation below is an **offline replay**. Root subsequently completed one separately instrumented post-integration GET; its numeric HTTP 200 and parsed result are recorded below.

## Public API and integration handoff

```python
from china_deals.china_public import parse_product_page

row = parse_product_page(body, marketplace, requested_url, observed_at)
```

- `body`: complete decoded HTML text, at most 2 MiB when encoded as UTF-8; decoding replacement characters fail closed.
- `marketplace`: exact `tmall`, `1688` or `weidian` key. Existing markets and alias resolution remain caller-owned.
- `requested_url`: exact HTTPS native product route, validated by the real `marketplaces.canonical_product_url` and `product_id` helpers. Tracking is removed only after route/identity validation.
- `observed_at`: caller-supplied timezone-aware ISO timestamp; retained unchanged, with no current-time fallback.
- Returns **one raw dictionary**, compatible with `models.normalize_offer`, or raises `ValueError`. The caller can place it in its `items` list. This parser performs no HTTP requests, browser actions or normalization itself.

The row includes `marketplace`, `item_id`, `title`, `description`, `url`, `nativeURL`, `observed_at`, `price=None`, `currency="CNY"`, `price_basis="source_observation_unverified"`, `source_mode="guest_product_page"`, availability, unknown condition, ranking exclusions and source warnings. There is deliberately no top-level `offers` or selected variant. `CNY` is the marketplace currency contract; it does not override published currencies retained under `source_detail`.

**Raw-shape additions for root integration:** the API signature is unchanged. Generic metadata still has `availability="unknown"`. Native Weidian state can return `delisted`, `unavailable` or `unknown`, never availability inferred from stock. `source_detail.provenance.kind="weidian_native_state"` adds `script_id`, `state_path="result.default_model.item_info"`, and optional `inert_companion_src`. `source_detail.native_state_claims` contains bounded, allowlisted `item_info` and `sku_properties`; the generic `product_claims={}` and `offer_claims=[]` remain present. Native `item_name` whitespace is preserved in the raw title; existing normalization strips outer whitespace. The source claims preserve the literal title. No changes to root's capture or integration files are included.

`source_detail` contains the exact canonical identity, selected source kind/script index, bounded Product/Offer/page metadata claims, explicit truncation paths and SHA-256 of the supplied HTML re-encoded as UTF-8. This digest is **not an HTTP response-byte digest**. Auxiliary evidence is limited to 32 KiB in ASCII JSON; identity and title are never truncated to make a match. Product names over 1,000 characters, descriptions over 8,000 characters and evidence beyond limits are rejected.

Root owns guest/browser/adapters integration. Acquisition must verify final URL against the request, HTTP/access status and complete transport before invoking this parser. Native state binds its primary item ID to the acquisition-verified URL passed as `requested_url`; the unchanged signature cannot independently observe redirects. Retain the transport or DOM receipt separately, translate `ValueError` to the existing unavailable/unverified result, and continue enforcing the shared host gate. The parser reuses the existing guest HTML challenge guard but does not replace acquisition checks or prove guest session state.

## Admission and price boundaries

Accepted generic identity sources are a unique exact-URL-bound JSON-LD Product, including document `@graph` or a bound WebPage's `mainEntity`, or head-only Open Graph product metadata with an exact canonical/`og:url`. A title, `productID` alone, an Offer URL, arbitrary application-state JSON, recommendations, or a search page cannot establish the product. Any supplied canonical/`og:url` must agree with the request. A bound Product's explicit `productID`, `url` and `@id` must agree; a variant `sku` is retained as a source claim and never treated as a selected item ID.

The sole native exception is one closed body-context `<script id="__rocker-render-inject__" data-obj="…">` with HTML-escaped JSON, successful integer `status.code=0`, and the fixed `result.default_model.item_info` path. Its exact string/integer `item_id` must match the URL without truncation/coercing floats or booleans. A matching sibling or recommendation never rescues the wrong/missing primary item. Multiple carriers or a simultaneous matching JSON-LD Product fail closed. Inline state is limited to 256 KiB UTF-8, raw carrier attributes to 512 KiB, the JSON tree to 4,096 nodes and depth 32. Duplicate JSON keys anywhere, malformed/truncated JSON, overflow/non-finite values, duplicate/unquoted/malformed attributes, nonempty script bodies, self-closing/unclosed scripts and ignored HTML contexts fail closed.

**Observed companion src exception:** the exact retained script has `crossorigin="anonymous"` and `src="//s.geilicdn.com/node/itemServerMixed/index/index.7da280e4305531c98caa.js"` as well as inline `data-obj`. This was independently rechecked against body hash `0367cba1af0721711cc73263bc755c6ab91386e0e74735268e5522656897fa8b`. `crossorigin` alone does not imply an external source. The parser accepts no src or this exact observed companion string only, retaining it as inert provenance. It never fetches or executes that URL. Src-only carriers, empty/boolean/different/duplicate src attributes are rejected. A future changed companion URL requires new source evidence; there is no permissive host/prefix fallback.

Literal `is_status_off_shelve=true`, `is_status_deleted=true` or the observed `商品已下架` buy-limit text produce `availability="delisted"`. Otherwise `is_valid_item=false` or `itemSellable=false` produces `unavailable`; all other native states remain `unknown`. Positive stock, a displayed SKU name or SKU prices cannot revive availability or establish a selected variant. Root's retained item has invalid/off-shelf flags, delisting text and stock 8,000; the resulting delisted state survives normalization and re-normalization. Source prices `origin_price="240"`, `itemLowPrice=24000`, and eight SKU price/stock records remain literal, bounded claims, with no unit/currency conversion or numeric price exposure.

All JSON-LD scripts are inspected. Duplicate keys, malformed later scripts, non-finite numbers, multiple matching Products, open/truncated scripts/documents and conflicting metadata fail closed. Unrelated products do not contribute price claims. Nested recommendation/variant trees are not recursively searched for an offer.

**Every price remains unpriced**, including an apparently simple CNY Offer. There is no evidence-backed contract for selected variant, single unit, wholesale quantity, deposit/installment scope, price currency or checkout total. Aggregate ranges/minima, conflicting currencies, unbound offers, page prices and availability are retained only as bounded claims. These values never enter top-level `offers` or `price`, including after normalization and re-normalization. This generic schema support is a local contract, not proof that these marketplaces currently publish it.

## Live discovery and access ledger

Original scoped worker budget: at most six queries and one exact product read for each of Tmall, 1688 and Weidian. That worker used **one query; zero exact product reads**. Root later supplied **one native Weidian GET** after independent connector-index discovery; this follow-up used **zero additional requests**. No Fansbuy host or asset was fetched by this worker; the existing Fansbuy HTTP 403 gate remained in force. DuckDuckGo was not retried.

T3 preview was available after opening a valid HTTPS URL. Two earlier `about:blank` open attempts returned `Preview automation open failed: Invalid preview URL (parse: https:; input length 11).` They did not navigate to an external source. No alternate browser system was used.

At `2026-10-27T18:55:04.607Z`, the first query was:

```text
site:detail.tmall.com/item.htm 索尼 WH1000XM6
```

Native search URL: <https://html.duckduckgo.com/html/?q=site%3Adetail.tmall.com%2Fitem.htm%20%E7%B4%A2%E5%B0%BC%20WH1000XM6>.

The T3 network snapshot reports **HTTP 202** and the visible page says:

> Unfortunately, bots use DuckDuckGo too.
> Please complete the following challenge to confirm this search was made by a human.

The host was gated immediately. No CAPTCHA interaction, subsequent query, HTTP fallback, alternate search access, login, cart, order, proxy or bypass followed. The browser automatically loaded page resources during navigation; these are recorded in the private snapshot and are not additional researcher queries. The tab used T3's default profile; no account operation occurred, and cookie-free/session identity was not independently established.

The rendered DOM was read without navigation at `2026-10-27T18:55:26.708Z`. Retained DOM is a browser serialization, not raw HTTP bytes or a screenshot. The snapshot contains the observed main-document status/timestamp; an HTTP body hash is unavailable. The DOM and receipt hashes are recorded in the private manifest.

The original discovery worker obtained no exact product URLs. Root later obtained <https://weidian.com/item.html?itemID=7287460067> independently. Its native guest read began at `2026-10-27T19:02:56.958898+00:00` and completed at `2026-10-27T19:02:59.538298+00:00`, with the same requested/final URL. The retained decoded HTML contains 43,514 UTF-8 bytes and hashes to `0367cba1af0721711cc73263bc755c6ab91386e0e74735268e5522656897fa8b`. This is decoded-text evidence, not an original compressed HTTP-byte digest. The listing is source-marked delisted; its stock field is not purchasable inventory evidence. Tmall/1688 native access and all comparable current prices remain unknown. The unexecuted Chinese query leads `Steam Deck OLED 掌机` and `AMD 锐龙 9800X3D` are historical suggestions, not completed queries or authorization for more requests. Do not construct live links from synthetic fixture IDs.

## Local evidence and validation

Private receipts: `.local/fansbuy-expansion/new-marketplaces/`.

- `01-discovery-snapshot.json`: T3 snapshot, visible challenge and network status/timestamp.
- `01-discovery-dom-result.json` and `01-discovery.dom.html`: retained T3 result and exact extracted DOM serialization.
- `access-ledger.json`: budget, host gates and unknown live-product status.
- `sha256-manifest.json`: retained artifact hashes.
- `focused-tests.log`: focused test output.

Root-owned originals, read only: `.local/fansbuy-expansion/root-live/weidian-decoded.html`, `weidian-provenance.json`, and `weidian-result.json`. Their hashes were compared before/after replay; none was overwritten. The original result remains `unavailable/item_schema_unverified`, recording the old parser failure.

New private follow-up evidence: `.local/fansbuy-expansion/weidian-state-followup/actual-body-offline-result.json` contains the exact-body successful raw row, normalized row, re-normalized price, parser hash and unchanged root receipt hashes. `focused-tests.log` contains the scoped suite; `root-receipts-before.json` and `unowned-before.json` preserve the starting receipt/WIP hashes. No raw live body was added to public fixtures.

`tests/fixtures/china-public-synthetic.json` remains explicitly **synthetic**. The new `tests/fixtures/china-public-weidian-retained.json` is explicitly **derived from retained first-party HTML**, with body hash/size, exact source URL, observation timestamp and sanitization notes. It retains the actual status/item/SKU structure and values while omitting unrelated shop/user/promotion/recommendation data and image URLs. It is not the full live body and its replay is not fresh HTTP evidence. Tests use the actual marketplace URL helpers and normalization, with no helper patches. Existing generic coverage remains intact; native tests add delisting versus stock, SKU claims without selection, wrong primary versus matching sibling IDs, carrier context/attributes, pinned inert src, duplicates, malformed/truncated/oversized JSON, numeric overflow, availability types and normalization round trips.

Command: `python -m unittest tests.test_china_public -v` — **30 tests passed** (17 original, 13 native follow-up). Separate offline replay of the **actual retained body**, not only the sanitized fixture, also passed and produced 3,251 ASCII JSON characters of bounded source detail. CI's full-suite command is left to root after integration. The earlier Ruff attempt found no installed module/executable; no lint success is claimed.

Owned changes are only `china_deals/china_public.py`, `tests/test_china_public.py`, `tests/fixtures/china-public*.json`, this document and the private evidence directory. Other workers' WIP was preserved. No commit or push was made. This handoff covers the scoped parser/validation work and iteration-2 native-state follow-up; root owns integration and broader validation. No additional network/browser/Fansbuy request is needed for this handoff.

## Root post-integration transport check

A separate bounded, cookie-free native GET began at `2026-10-27T19:15:23.757314+00:00` and completed at `19:15:26.318262+00:00`. The numeric status was **HTTP 200**, with server date `Tue, 27 Oct 2026 19:15:25 GMT`; requested and final URL both identify item `7287460067`. Its decoded HTML is **43,514 UTF-8 bytes**, SHA-256 `0367cba1af0721711cc73263bc755c6ab91386e0e74735268e5522656897fa8b`, matching the original retained decoded body. The integrated guest reader returned the exact title, **delisted**, and **price null**. This is a transport/parser canary for a clothing listing, not a purchasable electronics deal or authenticity assessment.

Root-owned receipts: `.local/fansbuy-expansion/root-live/weidian-postintegration-{provenance,result}.json` and `weidian-postintegration-decoded.html`. In total root made two native reads, one before and one after integration. Worker offline replay performed no additional request. No successful native Tmall/1688 read or selected-variant price is established. These timestamps are historical observations, not a promise of current access.
