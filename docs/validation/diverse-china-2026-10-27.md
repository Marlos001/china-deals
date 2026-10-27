# Diverse Chinese marketplace research — 2026-10-27

**Outcome: no verified current exact-product price and no best-price winner.** All five requested product families received Chinese connector searches. Four public Goofish primary-item DOMs were readable as a guest; the fifth product navigation, to JD, reached risk handling/login. Taobao yielded no exact product link in this bounded connector search. These are acquisition results, not inventory absence claims.

## Scope, revision and evidence

- Working root: `/home/marlos/projects/china-deals`; CLI `0.6.0`; baseline and post-acquisition HEAD `b134840ec0dc10ca48fa617e1d7ecaab2ea838ee`.
- Initial Git status was clean. SHA-256 snapshots of `pyproject.toml` and every top-level `china_deals/*.py` found no change during acquisition/import. See private `version-before.json` and `version-after-acquisition.json`; findings are bound to those bytes, not later root-agent edits.
- Final snapshot `version-final.json` observed concurrent WIP: modified `china_deals/products.py`, new `china_deals/product_profiles.py`, and new `tests/test_structured_product_evidence.py`. These were left untouched. The unsupported-intent finding describes the acquisition revision; the later implementation was not reviewed or tested here. Git HEAD still matched the baseline.
- Owned writes only: this report and `.local/diverse-search/china/`. No application/test edits, test suite execution, commits, pushes, accounts, carts, messages or purchases.
- Research workflow: project agent guide/FRESH_DATA, shared agent workflow, research skill and exact-root codebase graph. `china-deals` graph selected through paginated `list_projects`; focused filesystem reads confirmed relevant implementation.
- Raw evidence is private under `.local/diverse-search/china/` (directory mode 0700). `manifest.sha256` binds retained files; raw captures and redirect parameters must not be copied into public reports. Browser snapshots are bounded DOM/accessibility records, not independently retained screenshot images.

## Counts and execution bounds

| Measure | Result |
|---|---:|
| Successful-to-execution CLI search processes | 1 |
| Per-market search dispatches in that process | 3: Taobao, JD, Goofish, once each |
| CLI discovery network requests | 1 |
| CLI requests skipped after the shared-host challenge | 2 |
| CLI offers / native filters confirmed applied | 0 / 0 |
| Connector queries | 12 in four batches: 3 + 3 + 4 + 2 |
| Connector returned links / unique links | 35 / 35 |
| Product-route leads | 34: 19 Goofish, 15 JD, 0 Taobao |
| Other returned links | 1 Goofish seller page; not opened or treated as a product |
| Product-page navigations | 5: 4 Goofish, 1 JD |
| Complete bounded primary DOM captures / offline imports | 4 / 4 |
| Imported numeric exact-product prices | 0 |
| Browser tabs created / closed | 1 / 1, own T3 Incognito |

One initial CLI argument-validation attempt rejected explicit `--hydrate 0` (exit 2) **before any source request**. Its stdout, stderr and argv are retained as `cli-argparse-*`. The corrected invocation omitted hydration and exited 3. This is not a retry of a challenged host. No additional live search process ran after that challenge.

The requested per-market CLI checks were batched into one process to preserve the real shared-host gate. Separate processes would reset that gate and repeat the challenged DuckDuckGo surface. This is three market dispatches, **not three separately networked CLI searches**. Market query overrides intentionally exercise different products; the envelope still has the Steam Deck `intent_query`, so this is an acquisition/filter audit, not a cross-product ranking population.

```sh
python -B -m china_deals search 'Steam Deck OLED 1TB 掌机' \
  --markets taobao,jd,goofish \
  --query-for 'taobao=Steam Deck OLED 1TB 掌机' \
  --query-for 'jd=索尼 WH-1000XM6 头戴式降噪耳机' \
  --query-for 'goofish=锐龙 9800X3D 处理器' \
  --min-price 100 --max-price 15000 --condition new --free-shipping \
  --sort price-asc --strict-filters --limit 5 --include-offers \
  --currency native --access guest --timeout 20
```

