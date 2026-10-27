# Marketplace search and detail: reuse research

Final implementation choice: the broader [framework assessment](frameworks.md) identified OpenCLI's combined Taobao/JD/Xianyu adapters, which this project selected over the alternatives below. This file preserves the bounded alternative-candidate survey and its source contracts.

Research snapshot: 2026-10-27. All repository links below are pinned to the inspected commit. Contracts and live results are **upstream documentation/source claims**, not tests in this research: no candidate was installed or executed, no marketplace login performed, and no product, shipping quote, rate limit or account permission was verified. GitHub repository metadata and source files were read via unauthenticated GitHub API/raw HTTP. The local code graph was indexed first, but contained only two nodes and excluded `docs`; it offers no meaningful implementation coverage.

## Recommendation

- Prototype a **read-only Goofish adapter around `goofish-cli`**: native CLI with JSON and search/detail; it does not require an AI API for these commands. Pin and review the source and dependencies before installation. Do not expose its publish, delete, message, or cookie-management actions to the comparison flow.
- For **Taobao/Tmall and JD**, evaluate `dsh-shopping-mcp`'s Python adapters and normalized output, conditional on the actual affiliate API permissions. These are affiliate product pools, not evidence of complete marketplace inventory. Keep `mode=mock` separate from live data. JD keyword access is an explicit unresolved blocker for the upstream author's account. Separately evaluate `ali-mcp` for browser-based Taobao/Tmall search/detail; its selector caveat makes it a research prototype, not a proven fallback.
- Prefer one adapter interface returning source, original item ID and URL, title, price and currency, variant, condition, seller, observation time, availability and raw evidence. Keep unknowns as unknown. Compare the *same variant and condition*, distinguish advertised/coupon prices from payable prices, and calculate Brazil landed cost only with separately verified Fansbuy fees, domestic shipping, international freight, FX, taxes and destination assumptions. No source here establishes Fansbuy availability, shipping eligibility or final Brazil cost.

## Concrete candidates

### Goofish CLI — best CLI starting point

