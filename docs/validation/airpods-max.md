# AirPods Max guest validation — 2026-10-27

## Outcome and scope

No live purchasable AirPods Max offer was established. The actual guest HTTP CLI returned **zero items across all four markets**, exit **3**, with explicit access failures. This does not prove no inventory. No item price, seller, availability, selected variant, authenticity, coupon eligibility, or cheapest whole-headphone offer can be certified from this run.

Repository started clean on `main`, `1a096f326da6b89e0b2b1732dcdc1eca0870e4bb`, CLI `0.3.0`. Root owns production code. This validation writes only this report and `.local/search-validation/airpodsmax/`; no commit/push, account/login, payment/cart action, seller contact, challenge solving, or session-cookie reuse. Existing peer edits were preserved.

Frozen baseline: **168 tests pass**. Initial offline binding regressions: **3 failures, 1 passing control test**. Final root-tree recheck: **180 existing tests pass**, the search-URL ranking defect is corrected locally, **2 binding regressions remain**, and the product classifier still has **6 failing cases**. These synthetic failures are code evidence, not observations of live marketplace listings.

## Actual CLI and request budget

Executed once after correcting a pre-network argument error:

```sh
python -B -m china_deals search 'AirPods Max' \
  --markets taobao,jd,goofish,blibli \
  --zh-query '苹果 AirPods Max 头戴式耳机' \
  --query-for 'blibli=AirPods Max' --access guest --guest-engine http \
  --timeout 12 --limit 5 --currency native --include-offers
```

Started `2026-10-27T15:54:06Z`; elapsed **3.440 s**, outer subprocess timeout **65 s**, exit **3**. Native currency avoided an unrelated FX request; no hydration requested. The initial `--hydrate 0` command exited **2** during argparse validation (`must be between 1 and 100`) and made no network search. It was corrected by omitting the flag; it was not a repeated HTTP search.

- Taobao, JD, Goofish: exact Chinese query above; each one DuckDuckGo index request returned `blocked/challenge`.
- Blibli: exact `AirPods Max`; public API returned `http_403`, then its separate index-discovery request returned `blocked/challenge`.
- All four sources: `item_count: 0`; empty `groups`, `unranked`, and `offers`. There are **no CLI-returned product URLs to compare in a browser**. Constructed `filter_plan.native_search_url` values are not item links or executed-search proof.
- Guest access metadata is `authenticated: false`. No native-session fallback was enabled.

Receipts: [full JSON](../../.local/search-validation/airpodsmax/cli.json), [command/timing](../../.local/search-validation/airpodsmax/cli-receipt.json), [pre-network parse rejection](../../.local/search-validation/airpodsmax/parse-rejected-cli.stderr).

Conservative budget count: **12 targeted query submissions**, including the API and fallback separately: 5 CLI requests; 1 Google query; 3 Bing queries; 3 native browser searches (Blibli, Goofish, JD). **0 marketplace product opens** of the allowed 4. One Apple Support reference page was opened, not a marketplace product listing. Redirects and static resources are not extra targeted queries. No further query budget remains.

## Separate browser evidence; not CLI output

Used T3 `preview_status`, then `preview_open(profileId="incognito", reuseExistingTab=false, open=false)`. Returned tab **`tab_r_4cac2679-3846-4860-a3d7-8c794cdb6e4b`** had `profileId: incognito`, owner `agent`, `ownedByCaller: true`. Every later browser call supplied that explicit ID. The tab was closed after capture. Artifacts below are **DOM/tool observations, not saved screenshots**.