Bounds are CNY; free shipping means domestic postage. These filters exclude very low-value components and constrain condition/postage, but they cannot prove SKU identity. All five requested filter keys remained unverified/local; `submitted_native_filters=[]` for all markets. `cli-search.json` records the first DuckDuckGo `challenge` and later `skipped_after_challenge`, `network_attempted:false` receipts. No claim is made that Taobao/JD/Goofish native search itself issued this challenge. Connector discovery was separately authorized and did not request the challenged DuckDuckGo URL.

`discovery-ledger.json` retains all 12 exact Chinese queries and all 35 returned titles/URLs with `price:null`, `source_mode:search_index`. The connector merges batch results; individual result-to-query attribution is not asserted. Query allocation was six Goofish, three JD, three Taobao. The two-query final batch returned empty results; the earlier Taobao queries returned no Taobao links. A broad combined Sony/DJI Taobao query was weaker than separate exact queries; no exhaustive Taobao coverage is claimed.

## Primary-page findings

All amounts below are **literal page observations, not current purchasable exact-target prices**. Four capture timestamps span 17:37:48.918Z–17:38:20.149Z. The existing `china_deals.goofish_public.CAPTURE_JS` was evaluated without modification against the main DOM; all captures had one main/info/price/description/labels container and no truncation. No recommendations supplied these amounts.

