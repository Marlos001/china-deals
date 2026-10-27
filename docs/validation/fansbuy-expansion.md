# Fansbuy marketplace expansion — 27 October 2026

This update adds separate **Tmall, 1688 and Weidian** paths. Together with existing Taobao and JD, the CLI now covers the five marketplaces explicitly named by the retained official Fansbuy guide/procurement copy. Existing Goofish and Blibli remain available, giving seven marketplace keys. The official wording is inclusive and cached; **this does not certify every platform that Fansbuy might accept through manual fill-and-buy**.

[Primary source inventory](../research/fansbuy-marketplaces-2026-10-27.md) distinguishes guide keyword recommendations, guide link examples and procurement advertising. They are different claims. No account, checkout, procurement, shipping eligibility or current price is established by a platform name.

## Capability matrix

| Marketplace | Guest search | Guest detail evidence | Numeric price boundary | Optional native adapter |
| --- | --- | --- | --- | --- |
| Taobao | Bounded index discovery | No validated guest item schema; existing catalog observation is separate | Index/catalog amounts unranked | Existing pinned OpenCLI path |
| Tmall | Bounded index discovery | Identity-bound public metadata; HTTP/browser/capture | No selected-variant price contract; unpriced | Explicit unavailable receipt |
| 1688 | Bounded index discovery | Identity-bound public metadata; HTTP/browser/capture | Quantity/wholesale/variant amounts unpriced | Explicit unavailable receipt |
| Weidian | Bounded index discovery | Identity-bound public metadata and retained native server-state shape; HTTP/browser/capture | No selected-variant price contract; unpriced | Explicit unavailable receipt |
| JD | Bounded index discovery | Existing bound public JSON | Missing/masked/unbound price remains unknown | Existing pinned OpenCLI path |
| Goofish | Bounded index discovery | Existing bounded primary DOM/browser capture | Consistent primary-item contract only | Existing pinned OpenCLI path |
| Blibli | Public API then bounded index discovery | Existing selected product-state/schema reader | Exact selected-item contract only | Existing optional adapter/browser path |

Every search may still be blocked or empty. Metadata parser fixtures do not establish that a particular live page publishes that schema. Existing native paths are implementations, not proof of an authenticated bridge or unblocked source. No native filter parameters were invented for the new markets. Literal local term filters remain separate from product relevance.

All seven keys participate in the existing configuration, rank, product intent, freshness, refresh/history, promotion evidence, coupon scenario and Brazil comparison workflows. The new China markets use CNY and the configurable Fansbuy freight policy. That policy is an estimate workflow, not procurement/carrier/import clearance. Blibli remains IDR/Indonesia with freight excluded by default. Old preferences merge additively; old marketplace/history keys remain unchanged.

## Inspect and use

```sh
china-deals marketplaces
china-deals schema
china-deals plan 'Sony WH-1000XM6'
china-deals search 'Sony WH-1000XM6' --markets fansbuy \
  --zh-query '索尼 WH-1000XM6 头戴式耳机' --currency native --include-offers
china-deals filters 1688 '索尼 耳机' --max-price 2000
```

`fansbuy` expands Taobao/Tmall/1688/Weidian/JD; `all` expands all seven keys. Aliases such as `1688.com`, `alibaba1688`, `tmall.com` and `weidian.com` resolve to canonical keys. 1688 is not Alibaba.com or AliExpress; Weidian is not a generic WeChat storefront.

New exact routes are `detail.tmall.com/item.htm?id=ID`, `detail.1688.com/offer/ID.html` and `weidian.com/item.html?itemID=ID`, using HTTPS and exact native authorities. Conflicting/duplicate/blank identity parameters, unsafe authorities and unsupported routes are rejected before acquisition. Legacy Taobao rows may retain Tmall URLs, so separate searches can overlap; counts are observations, not inventory totals.

Browser imports use `china_deals.china_capture.CAPTURE_JS` and `detail MARKET URL --from-browser-json FILE`. The complete `{url,capturedAt,html,htmlBytes,htmlTruncated}` envelope must bind the same item and preserve an aware timestamp and exact UTF-8 byte count. Imports perform no network or implicit FX request; a local snapshot may convert eligible amounts. Raw HTML is not returned. Capture authenticity remains caller supplied, challenges are rejected and prices remain unpriced without a validated price contract. Goofish keeps its existing primary-DOM capture shape.

## Source and access evidence

- Fansbuy homepage: actual HTTP 200; linked index JavaScript: HTTP 403; the concurrent language-asset outcome is unknown. Requests to that source stopped. Named-platform evidence comes from dated indexed official copy, not the empty SPA shell or an invented static enum.
- One T3 DuckDuckGo discovery query: HTTP 202/CAPTCHA. That host was not retried or operated. The initial metadata worker made no product reads.
- Root independently used the connector's index to discover exact native routes, without reopening the challenged Fansbuy/DDG surfaces. Five connector query strings produced no exact electronics leads on the new markets; a broader Weidian result supplied a native route for a transport canary. Index amounts were never accepted as current prices.
- A direct cookie-free Weidian HTTP GET returned the exact requested product page. The initial generic parser returned `item_schema_unverified`. Retained source exposed an inline identity-bound server state and a delisted primary item despite stock 8,000; the subsequent reader improvement is driven by those bytes. A separate post-integration canary at 19:15:23–19:15:26 UTC retained numeric HTTP 200, the same decoded-body hash, and an integrated `ok` receipt with delisted availability and no price. This is not a purchasable electronics candidate, a price recommendation or seller-authenticity finding.

See [the parser/acquisition handoff](fansbuy-new-marketplaces-live.md) for exact retained-source bounds. Private decoded HTML, access receipts, hashes, discovery output and review receipts stay under `.local/fansbuy-expansion/`. HTML re-encoding hashes are distinguished from server wire-byte hashes. No successful live Tmall/1688 product extraction, fresh selected-variant price or live coupon redemption is asserted.

## Three implementation and validation rounds

1. **Registry and command contracts.** Added the three keys, pure strict URL/ID helpers and normalization identity evidence; wired HTTP/browser index discovery, configuration, plans, filters, native refusal, refresh sanitization, promotion/coupon hosts and capability output. The 490-test checkpoint passed. Independent review cleared its bounded contract scope with 189 existing tests, seven additional checks and 81 JSON cycles; six subprocess tests were excluded by that review harness.
2. **Acquisition, capture and workflow evidence.** Added the generic identity-bound metadata reader, network-free browser import and cross-command tests. The 521-test checkpoint passed. A real Weidian body exposed the missing native-state shape and prompted the delisted/stock-preservation extension. Initial generic tests are explicitly synthetic, not live product proof. Independent round-two review found login-wall classification/host-gating and premature HTTP EOF defects. Both were corrected; the original four reproduction methods and eight independent control methods pass against current source, and 536 repository tests pass with sockets/DNS blocked.
3. **Final adversarial reconciliation.** Independent third-round review found no remaining P1/P2 within scope, verified both original acquisition fixes, rejected 52 state mutations and passed 243 normalization/ranking cycles. Its isolated suite passed 533 tests with three optional private-capture skips; root passed all 536 with network blocked. Final acquisition, state, identity, history, coupon and financial-boundary checks are recorded in [release validation](../VALIDATION.md). The final review and release receipts remain distinct from the two earlier checkpoints and from live source access.

No marketplace account, login, cart, order, coupon claim, seller message, purchase, payment, shipment submission or customs declaration occurred. No CAPTCHA, proxy, signing/replay or account-block bypass was used. No LLM API is called by the CLI.
