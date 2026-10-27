# Fresh acquisition and Brazil comparisons

A two-week search crawl is useful for discovering a link. Fetching that index today does not refresh its price. Version 0.6 separates discovery, source observation, price history, promotion evidence and account eligibility. It uses your existing subscription agent for translation and interpreting terms; no AI API is called.

## Price workflow

1. Use `plan` and native-language `search` to discover exact product links. All Chinese marketplaces require Chinese queries. Keep all requested hardware generations/configurations separate.
2. Use `refresh` on a shortlist/watchlist. Each invocation attempts first-party detail; it never serves an old quote as a successful refresh. The HTTP core is cookie-free. The optional browser reader uses a disposable Chromium context. A challenge stops that host during the command; there is no automatic transport switch or retry loop.
3. Inspect `price_freshness`, access receipts, exact variant, condition and fulfillment. `--fresh-only --max-age-hours 1` holds older/unknown observations out of ranking. Cached/index/proxy observations never pass, even with today's retrieval timestamp. Fresh observation does not establish stock or checkout acceptance.
4. Optionally keep local SQLite history with `--store`. Compare identical selected variants, currencies, conditions and payment terms before treating a change as a price drop. A seller's crossed-out reference price is not historical proof of a discount.

```sh
cp examples/watchlist.example.json watchlist.json
# Replace the synthetic placeholders with exact observed native URLs first.
china-deals refresh watchlist.json --currency native \
  --fresh-only --max-age-hours 1 --store /tmp/china-deals-history.sqlite
china-deals history --store /tmp/china-deals-history.sqlite --limit 20
china-deals rank shortlist.json --fresh-only --max-age-hours 1
```

The bundled watchlist contains synthetic placeholders. Replace them before requesting a live refresh. A failed or masked refresh has no current numeric price; an earlier observation remains separately labeled. Source observation timestamps survive capture imports, search hydration and offline re-ranking. Required freshness exclusions survive exported arrays. `--as-of` is an explicit historical simulation, never proof of today's price. Default price threshold is 24 hours. Choose a shorter threshold near a purchase.

HTTP requests ask intermediaries to revalidate with `Cache-Control: no-cache`; servers may still serve their own cached data. The CLI claims a recent **source observation**, not knowledge of an origin database's update time. It preserves source cache labels. No background scheduler is installed. Invoke refresh from your agent or your own scheduler with an appropriate cadence and retain the JSON receipt; never run a tight retry loop against a challenged site.

## Promotions and coupons

Read current public promotion terms and product-specific conditions before constructing rules. The `promotions` command is a bounded first-party evidence reader; returned text is untrusted evidence, not an automatically eligible coupon. JavaScript-only pages can be read by your subscription agent in T3 and imported through the documented capture path. A challenge is a failed acquisition, not evidence there are no coupons.

```sh
china-deals promotions blibli https://www.blibli.com/promosi --timeout 20
# For a browser page your agent can publicly read, evaluate the fixed
# china_deals.promotions.CAPTURE_JS expression and save its returned object:
china-deals promotions blibli https://www.blibli.com/promosi --from-browser-json capture.json
```

Capture imports are offline, bind the exact URL and preserve the original aware capture timestamp and text hash. Truncated captures are refused. The HTTP reader supports the four marketplaces' allowlisted primary hosts; a dynamic shell can produce `empty_unverified`, which does not mean no coupons exist.

The CLI requires fresh coupon evidence by default when evaluating rules. Default maximum age is **one hour**, independently of product age. A fresh campaign needs a primary HTTPS source, a recognized page/API mode, an aware original observation timestamp, and an explicit currently active start/end window. A later `verified_at` cannot renew an old observation. Dates and freshness alone cannot establish the actual buying account's eligibility.

```sh
china-deals coupons shortlist.json --rules current-campaigns.json \
  --coupon-max-age-hours 0.25 --currency native
```

Rules retain exact product/seller scope, minimum spend, caps and explicit `requires` facts for the real purchaser's account, payment, app, membership, quota or quantity. Unknown requirements remain potential; contradicted requirements are ineligible. A personal coupon does not automatically transfer to Fansbuy. Source quota and checkout applicability remain unknown unless the evidence establishes them. Discounts already included in the displayed price are never subtracted twice. Cashback stays separate, and stacking is not inferred.

`--allow-unverified-coupons` opts into historical/caller-asserted scenarios without the fresh-evidence gate. It does not turn them into independently checked promotions. CLI evaluation uses the current clock by default; a saved rules file's `as_of` cannot silently backdate it. The Python evaluator retains its backward-compatible optional gate.

## Import versus Brazil

```sh
china-deals brazil-compare examples/brazil-comparison.synthetic.json --format markdown
china-deals brazil-compare examples/brazil-references-2026-10-27.json --format markdown
```

This command is offline: no implicit FX or retailer request. Supply local `--fx-from-json` or payload `fx`. Reference FX dates older than seven calendar days, or in the future, hold a financial decision; weekend reference dates are allowed. It is not card/payment FX. Add actual spreads, IOF and payment fees as cost inputs.

Each case supplies `imported.offer`, `brazil.offer`, explicit identities and costs, `equivalence`, and `import_eligibility`. See the synthetic example for the complete schema. Exact known model, condition and nonempty variant dictionaries must agree; `equivalence.status=confirmed` cannot override a contradiction. Repaired/used and new products remain separate. Full cash/Pix prices and installment totals must be distinguished. An installment amount cannot win as a full product price.

Import costs are `domestic_freight`, `international_freight`, `insurance`, `taxes`, `agent_fees`, `payment_fees`, and `other_fees`. Brazil costs are `delivery` and `fees`. Each known cost has `{amount, currency, basis}`; `basis` is `scenario` or `observed`. Observed costs also need a recent aware `observed_at` to support a decision. Missing/null means unknown; an explicit zero is an assumption you must justify. Blibli international freight is excluded by the user's default per-market policy; taxes and other fees are not implicitly zero. Excluded freight is not free freight.

The output shows known subtotals, complete totals only when all applicable components are supplied, and savings/percent only when price, identity, freshness and eligibility checks pass. With missing import costs and a complete Brazil total, a break-even budget covers **all** missing import components, including a missing product price where applicable. It is not verified savings. `conditional_math` retains scenario arithmetic while review/eligibility holds remain visible. Import eligibility is a caller assertion, not legal clearance. No potential coupon or cashback is automatically deducted.

The [fresh Brazil research](validation/brazil-price-references.md) contains exact sources, payment bases and unresolved comparisons. The real example deliberately produces `needs_review`: the foreign AirPods Max 2 source is cached and its model/color/condition are not confirmed. The synthetic example demonstrates arithmetic only.

## Current access limits

First-party Taobao, JD and Blibli may require verification or withhold guest prices. This release does not guarantee access through those gates. Goofish main-item DOM can sometimes be read without an account; recommended products cannot supply its price. On 2026-10-27 at 17:08:36Z, T3 directly read the silver 1 TB iPhone listing at ¥7,499, with battery/replaced-screen and wholesale qualifiers preserved. Local capture import returned the same amount and original timestamp. This is fresh browser evidence plus offline import, not proof that every CLI transport succeeds or that the item can be procured or imported.


The new Blibli first-party state reader can also read a selected SKU from the HTTP product response when JSON-LD is absent. It validates parent/child identity, selected attributes and pickup point. This produced a fresh retained Midnight AirPods Max source observation at Rp8,799,000; the same source marks delivery unavailable and pickup selected. See [fresh-data validation](validation/fresh-data-2026-10-27.md). Access can change between requests; the rendered site still requested verification.
