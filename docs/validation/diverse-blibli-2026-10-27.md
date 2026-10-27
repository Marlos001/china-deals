# Diverse Blibli guest validation — 27 October 2026

**Concrete result:** five different exact product pages returned HTTP 200 without an account. Baseline 0.6.0 parsed the Sony WH-1000XM6 selected SKU successfully; it rejected four single-option products because their selected `attributes` arrays are empty. Two rejected products have explicit selected-SKU prices (Ryzen and DJI). Search itself remained blocked. These observations describe this bounded run, not universal Blibli access or inventory.

Baseline: `/home/marlos/projects/china-deals`, HEAD `b134840ec0dc10ca48fa617e1d7ecaab2ea838ee`; initial Git status clean. Installed `china-deals --version` and installed distribution metadata both reported `0.6.0`; the installed interpreter resolves the package to this checkout. The actual checkout `cli.main(argv)` was exercised with a research-only transport recorder. Only this report and `.local/diverse-search/blibli/` are owned. No application code, tests, commits or pushes were changed/run. No purchases, login, carts, seller messages, proxies, extensions or challenge interaction.

## Access, retention and query budget

- **Five connected-web discovery queries**, all scoped to first-party Blibli product routes. Two connector calls: three queries, then two. No connector product opens. Discovery preceded the HTTP run; no connector/browser transport was tried after a challenge.
- **Five exact product HTTP reads, each once**, 17:37:49–17:37:57 UTC. All returned 200. Retained response bodies are 232–239 KB, below the 2 MiB bound. Headers report `no-cache, no-store`; HTTP/source server dates are from this run. This is fresh retrieval of source claims, not a checkout or physical-inventory audit.
- **Five accepted CLI search query commands**, one per product. The first made two HTTP requests: Blibli API **403**, then the separate DuckDuckGo discovery surface **202 with challenge**. The remaining four commands made **zero requests**, with `skipped_after_challenge` receipts for both hosts. Thus ten logical query specifications total: five connector queries and five CLI queries. Only two CLI search HTTP requests were sent; the connector's internal network request count is not exposed.
- Total recorded Python HTTP requests: **7 = 5 product + 1 API + 1 index**. No repeated product requests. No HTTP work after the two search gates. No browser was needed or opened, so no owned tabs remain.
- Raw bytes were saved privately **before** `_html`/JSON/product parsing; error bodies were retained before the adapter classified them. [Network receipts](../../.local/diverse-search/blibli/network.json) include exact URLs, times, sizes and SHA-256. [.local evidence directory](../../.local/diverse-search/blibli/) is Git-ignored and private. No raw HTML is committed.

The harness wraps `urllib.request.OpenerDirector.open` to retain the original response bytes, leaving the real network response and production parsers in place. It reuses `guest.access_session()` across CLI invocations so both host gates persist. It does not supply fixtures or replace source content. An initial `--hydrate 0` argument was rejected locally (exit 2, no search request); the resumed search stage omitted that argument, using the default disabled hydration. Existing product receipts were reused; products were not fetched again. [Original error](../../.local/diverse-search/blibli/run.stderr), [resume receipt](../../.local/diverse-search/blibli/resume-start.json), [final gates](../../.local/diverse-search/blibli/gates.json), [completed run](../../.local/diverse-search/blibli/run-end.json).

## Fresh product observations

All amounts below are **IDR**. Currency comes from the Blibli adapter contract; the selected summary price objects have no explicit currency field. No FX conversion, international shipping, import tax or coupon subtraction is applied. `stock` is the summary's literal stock claim; it is not independently verified or necessarily an isolated per-color quantity. `selected.available` is reported separately. All five summaries identify product type `REGULAR` and `preOrder.isPreOrder=false`. No structured condition was established.