[`fancyboi999/goofish-cli` at `5b6b64ca72c54038874d57d61384765ee4e9b2be`](https://github.com/fancyboi999/goofish-cli/tree/5b6b64ca72c54038874d57d61384765ee4e9b2be), Apache-2.0 ([README](https://github.com/fancyboi999/goofish-cli/blob/5b6b64ca72c54038874d57d61384765ee4e9b2be/README.md), [LICENSE](https://github.com/fancyboi999/goofish-cli/blob/5b6b64ca72c54038874d57d61384765ee4e9b2be/LICENSE)). README describes Python CLI + MCP, structured JSON/YAML/table/Markdown/CSV output, browser-driven `search items` and `item view` using Playwright and system Chrome, and `item get` for detail. Representative documented invocations, **not run**:

```sh
goofish auth status
goofish search items '机械键盘' --limit 3
goofish item get 1045171414271 --format json
```

The README also documents a Docker sandbox with `goofish sandbox run search items '机械键盘' --limit 3`, manual login in its isolated browser, and persistent state. QR login and cookie import are described; the human handles verification. Exact search JSON schema, real item coverage, current session behavior and package version matching the pinned source remain to be checked. Although the repository contains AI-facing features, these search/detail paths are described without an AI API key. README states its tool is intended for users' own accounts and includes usage restrictions; inspect [compliance terms](https://github.com/fancyboi999/goofish-cli/blob/5b6b64ca72c54038874d57d61384765ee4e9b2be/docs/compliance.md) and platform terms before use.

### Shopping MCP — official affiliate API adapter

[`EastMG/dsh-shopping-mcp` at `22190059ea1007050e2d0864e9afed3d05bd19c9`](https://github.com/EastMG/dsh-shopping-mcp/tree/22190059ea1007050e2d0864e9afed3d05bd19c9), MIT ([README](https://github.com/EastMG/dsh-shopping-mcp/blob/22190059ea1007050e2d0864e9afed3d05bd19c9/README.md), [server source](https://github.com/EastMG/dsh-shopping-mcp/blob/22190059ea1007050e2d0864e9afed3d05bd19c9/src/shopping_mcp/server.py)). Python 3.11+ MCP server, usable by an MCP client without an AI service. Source declares:

```json
{"name":"search_products","arguments":{"platform":"taobao","keyword":"机械键盘","page":1,"page_size":10,"has_coupon":false,"sort":"default"}}
{"name":"get_product","arguments":{"platform":"jd","item_id":"123456789"}}
```

`platform` is `taobao`, `jd` or `pdd`; search page size documented 1–50, and detail IDs are Taobao `num_iid` or JD `skuId`. Search response is serialized JSON with `ok`, `platform`, `mode`, `note`, `keyword`, `count`, `items`; detail has `item` instead. The source model includes title, item URL, price, original price, coupon, sales, shop and image; upstream warns raw payload is not output by default and normalized rates/amounts must be checked. Crucially the Taobao search adapter notes its returned `item_id` can be an **opaque token**, not numeric `num_iid`: do not assume search ID can always feed `get_product`; verify linkage and retain canonical URL and raw ID ([adapter](https://github.com/EastMG/dsh-shopping-mcp/blob/22190059ea1007050e2d0864e9afed3d05bd19c9/src/shopping_mcp/adapters/taobao.py)).

Unconfigured platforms silently use mock data at `mock.local` according to README; call `shopping_status` and refuse mock records in real comparisons. Upstream reports live Taobao success with its own credentials, but its JD keyword search returned 403 and JD detail only partial; this is its account-specific report, not a universal permission determination ([JD notes](https://github.com/EastMG/dsh-shopping-mcp/blob/22190059ea1007050e2d0864e9afed3d05bd19c9/docs/apply-jd.md)).

The source uses `https://eco.taobao.com/router/rest`, `taobao.tbk.dg.material.optional.upgrade` with `q`, `adzone_id`, `page_no`, `page_size`; detail uses `taobao.tbk.item.info.get`. JD uses `https://api.jd.com/routerjson`, method `jd.union.open.goods.query` with business JSON `{"goodsReqDTO":{"keyword":"机械键盘","pageIndex":1,"pageSize":10}}`; detail uses `jd.union.open.goods.bigfield.query` and `{"goodsReq":{"skuIds":[123456789]}}`. These are **business payloads only**, not complete signed HTTP requests; see [Taobao adapter](https://github.com/EastMG/dsh-shopping-mcp/blob/22190059ea1007050e2d0864e9afed3d05bd19c9/src/shopping_mcp/adapters/taobao.py) and [JD adapter](https://github.com/EastMG/dsh-shopping-mcp/blob/22190059ea1007050e2d0864e9afed3d05bd19c9/src/shopping_mcp/adapters/jd.py) for signing, wrapper and error handling. JD business result may itself be a JSON string; a 200 transport response is not necessarily success. Upstream notes JD bigfield may need `sceneId`, which its current detail payload omits; validate against current authorized documentation.

### Ali MCP — browser Taobao/Tmall and Goofish prototype

[`Tsinglung-Tseng/ali-mcp` at `29d083a80f0b13224ada6831aad125499122990a`](https://github.com/Tsinglung-Tseng/ali-mcp/tree/29d083a80f0b13224ada6831aad125499122990a), MIT ([README](https://github.com/Tsinglung-Tseng/ali-mcp/blob/29d083a80f0b13224ada6831aad125499122990a/README.md), [tool schema](https://github.com/Tsinglung-Tseng/ali-mcp/blob/29d083a80f0b13224ada6831aad125499122990a/mcp_server.go)). Go/Rod browser server exposes MCP at `http://localhost:18070/mcp` and documents:

```json
{"name":"taobao_search","arguments":{"keyword":"机械键盘","limit":10}}
{"name":"taobao_get_item_detail","arguments":{"url":"https://detail.tmall.com/item.htm?id=123456789"}}
{"name":"xianyu_search","arguments":{"keyword":"机械键盘","limit":10}}
{"name":"xianyu_get_item_detail","arguments":{"id_or_url":"123456789"}}
```

The source accepts Taobao/Tmall item URLs; `limit` defaults to 20, with 0 described as all on the current page. README claims guest Goofish search and Taobao SSO into Goofish, but **explicitly says all DOM selectors are initial assumptions requiring real-machine correction**. It also exposes write/destructive operations; restrict the integration to read-only tools. `ALI_COOKIES_DIR` defaults to `./.cookies`, and `ROD_BROWSER_BIN` can select browser binary. No AI API is described as necessary.

### Other Xianyu MCP options

- [`DoLovya/xianyu-mcp-server` at `0c5ab05892370ad01947120ed802a6c225c886e5`](https://github.com/DoLovya/xianyu-mcp-server/tree/0c5ab05892370ad01947120ed802a6c225c886e5) is Python 3.11+, README says GPL-3.0; GitHub metadata reports `NOASSERTION`, so inspect the actual [LICENSE](https://github.com/DoLovya/xianyu-mcp-server/blob/0c5ab05892370ad01947120ed802a6c225c886e5/LICENSE) and dependency/submodule licenses before reuse. [Source](https://github.com/DoLovya/xianyu-mcp-server/blob/0c5ab05892370ad01947120ed802a6c225c886e5/src/xianyu_mcp/server.py) defines `search_items(keyword, page_number=1, rows_per_page=20, sort_field="", sort_value="")`, with documented bounds 1–50, and `get_item_detail(item_id)`; both return serialized JSON or a login-required payload. Example `{"name":"search_items","arguments":{"keyword":"机械键盘","page_number":1,"rows_per_page":20}}`; detail `{"name":"get_item_detail","arguments":{"item_id":"123456789"}}`. README warns real per-account page limits can be stricter. It also exposes write and messaging tools and cookie/QR operations; exclude those from a read-only client. No AI API is required by these declared calls.
- [`babachen/xianyu-mcp` at `44cbaa9630ceb03c89dc6101c7a1cbb60543abfa`](https://github.com/babachen/xianyu-mcp/tree/44cbaa9630ceb03c89dc6101c7a1cbb60543abfa), Apache-2.0: browser automation, `search_items`, plus documented HTTP `GET /api/v1/search?keyword=...&limit=10`; its README tool list does not establish a product-detail tool. Lower priority for a search-and-detail adapter. [README](https://github.com/babachen/xianyu-mcp/blob/44cbaa9630ceb03c89dc6101c7a1cbb60543abfa/README.md).
- [`mercy719/goofish-mcp-server` at `1a4c5817d0896eb7a77fbba665b003cfc9982929`](https://github.com/mercy719/goofish-mcp-server/tree/1a4c5817d0896eb7a77fbba665b003cfc9982929) documents Node/Playwright stdio `search_items` with `{"keyword":"iphone 15 pro","limit":10}` and `get_item_detail` with `{"item_id":"1234567890"}` or `{"url":"https://www.goofish.com/item?id=1234567890"}`; it uses persistent browser profile and in-page mtop. GitHub metadata identifies no license, so do not assume copying or redistribution permission. [README](https://github.com/mercy719/goofish-mcp-server/blob/1a4c5817d0896eb7a77fbba665b003cfc9982929/README.md).

## Agent-Reach and official access boundaries

[`Panniantong/Agent-Reach` at `14c213405669414492bda0f8d52cc6531d062c45`](https://github.com/Panniantong/Agent-Reach/tree/14c213405669414492bda0f8d52cc6531d062c45), MIT, documents `agent-reach channels`, `agent-reach read URL`, and other channel-specific commands. Its [current pinned channel table](https://github.com/Panniantong/Agent-Reach/blob/14c213405669414492bda0f8d52cc6531d062c45/README.md) does **not list Taobao, Tmall, JD or Goofish** as dedicated channels. Generic web read/search is not proof of marketplace search, authenticated product detail or complete results. Useful for general source discovery, not a primary marketplace adapter. Its optional audio transcription explicitly needs Groq/OpenAI, but generic use does not establish an AI API requirement. README describes copying existing Chrome login into a dedicated browser for some platforms; do not copy or log in during this research.

Official entry points: [Taobao Open Platform](https://open.taobao.com/), [Alimama](https://www.alimama.com/), [JD Union](https://union.jd.com/) and [JD Open Platform](https://open.jd.com/). Registration, app credentials, method-specific approval, OAuth/session and affiliate eligibility are documented by the candidate project as prerequisites; exact present-day permissions, quota and eligibility must be verified directly in the logged-in official developer consoles. We did **not** independently retrieve authoritative per-method official documentation or verify numeric quotas; no universal limits or full-catalog access should be inferred from the project's reports. Browser automation is unofficial and may change or require human verification; isolate user-controlled persistent profiles, protect cookies as secrets, avoid logging them, and surface login, verification, blocked and partial-result states rather than treating them as zero matches.