1. **Steam Deck OLED 1TB:** [Goofish item 982006970781](https://www.goofish.com/item?categoryId=126856327&id=982006970781), source title `【Steam deck OLED 1TB 极致优化双系统】拷_闲鱼`. Main display ¥1,240; seller text says `标价为预售64裸机`, attributes give `内存容量:64GB`. Description mixes OLED/LCD, upgraded 1T/2T and original 1T units. This is a wrong-price-basis/mixed-variant lead for the requested OLED 1TB. It is a presale base-unit amount, **not proven to be a deposit**. A purchase control exists but proves neither selected OLED stock nor checkout. Evidence: `capture2.json`, `import2.json`.
2. **DJI Mini 4 Pro:** [Goofish item 1080374220814](https://www.goofish.com/item?categoryId=0&id=1080374220814), `大疆Mini4pro套装版_闲鱼`. Main range ¥2,399–3,650, ordinary-controller variant, visible used-condition claim, and `已下架`. Delisted and range-priced; not an available exact bundle. Battery count and exact package contents remain unresolved. Evidence: `capture1.json`, `import1.json`.
3. **Ryzen 9800X3D false-positive discovery:** [Goofish item 1019398583977](https://www.goofish.com/item?categoryId=126856240&id=1019398583977), actual title `AMD锐龙R7 3700X 3800X R9 3900X散片_闲鱼`. Main display ¥468; older CPU models, motherboard/bundle language, `只卖cpu`, and `卖掉了`. The indexed 9800X3D text was not the main product. Wrong model, sold wording, unresolved older-model selection. Evidence: `capture3.json`, `import3.json`.
4. **RTX 5070 Ti 16G false-positive discovery:** [Goofish item 1039123072500](https://www.goofish.com/item?categoryId=126856282&id=1039123072500), actual title `英伟达定制RTX4090 48G 单涡轮 双宽_闲鱼`. Main ¥19,999 belongs to a different multi-model 4090/4080 listing with conflicting VRAM evidence, reference-price wording, and `已下架`. Exclude entirely from 5070 Ti comparison. Evidence: `capture4.json`, `import4.json`.
5. **Sony WH-1000XM6:** [JD platinum-silver source link](https://item.jd.com/product/zUfN_4_H-gL8GVi-4U8-TA.html). The connector title names WH-1000XM6 headphones. Direct T3 navigation reached JD risk handling, then login. No main product price was observed; **masked price was not independently observed in this run either**. No HTTP/mobile alternate, login action or subsequent JD detail was attempted. Evidence: `nav5.json`, `snapshot5.json`.

## Relevant exact links retained as discovery only

- [JD 9800X3D boxed, near-new listing](https://item.jd.com/product/1__5X77_64aLknp56wmtLQ.html): indexed title includes `准新品`, 9800X3D and boxed CPU. Do not label as new or infer an individual selected unit from the title.
- [JD 9800X3D loose-chip selection in a multi-model listing](https://item.jd.com/product/TuQ0Vv8e0VDQpeJM45lkSQ.html): title ends in `R7 9800X3D 散片`; other CPU alternatives remain in the title. Requires first-party selection/condition/warranty evidence.
- [JD PRIME-RTX5070TI-O16G lead](https://item.jd.com/product/RTXs_ERG96ADekuotKxBuA.html): title lists 5070 Ti, 5080 and 5090 alternatives. A title suffix is a lead, not proof of selected-SKU price.
- [JD RTX5070TI 16G OC factory-package lead](https://item.jd.com/product/5-_O5ycJszyORQABXsF86w.html): `工包` is a packaging qualifier; it does not independently establish new condition or full retail warranty.
- [JD returned/near-new black WH-1000XM6 lead](https://item.jd.com/product/399wNd61RTQZmizgSUo4nw.html): title includes `99成新` and `自营退货`; keep separate from new platinum-silver headphones. Government-subsidy text does not establish purchaser eligibility.
- [Goofish drone/controller search hit](https://www.goofish.com/item?categoryId=126866698&id=841111913335): indexed text mixes RC2/RC-N1 controllers, exchange-price wording and multiple drones. **Accessory/exchange-price risk only; main product not inspected.** Never price a complete Mini 4 Pro from this snippet.
- [JD WF-1000XM6 distractor](https://item.jd.com/product/BBa0--71FUeXt_WO15hx6Q.html): WF earbuds are not WH over-ear headphones. Its recommendations contain other headphones and unrelated prices.

These seven retained leads were not opened. All numeric snippets remain unranked. No direct Taobao product URL was found; none was guessed.

## Concrete pipeline findings at the captured revision

1. **Sold synonym missing, live reproduction.** Main DOM for item `1019398583977` contains `卖掉了`, but `import3.json` returns `availability:unknown`. The availability patterns in `china_deals/goofish_public.py:195` recognize `已售出|已卖出`, not this wording. Price still remains null; this is an availability-classification defect, not an observed false priced winner.
2. **Condition normalization loses native evidence, live reproduction.** `import1.json` preserves `轻微使用痕迹` but returns condition unknown; `import2.json` does the same for `几乎全新`; `import4.json` preserves `全新` yet also returns unknown. `goofish_public.py:205` only produces used or unknown, and its used regex misses the two common labels. `filters.py:74` also has a narrow exact condition vocabulary. Near-new must not become new; a new seller claim should remain explicitly a source claim. These gaps reduce strict-filter recall.
3. **The price binder is phone-specific, confirmed source limitation.** `_models` at `goofish_public.py:106` only recognizes phone-style two-digit Pro/Pro Max patterns. Consistency also demands storage. It cannot establish CPU, GPU, headphone or drone identity. All four imports correctly held numeric prices, but it would be wrong to interpret successful import/exit 0 as supported exact-product pricing.
4. **Capacity label/context mismatch, live evidence.** Item `982006970781` exposes `内存容量:64GB`, while the binder reads only `存储容量`; its capacity evidence contains 1T/2T from prose and omits the observed 64GB attribute. Conversely GPU 16G/24G/48G values enter the generic capacity set without a VRAM/storage distinction. These quantities need known product/category context before interpretation; do not globally alias every `内存容量` to SSD/RAM.
5. **All five new product intents are unsupported.** `offline-plans.json` records empty Chinese plan arrays and `requires_agent_translation:true` for all five already-Chinese queries. `products.py:20` only supports three earlier families; `assess_product` returns `unsupported_product_intent` before family-specific accessory logic. This is a coverage gap, not evidence the five product families are unavailable. Agent-supplied Chinese aliases still work as search input.
6. **Shipping normalization remains intentionally unresolved.** Main `包邮` badges survive in `source_detail.shipping_badges`, but `domestic_free_shipping:null` remains in both the drone and Deck import. Strict free-shipping filtering therefore cannot pass either from normalized fields. Preserve destination/conditional fulfillment uncertainty; do not convert a generic badge into international free shipping.
7. **Run-level gate persistence is outside the CLI.** `guest.access_session` and `cli.run` scope gates to one invocation. The live command correctly made one request and skipped two; a naive three-process market loop would forget the first challenge. External orchestration must retain this run's challenged surfaces. This run stopped both DuckDuckGo discovery and JD detail after their gates.

The connector's recommendation contamination was directly demonstrated by the older-CPU and 4090 pages. The existing primary-DOM boundary and null-price behavior prevented those amounts from becoming target prices. No application fixes were made here.

## Native-language query and filter guidance

These are suggested query refinements, not additional executed searches or manufacturer-spec claims:

- Steam Deck: retain `Steam Deck OLED 1TB 掌机`; distinguish `原装1T`, `512改1T`, `LCD`, `64G`, `裸机`, `预售`, `定金/订金`, case/dock/film (`保护壳/扩展坞/贴膜`). An upgraded LCD 1TB is not OLED 1TB. The word `掌机` alone also finds ROG Ally and other consoles.
- Sony: use `索尼 WH-1000XM6 头戴式 降噪耳机`, with spacing/hyphen variants. Keep `WH` versus `WF`, XM6 versus XM5, color and condition. `耳垫/头梁/耳罩/收纳包` require accessory-context review; do not exclude `头戴式耳机` because it contains a broad ear-related token.
- AMD: use `AMD 锐龙7 R7 9800X3D 处理器 CPU`; distinguish `散片/盒装`, `板U套装`, `整机/主机`, tuning services (`分核心负压/调试`), repairs and non-target 7800X3D/9850X3D. `散片` alone does not mean used.
- GPU: use `RTX 5070 Ti 16GB 独立显卡`; retain board maker and exact suffix. Chinese cooler names (`火神/魔龙/大师/星云`) are context-dependent series names, not proof of model/VRAM. Separate 5070 12G, 5070 Ti 16G, notebook GPUs, desktops, empty boxes and coolers. `工包/拆机/99新` need distinct condition/package interpretation.
- DJI: use `大疆 DJI Mini 4 Pro 无人机`; preserve `单机身/套装/畅飞`, `普通遥控器/带屏遥控器`, battery count, activation and repair state. `RC2`, `机臂`, `电池`, `置换价`, deposits and crashed units (`炸机`) cannot silently price a complete drone.

Alias inference requires explicit category, model and relevant hardware evidence. Source nicknames, title recommendations and SKU-family alternatives cannot fill unknown CPU/GPU/VRAM/storage/controller/package fields. Narrow per-product filters are preferable once a usable population exists; broad price bounds alone do not validate identity. There is no evidence here supporting a best-price ranking.

## Handoff

Private exact filenames: `cli-search.json`, `cli-search-receipt.json`, `cli-search.stderr.txt`; `connector-batch-1.json` through `connector-batch-4.json`; `discovery-ledger.json`; `capture1.json` through `capture4.json`; `import1.json` through `import4.json`; `normalized-imports.json`; `normalized-observations.json`; `offline-plans.json`; `capture-expression.js`; `nav5.json`, `snapshot5.json`, `browser-close.json`; version snapshots and `manifest.sha256`.

All four offline capture imports exited 0 with null exact prices. No tests were run. Five page navigations and twelve connector queries exhaust this run's budgets. The owned Incognito tab was closed and `browser-final-status.json` records no available tab. No source acquisition remains running. Root can review the retained normalization defects against its concurrent WIP; this report author did not change app code or tests. All 38 retained private files are under the owned directory, which Git ignores.