| Product and exact requested source | Selected child / pickup point | Fresh price and availability evidence | Fulfillment / baseline CLI |
| --- | --- | --- | --- |
| [Steam Deck OLED White Limited Edition 1TB][steam] — PSEGAMESHOP | `PSP-60021-07252-00001` / `PP-3035029`; one selected option, no attribute dimensions | **Price field absent**; stock **33**, selected available **false**, tag `COMING_SOON`. Positive stock alone is insufficient. | Delivery `AVAILABLE`, pickup `UNAVAILABLE`; CLI `item_state_unverified`, exit 3. |
| [Sony WH-1000XM6 Platinum Silver][sony] — Sony Electronics | `SOA-60059-00376-00003` / `PP-3205922`; `Warna=Platinum Silver`, exactly one selected color | Offered **Rp6,179,000**, listed **Rp7,499,000**, displayed discount **18%**; stock **1173**, selected available **true**. | Delivery and pickup `AVAILABLE`, selected `DELIVERY`; CLI **ok**, exit 0, `recent_observation`. |
| [AMD Ryzen 7 9800X3D Box][ryzen] — Foursquare Computer | `FOC-70056-02589-00004` / `PP-3508358`; one selected option, no attribute dimensions | Offered/listed **Rp8,905,000**, discount **0%**; stock **25**, selected available **true**. Box is a title claim; source warranty claims three years. | Delivery `AVAILABLE`, pickup `UNAVAILABLE`; CLI `item_state_unverified`, exit 3. Price is a manually inspected fresh source claim, **not CLI-admitted**. |
| [Gigabyte RTX 5070 Ti GAMING OC 16G][rtx] — IT Shop | `ITS-29724-04198-00001` / `PP-3005896`; one selected option, no attribute dimensions | **Price field absent**; stock **0**, selected available **false**, `COMING_SOON`. Source selling-point field specifies 16GB GDDR7/256-bit. | Delivery `AVAILABLE`, pickup `UNAVAILABLE`; CLI `item_state_unverified`, exit 3. Generic delivery capability does not imply purchasability. |
| [DJI Mini 4 Pro with DJI RC 2][dji] — FUJISHOPid Sedayu | `FUS-60039-01703-00001` / `PP-3414881`; one selected option, no attribute dimensions | Offered **Rp12,266,000**, listed **Rp14,430,000**, displayed discount **15%**; stock **1**, selected available **true**. RC 2 is explicit in title and selling points; Fly More bundle is not established. | Delivery `AVAILABLE`, pickup `UNAVAILABLE`; CLI `item_state_unverified`, exit 3. Price is a manually inspected fresh source claim, **not CLI-admitted**. |

Exact native selected URLs, including `pickupPointCode`, are retained in [analysis.json](../../.local/diverse-search/blibli/analysis.json). Parent `/ps--` URLs above resolved to the explicit selected child in the summary; no child URL was fetched a second time. Seller `official=true` and `status=ACTIVE` are source claims, not independent seller verification. All five also expose `businessOperational.status=CLOSE`; do not interpret this alone as permanently closed, or silently overwrite the other source fields. Delivery/pickup flags do not establish destination coverage, fees, collection address, forwarder acceptance or Indonesia-to-Brazil eligibility.

The three numeric amounts come from `summary.price.offered`, with separate listed prices and separate `installment.startFrom` values: Sony **257458**, Ryzen **371042**, DJI **511083**. Those smaller amounts are installments, **not full prices or discounts**. No deposit wording/field was established in this retained summary; offered amounts are ordinary displayed item-price claims, not verified payable totals. Conditions, detailed package contents and payment eligibility remain unresolved.

Sony's source also binds campaign `CAMP-03340`, `ELECTRODEALS OKT 2026`, with `promoEndTime=1793465940000` (**2026-10-31 16:59 UTC**, 23:59 WIB). This is campaign membership/time evidence, not an extra coupon. No code, additional deduction, quota, account eligibility or stacking was established. The displayed 18% and DJI's 15% are retained source comparisons, not independently verified historical savings. Other summaries expose no `campaignInfo` in these captures. No promo endpoint was called.

## Indexed evidence stays separate

The connected search receipts are [discovery 1](../../.local/diverse-search/blibli/01-web-discovery.json) and [discovery 2](../../.local/diverse-search/blibli/02-web-discovery.json). Connector relative crawl ages are reproduced literally; exact crawl dates were unavailable. Receipt file creation is retention time, not source freshness.

- Steam White 1TB exact parent: **4 months ago**. Sony selected Platinum Silver child: **last week**. Ryzen Box exact parent: **last week**. RTX exact parent: **2 weeks ago**. DJI RC 2 exact parent: **last week**. These provided links; numeric fresh observations above come solely from the later retained HTTP responses.
- The indexed [RTX parent][rtx] claimed **Rp23,990,000 and 1 remaining**, while this run's fresh state has no price, zero stock and selected availability false. This is a concrete reason never to promote an index lead into a price or current stock claim. The old amount is excluded.
- The Steam search surfaced [child `PSP-60021-06475-00030`][steam-wrong] and sibling `...00031`: their base titles contain OLED/512GB/1TB, but the indexed selected variant is **LCD 512GB**. They are wrong-target discovery leads for OLED 1TB. Neither was opened or priced. A base-title keyword match must not override selected-variant conflicts.
- Ryzen search surfaced both tray and box products. The chosen Box page avoids merging their package/warranty claims. DJI query used `RC 2` to narrow controller configuration; a generic Mini 4 Pro title does not prove RC 2 or Fly More contents.