- [Google Apple query](https://www.google.com/search?q=site%3Aapple.com+AirPods+Max+USB-C+Lightning+identify): unusual-traffic page, HTTP 429; no interaction or retry. [Proof](../../.local/search-validation/airpodsmax/browser-google-challenge.json).
- [Bing Blibli query](https://www.bing.com/search?q=site%3Ablibli.com%2Fp%2F+AirPods+Max): displayed Apple/Brazilian retail results rather than verified Blibli item results. These were rejected as wrong-market leads; no displayed price was imported. [Proof](../../.local/search-validation/airpodsmax/browser-bing-blibli.json).
- Bing Taobao and JD site queries used `苹果 AirPods Max 头戴式耳机`. Both displayed `Resolva o desafio abaixo para continuar`, no product links. The JD navigation was submitted immediately after the Taobao capture in the same orchestration step; it was an avoidable second query to a challenged engine. No further Bing query or challenge interaction followed. [Taobao proof](../../.local/search-validation/airpodsmax/browser-bing-taobao.json), [JD proof](../../.local/search-validation/airpodsmax/browser-bing-jd.json).
- [Blibli native search](https://www.blibli.com/cari/airpods-max): redirected to `/challenge/landing/`, `Ada aktivitas yang tidak biasa`; stopped. [Proof](../../.local/search-validation/airpodsmax/browser-blibli-native.json).
- [Goofish native search](https://www.goofish.com/search?q=%E8%8B%B9%E6%9E%9C%20AirPods%20Max%20%E5%A4%B4%E6%88%B4%E5%BC%8F%E8%80%B3%E6%9C%BA): query title loaded; body had `加载中...`, login invitation and unrelated suggested queries; no `/item?` links in the capture. This is an unresolved guest/loading observation, not an empty-inventory result or a verified authentication diagnosis. [Proof](../../.local/search-validation/airpodsmax/browser-goofish-native.json).
- [JD native search](https://search.jd.com/Search?keyword=%E8%8B%B9%E6%9E%9C%20AirPods%20Max%20%E5%A4%B4%E6%88%B4%E5%BC%8F%E8%80%B3%E6%9C%BA): navigation first reached `cfe.m.jd.com/.../risk_handler/...`, then automatically redirected to `passport.jd.com/new/login.aspx`; login page only. No login attempted. [Final-page proof](../../.local/search-validation/airpodsmax/browser-jd-native.json).
- Taobao native search/product page was not opened; budget used by the checks above. No live primary seller page or recommendation-to-item comparison was possible for any market.

## Primary Apple identity reference

[Apple: Identify your AirPods](https://support.apple.com/en-us/109525), captured live; page says **Published Date: September 25, 2026**. [Retained text](../../.local/search-validation/airpodsmax/browser-apple-identify.json):

- `AirPods Max 1 (Lightning)` — **A2096**, year introduced **2020**.
- `AirPods Max 1 (USB-C)` — **A3184**, year introduced **2024**.
- `AirPods Max 2` — **A3454**, year introduced **2026**.
- Apple locates the Max model number behind the cushion on the left ear cup.

These years/names are literal Apple evidence, not inferred marketplace model years. The captured identification section does not specify the Max 2 connector; do not derive it from the product family alone. A seller title saying only “AirPods Max”, “new”, or “2026” does not establish A3454, authenticity, connector, condition, or selected SKU. Whole headphones including a Smart Case differ from a Smart Case-only listing. No actual marketplace item was bound to any of these Apple identifiers in this run.

## Reproduced baseline defects — root-owned fixes

All IDs, prices and URLs in the repro fixtures are **synthetic and never fetched**. The minimal suite exercises the existing normalization/ranking and Blibli detail parser. Run from repository root:

```sh
python -B .local/search-validation/airpodsmax/repro.py \
  --repo .local/search-validation/airpodsmax/baseline
# expected current baseline: exit 1, 3 failing tests, 1 passing control
python -B .local/search-validation/airpodsmax/repro.py --repo .
```

1. **Non-product marketplace URL enters price ranking.** JD `sku=123`, price `100`, URL `https://search.jd.com/Search?keyword=AirPods` becomes a ranked CNY candidate. Domain safety is checked, but a valid product route and item binding are not required. Fix the rank/normalize boundary to distinguish safe host from product identity. Tests should cover search, category, shop and recommendation URLs across all four markets, valid native routes, and ID mismatch. Keep the original unsafe/unbound observation for review without creating a price candidate.
2. **Embedded Offer identity conflicts are ignored by imported normalization.** Outer JD URL/sku identify `123`, embedded `offers.url` identifies `456`, and embedded price `200 CNY` is ranked under item `123`. The explicit outer ID-vs-URL conflict control already passes; it is specifically the nested Offer identity that is not checked. Bind Product, Offer, item ID and selected variant before accepting the amount. Test raw import and normalized round-trip. The guest Blibli parser already rejects an Offer URL mismatch; preserve that protection when fixing the broader normalization seam.
3. **Blibli explicit out-of-stock status is lost.** A unique URL-bound Product/Offer with `availability: https://schema.org/OutOfStock` survives `_blibli_detail`, but the normalized availability becomes `unknown` and the IDR price is ranked. Preserve explicit availability from the bound Offer; test OutOfStock, SoldOut, Discontinued, unknown, and source-claimed InStock without turning source claims into checkout verification. Retain the literal Offer evidence.

Source locations at baseline: `china_deals/models.py:103` (`normalize_offer`, URL handling around 151–201), `china_deals/ranking.py:9` (`rank_offers`), `china_deals/guest.py:384` (`_blibli_detail`). [Frozen repro output](../../.local/search-validation/airpodsmax/frozen-repro.log), [working-tree output](../../.local/search-validation/airpodsmax/working-repro.log).

Actual **offline CLI** corroboration, not just direct function calls: `python -B -m china_deals rank <absolute rank-input.json> --currency native` from the frozen baseline returns exit **0** and ranks **both** the search-URL row and conflicting embedded-Offer row. [Input](../../.local/search-validation/airpodsmax/rank-input.json), [output](../../.local/search-validation/airpodsmax/frozen-cli-rank.json), [exact command/cwd](../../.local/search-validation/airpodsmax/frozen-cli-rank-receipt.json).

Passing controls: ordinary bound whole-headphone price remains rankable; search-index prices, explicit outer ID mismatch, `availability=unavailable`, and ambiguous price strings (`定金 ¥100`, `¥100/月`, range, starting price, coupon-labelled price) remain unranked.

## Iterative review of root's in-progress classifier

Peer-created `china_deals/products.py` / `tests/test_products.py` appeared during validation. They were read and tested, not modified. Current results are pinned by file hashes in [offline-test-receipt.json](../../.local/search-validation/airpodsmax/offline-test-receipt.json); they are not claims about committed `0.3.0` behavior or a completed root change.

```sh
python -B .local/search-validation/airpodsmax/product-repro.py --repo .
# captured result: exit 1, 6 failures, 1 passing multi-case control test
```

Six actionable cases:

- `AirPods Max 头梁 单卖`: currently `match`; headband sold separately must be excluded from whole-headphone candidates.
- `AirPods Max 维修 不开机维修`: currently `match`; repair service must be excluded.
- `AirPods Max display dummy 模型机`: currently `match`; display dummy must be excluded.
- `AirPods Max 1:1 replica 高仿`: currently `match`; explicit replica/non-original wording must not qualify as genuine Apple headphones. This fixture does not authenticate or accuse any real seller.
- `Apple AirPods Max USB-C 头戴式耳罩式耳机`: currently `mismatch`; the broad `耳罩` accessory substring rejects the ordinary over-ear headphone phrase. Require accessory context, not that substring alone.
- `Apple AirPods Max USB-C 含 Smart Case`: currently `mismatch`; a clearly included case must not make the whole headphone listing an accessory. Add Chinese inclusion boundaries alongside English `with`/`includes`; preserve selected-variant checks.

Controls pass for Smart Case-only, ear cushions/耳垫, replacement headband, English included Smart Case, the three primary-confirmed model identifiers, and an unrelated primary title with an AirPods recommendation only in description. [Final output](../../.local/search-validation/airpodsmax/working-product-repro.log). The initial test harness had one incorrect “Smart Case → uncertain” control; it was corrected to an unrelated-headphones title, with the original log retained and correction explained in the receipt.

## Further bounded tests and product improvements

[80-case synthetic matrix](../../.local/search-validation/airpodsmax/negative-example-matrix.json): 20 titles × 4 markets; preserved baseline signals and current classifier output. **All 80 rank in baseline when supplied a numeric price and native product URL**, including accessories, wrong product, deposit/monthly titles and unrelated primary title. Baseline labels comparability unverified; lack of semantic product filtering is a documented capability gap, distinct from the three binding defects above.

- Bind the requested product intent to title and selected variant. Recommendation text in description must never prove the primary product, revision, seller, price or availability.
- Separate whole headphones from Smart Case, ear cushions/耳垫, standalone/replacement headband/头梁, repair/维修, display dummy/模型机, and explicit counterfeit/replica keywords (高仿, 精仿, 山寨, 复刻, replica). Use context and review reasons rather than blanket word bans; accessory compatibility may mention every revision.
- Deposit (`定金`, `订金`, `首付`, `deposit`, `uang muka`) and instalment (`月供`, `per bulan`, `/month`, `cicilan`) constraints must follow the price when those qualifiers are outside the numeric price field. Do not rank `100` as the total just because its string is clean. Whole-product relevance and price eligibility are separate decisions.
- Coupon-labelled/new-user/member/app/card/quota prices require source-linked terms and explicit purchasing-account context. Do not invent coupon rules, treat a price after coupon as universal, subtract a coupon twice, or transfer entitlement to a buying agent. No live coupon terms or eligible account were verified here.
- Keep A2096, A3184 and A3454 separated when exact-model comparisons are requested; retain colour, condition, selected variant, raw price and currency. A source that lists several variants but a minimum price does not bind that price to a particular revision.
- Preserve bound seller identity from the primary Product/Offer or page. Recommendation-card sellers and prices must not populate the primary offer. Missing seller evidence stays unknown.
- Consider a per-run host challenge stop/circuit breaker: the CLI issued four DuckDuckGo query requests after each response reported a challenge. This is observed request behavior, not a bypass. Report later sources as not attempted because of the prior host block, rather than retrying that discovery host within the same run.

## Verification receipts and remaining gaps

The first working-tree full suite ran **175 tests, one error**: new peer `test_products` passed `query=` before `rank_offers` accepted it. Treat this as an intermediate integration state, not a baseline regression. [Log](../../.local/search-validation/airpodsmax/baseline-tests.log).

For immutable baseline proof, `git archive 1a096f3 china_deals tests` was extracted only under the owned artifact directory. Its first run lacked the example coupon fixture; `examples` from the same commit was then added, and **168 tests passed in 0.416 s**. [Final frozen log](../../.local/search-validation/airpodsmax/frozen-baseline-tests.log); the incomplete-fixture failure is separately retained. The baseline snapshot is a test artifact, not a worktree or production edit.

Final iterative recheck after root edited ranking/classification/CLI: **180 existing tests pass in 0.439 s**; the binding suite now has **2 failures and 2 passes**, because the non-product search URL is no longer ranked. Embedded Offer URL conflict and Blibli OutOfStock loss remain. All six product-classifier failures remain, with the positive/negative control test passing. Source hashes were stable across this final check. [Final source hashes and exact commands](../../.local/search-validation/airpodsmax/final-offline-receipt.json), [binding log](../../.local/search-validation/airpodsmax/final-working-binding.log), [product log](../../.local/search-validation/airpodsmax/final-working-products.log), [180-test log](../../.local/search-validation/airpodsmax/final-working-suite.log). Earlier receipts are retained rather than overwritten.

No live product-open comparison, exact item price, in-stock variant, seller authenticity or coupon applicability was established. No claim of live marketplace success, complete inventory, or deployment is made. Root's next step is to address the **2 remaining binding defects and 6 classifier cases**, then rerun the supplied offline regressions and retain final source hashes; do not replay external searches from this exhausted budget.