## Actual filtered search behavior

Common argv: `--markets blibli --access guest --guest-engine http --currency native --limit 5 --timeout 20 --include-offers --sort price-asc --condition new --city Jakarta --free-shipping`. No native-mode session or browser fallback. The requested ranges are research constraints, not expected market prices.

| CLI query | Minimum / maximum IDR | Result |
| --- | ---: | --- |
| `Steam Deck OLED 1TB` | 5,000,000 / 20,000,000 | API 403; index challenge; exit 3; no offers |
| `Sony WH-1000XM6` | 3,000,000 / 9,000,000 | Both hosts skipped after challenge; exit 3; no network |
| `AMD Ryzen 7 9800X3D` | 5,000,000 / 12,000,000 | Both hosts skipped after challenge; exit 3; no network |
| `RTX 5070 Ti 16GB` | 10,000,000 / 30,000,000 | Both hosts skipped after challenge; exit 3; no network |
| `DJI Mini 4 Pro RC 2` | 8,000,000 / 25,000,000 | Both hosts skipped after challenge; exit 3; no network |

Every `filters blibli QUERY ...` plan returned `documented_native_filters=[]`, `submitted_native_filters=[]`; all six restrictions remain `unverified_or_local_filters`. Actual API URL contains only `searchTerm`, `start=0`, `itemPerPage=5`. There is **no source-verified native filter mapping** to invent here. No claim of successful price sorting, Jakarta-only inventory, new condition or free shipping is justified. The four skipped queries are not four independent demonstrations of a marketplace outage. [Full argv and exits](../../.local/diverse-search/blibli/commands.json), [first search](../../.local/diverse-search/blibli/search-steam-deck.json).

An offline call to production `filters.evaluate_offer` using the real parsed Sony row matched both price bounds but left `condition`, `city` and `free_shipping` unknown. `source_detail.merchant_claims.location` retains `SONY WAREHOUSE - Kota Jakarta Pusat`, while normalized `location` is null. This is a concrete location-extraction gap for local filters, not evidence that requested native filtering worked. A future mapping should specify seller location versus fulfillment origin; it must not infer shipping destination or free shipping. [Offline evaluation](../../.local/diverse-search/blibli/sony-filter-evaluation.json).

## Root implementation handoff: bounded repros and improvements

1. **Priority: valid single-option products disappear.** `blibli_public.parse_product_state` requires at least one selected attribute ([source](../../china_deals/blibli_public.py), approximately line 254). All four failing pages have exactly one selected option with a coherent product/child/pickup tuple, `attributes=[]` on the option and summary, and native selected URL binding. Production raises `ValueError: Missing selected variant attributes`; `guest._blibli_detail` collapses it to `item_state_unverified`. Ryzen and DJI therefore lose explicitly available numeric source claims. Support dimensionless single-option products only when unique selected identity and all URL/pickup/price bindings remain validated. Do not synthesize an attribute from the title or weaken conflicting-SKU rejection.
2. **Keep unavailable detail useful without ranking it.** Steam and RTX lack `price` entirely, not a literal JSON null price. Both have selected availability false and `COMING_SOON`; RTX stock is zero, Steam stock is 33. After supporting empty attributes, the existing mandatory price-object check would still reject them. Preserve bound identity, explicit unavailability, tags and fulfillment with `price=None`, instead of classifying a readable unavailable product as an unknown schema. Never turn Steam's positive stock into availability. This second failure follows from code and original fields; no altered fixture was used.
3. **Retain diagnostic reason and source receipt.** Generic `item_state_unverified` obscures the shared empty-attributes shape. Expose a stable, non-sensitive parser reason and optional body hash/artifact pointer. This run's private raw bytes make the failure replayable without new requests; production currently discards this distinction.
4. **Improve discovery handoff and local location mapping.** A readable exact URL can yield useful detail even when search fails, as Sony proves before the later API gate. Expose bounded agent-supplied primary links as discovery inputs with evidence tiers; never silently hydrate after a challenge or treat connected-web snippets as current offers. Preserve the Sony merchant location with an explicit semantic basis so local filtering can use it where appropriate.
5. **Product relevance must reconcile selected variants.** Preserve the indexed LCD 512GB Steam mismatch as a discovery counterexample. Do not equate title token overlap with OLED 1TB compatibility; keep tray/box CPU and drone-controller/bundle distinctions. This run proves a source discovery hazard, **not** a measured false-positive rate of the CLI's relevance implementation (native search returned no rows).
6. **Retain useful promo/stock semantics.** The Sony successful parser preserves selected price and fulfillment but omits `campaignInfo`, `installment`, `tags`, `preOrder` and merchant operational status from its source-detail projection. Bounded raw claims would let reviewers distinguish sale membership, installment amounts and explicit unavailability without another fetch. No extra discount should be inferred.

No fixes or regression tests were implemented by this research worker. The strongest follow-up is the single-option parser improvement using the retained Ryzen/DJI/Steam/RTX bytes, while preserving the successful Sony binding and fail-closed ranking behavior.

## Reproduction and source inventory

Safe offline reproduction, hashes checked first, no HTTP:

```sh
cd /home/marlos/projects/china-deals
PYTHONDONTWRITEBYTECODE=1 python .local/diverse-search/blibli/analyze.py
```

Observed result: **5 retained product hashes verified; 1 parser success, 4 identical empty-attributes failures**; Sony local filter evaluation is unknown for condition/city/free shipping. This is a replay of real bytes, not a newly added application test. [Analysis script](../../.local/diverse-search/blibli/analyze.py), [analysis results](../../.local/diverse-search/blibli/analysis.json). All report-local links resolved. Final status also showed concurrent changes to `china_deals/products.py`, `china_deals/product_profiles.py`, `tests/test_structured_product_evidence.py` and `docs/validation/diverse-china-2026-10-27.md`; those belong to other work and were left untouched. HEAD remained unchanged.

Executed live harness commands (historical receipt, **do not replay this run**):

```sh
PYTHONDONTWRITEBYTECODE=1 python .local/diverse-search/blibli/run.py
PYTHONDONTWRITEBYTECODE=1 python .local/diverse-search/blibli/run.py --resume-search
```

The first exited 2 at the invalid hydration argument after five completed product reads; the second resumed searches only and exited 0. Individual CLI exits are in `commands.json`: five detail calls (3/0/3/3/3), five filter plans (0), five searches (3). Each detail argv was `china-deals detail blibli EXACT_URL --access guest --guest-engine http --currency native --timeout 20`. No subprocess/live work remains.

Connected query strings, exactly five:

```text
site:blibli.com/p/ "Steam Deck" "OLED" "1TB"
site:blibli.com/p/ "Sony" "WH-1000XM6"
site:blibli.com/p/ "Ryzen" "9800X3D"
site:blibli.com/p/ "RTX 5070 Ti" "16GB"
site:blibli.com/p/ "DJI Mini 4 Pro"
```

Exact search HTTP URLs are in `network.json` and `gates.json`; no undocumented private API was guessed. The five original product bodies correspond in table order to `http-01.body` through `http-05.body`; parser replays to `http-0N.body.parser.json`. `http-06.body` retains the API denial; `http-07.body` retains the independent index challenge. Full source state JSON is private; `analysis.json` projects only review-relevant claims.

[steam]: https://www.blibli.com/p/steam-deck-oled-limited-edition-white-color-1tb/ps--PSP-60021-07252
[sony]: https://www.blibli.com/p/sony-wh-1000xm6-noise-cancelling-headphones-1000xm6/is--SOA-60059-00376-00003
[ryzen]: https://www.blibli.com/p/amd-ryzen-7-9800x3d-box-processor-8-core-16-thread-up-to-4-7-ghz-garansi-resmi/ps--FOC-70056-02589
[rtx]: https://www.blibli.com/p/gigabyte-geforce-rtx-5070-ti-gaming-oc-16g/ps--ITS-29724-04198
[dji]: https://www.blibli.com/p/dji-mini-4-pro-dji-rc-2-drone-garansi-resmi/ps--FUS-60039-01703
[steam-wrong]: https://www.blibli.com/p/steam-deck-oled-valve-handheld-gaming-pc-steamdeck-512gb-1tb/is--PSP-60021-06475-00030
