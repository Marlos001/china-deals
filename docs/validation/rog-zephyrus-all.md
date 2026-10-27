# ROG Zephyrus family validation — 2026-10-27

## Result and scope

**Guest live search is access-blocked; no available deal, exact selected variant, or cheapest Zephyrus was established.** The clean baseline was `main`, commit `1a096f326da6b89e0b2b1732dcdc1eca0870e4bb`, CLI `0.3.0`. All **168 baseline tests passed**. Bounded offline examples reproduce accessory admission, cross-family grouping, negated-TGP extraction, AMD-name splitting, and extraction gaps beyond G16.

Owned files: this report and `.local/search-validation/zephyrus/` only. No application/test-suite edits, commit, push, login, account, cart, purchase, seller contact, or verification bypass. Peer changes appeared later in `cli.py`, `ranking.py`, `hardware.py`, `products.py`, and `tests/test_products.py`; they were preserved and are **not certified by the baseline test result**. `source-snapshot.json` records that later state. To remove timing ambiguity, the final reproductions and actual offline compare commands were rerun against 14 frozen baseline Python modules under the owned `baseline/` fixture directory, extracted from the exact commit above; `baseline-source-manifest.json` records their hashes. These are fixture copies, not implementation changes.

This is family-wide validation, **not an exhaustive inventory of models, generations, SKUs, sellers, or markets**. No year, condition, price, location, free-shipping, or hardware filter was imposed in live search. Artifact examples are synthetic unless explicitly marked as live CLI or ASUS browser evidence.

## ASUS-supported family boundary

Primary pages were read in a dedicated incognito T3 tab. ASUS supports the following broader scope; a G16-only search would miss it:

| Family | First-party evidence observed | Identity implications |
| --- | --- | --- |
| G14 | [ASUS laptop catalog](https://rog.asus.com/laptops-group/) names **ROG Zephyrus G14 (2026) GU405**, and its 2024 G14/G16 campaign | Do not assume every G14 has a GA prefix or AMD CPU. |
| G15 | [ROG Zephyrus G15 (2022)](https://rog.asus.com/laptops/rog-zephyrus/rog-zephyrus-g15-2022-series/) heading: **ROG Zephyrus G15 (2022) GA503** | Include older 15-inch family; not a G16 alias. |
| G16 | [ASUS Zephyrus series](https://rog.asus.com/laptops/rog-zephyrus-series/?items=20393) shows 2026 GU606 variants; M16 page also links 2023 GU603 and 2024 GA605 G16 | CPU/platform/year must remain separately observed; prefixes alone are not sufficient family proof. |
| M16 | [ROG Zephyrus M16 (2023)](https://rog.asus.com/laptops/rog-zephyrus/rog-zephyrus-m16-2023-series/) heading: **GU604**; S17 page also recommends **M16 GU603** | G16 and M16 can share a base prefix across generations. A 幻16 search is discovery, not unique G16 identity. |
| Duo | [ASUS catalog](https://rog.asus.com/laptops-group/) explicitly lists **ROG Zephyrus Duo (2026)** and links its article about **Duo 16**; M16 page recommends **Duo 16 (2023) GX650** | Dual-screen topology needs its own comparison treatment. |
| S17 | [ROG Zephyrus S17](https://rog.asus.com/laptops/rog-zephyrus/2021-rog-zephyrus-s17-series/) heading: **GX703** | Include older S-family listings when literal family identity is established. |

The ASUS catalog explicitly separates **ROG Flow**, **ROG Zephyrus**, and **ROG Strix**. Exclude Strix G16 and Flow X13/X16/Z13 from a Zephyrus population; TUF and compatible chargers, sleeves, panels, batteries, or parts are also outside the requested whole-laptop population. A number such as G16, an ASUS brand mention, or a compatible model code is insufficient.

Two additional legacy routes attempted for Zephyrus M/GM501 and M15 returned ASUS's “The page you’re looking for can’t be found.” They do **not** establish absence or valid family coverage. M15, S15, original Zephyrus/G/M/S variants, special editions, and additional historical models remain a source-verification gap. The synthetic GM501 parser example below tests regex scope only; it is not a verified SKU specification. ASUS's catalog count of 206 products is not a count of marketplace offers or distinct families. Current catalog “up to” specifications are not selected-SKU evidence.

Retained primary evidence: `asus-catalog-browser.json`, `asus-series-browser.json`, `asus-g15-browser.json`, `asus-m16-browser.json`, `asus-s17-browser.json`. These are **DOM text records, not screenshots**. M16/S17 records deliberately bound body text and retain title/headings; no claim relies on an omitted section.

## Commands and live results

Ran workflow, CLI version/help/schema/config checks, then this actual command from the repository:

```sh
python -m china_deals search 'ASUS ROG Zephyrus' \
  --zh-query '华硕 ROG 幻系列' --query-for 'blibli=ASUS ROG Zephyrus' \
  --markets taobao,jd,goofish,blibli --limit 5 --access guest \
  --guest-engine http --include-offers --currency native --timeout 20
```

Started **2026-10-27T15:54:01Z**, exited **3**, took **3.52 seconds**. Exact argv/timing/exit are in `01-broad.command.json`; complete JSON in `01-broad.json`; stderr was empty. `--currency native` avoids an unrelated FX request and preserves CNY versus IDR. Explicit guest mode prevents configured native-session use.

| Market | Actual route/result | Offers and price evidence |
| --- | --- | --- |
| Taobao | DuckDuckGo `site:item.taobao.com 华硕 ROG 幻系列`; `blocked/challenge` | 0 returned; native marketplace inventory unknown |
| JD | DuckDuckGo `site:item.jd.com 华硕 ROG 幻系列`; `blocked/challenge` | 0 returned; no primary price/variant/condition/stock read |
| Goofish | DuckDuckGo `site:www.goofish.com 华硕 ROG 幻系列`; `blocked/challenge` | 0 returned; no assertion that Zephyrus is absent |
| Blibli | Public `/backend/search/products?searchTerm=ASUS+ROG+Zephyrus...` → HTTP 403, then DuckDuckGo index fallback → challenge | 0 returned; no IDR price or selected available variant established |

The three Chinese-market HTTP searches use an external index, not native marketplace search. The CLI's constructed `native_search_url` is **not an executed request**. Every source reported `source_mode=search_index`, `coverage=discovery_only`, with no filters requested/submitted. Root-level `coverage=observed_results_only` must not hide source-level blocking.

**Challenge stop:** no further live requests to the challenged routes. The CLI itself continued serially through all requested markets, sending four separate DDG requests despite the first challenge; a shared index-host challenge stop would avoid redundant attempts within one command. This is not a successful retry or bypass.

The two specific variations were exercised through the real CLI dispatcher **offline**, with copied adapter responses and networking forbidden:

1. `ASUS ROG Zephyrus G14` + `--zh-query '华硕 ROG 幻14'`, all four markets.
2. `ASUS ROG Zephyrus M16` + `--zh-query '华硕 ROG 幻15'` + `--query-for 'jd=华硕 ROG 幻16'`, all four markets.

Both dispatch tests exit 3, record four correct adapter calls, preserve Blibli's English query, and use no optional filters. They verify query routing only; **the two specific live searches remain unperformed** because of the access challenge. These are sensible alternative leads, not evidence that 幻14/幻15/幻16 uniquely identifies a family or generation. The broad phrase 幻系列 is not proof of all-model recall.

An additional offline English-only JD query returns `chinese_query_required`, exit 3, and **zero adapter calls**. This is the documented query gate working as designed, not a network failure. Model-only English input cannot establish marketplace absence; supply the Chinese query/override. The gate tests for a Chinese character, not translation quality or family membership. Evidence: `offline-query-dispatch.json`.

## Browser checks and budget

Called `preview_status`, then `preview_open(reuseExistingTab=false, profileId="incognito", open=false)`. Owned tab: `tab_t_4cac2679-3846-4860-a3d7-8c794cdb6e4b`; all later preview calls used this exact ID. No peer tab was operated.

A separate primary-source discovery query, `site:rog.asus.com Zephyrus G14 G15 G16 M16 Duo S17`, redirected Google to `/sorry/index`; stopped there. Direct ASUS navigation subsequently established the family evidence above; **it supplied no marketplace results**. The attempted ASUS category `/laptops/rog-zephyrus/` returned 404; the working navigation was `/laptops-group/` → `/laptops/rog-zephyrus-series/?items=20393`.

**Zero marketplace product opens:** the CLI returned no exact product links to validate. No prior G16 URL, independently found listing, or invented URL was substituted. Five ASUS product-route opens total: G15, M16, S17, and the two not-found legacy routes. No further products opened. Total live targeted queries: four marketplace queries in one CLI call, plus one Google query; within the 14-query cap. The nine simulated dispatch/gate queries made no requests. `browser-ledger.json` retains the access/budget record.

Fresh CLI browser search was **not run**: its implementation uses Google, where this fresh incognito check already encountered verification. There was no exact returned listing for useful browser detail hydration. Switching transport to retry the challenged index would not validate guest access. Optional browser mode therefore remains untested in this run, rather than passed or broken.

## Reproducible offline findings for root

All reproductions are synthetic, use no accounts/network, and preserve literal inputs/outputs in the owned evidence directory. Final runs use the frozen baseline package, irrespective of concurrent root fixes. These findings are not claims about current live listings or the latest working tree.

```sh
PYTHONDONTWRITEBYTECODE=1 python .local/search-validation/zephyrus/reproduce.py
cd /home/marlos/projects/china-deals/.local/search-validation/zephyrus/baseline
PYTHONDONTWRITEBYTECODE=1 python -m china_deals compare ../synthetic-cross-family-input.json --currency native
PYTHONDONTWRITEBYTECODE=1 python -m china_deals compare ../synthetic-accessory-input.json --currency native
PYTHONDONTWRITEBYTECODE=1 python -m china_deals compare ../synthetic-negation-input.json --currency native
```

All three offline compare commands exit 0 and each produces one group; exact executed absolute argv/cwd are in `offline-cli-command-receipts.json`. The repro script itself selects `baseline/` explicitly and cannot silently import root's changed package.

| Finding | Minimal observed failure | Root-owned fix suggestion |
| --- | --- | --- |
| **High: accessory becomes laptop candidate** | “Replacement charger compatible with ASUS ROG Zephyrus G16 GU605MI” followed by complete copied laptop specs, price 100, yields one group and `cheapest_candidate_ids=[synthetic-charger]`. `cli-accessory-output.json` confirms actual compare CLI behavior. | Add conservative whole-product/compatibility/accessory evidence before ranking/comparison. Current `models.py` accessory words omit charger/adapter and only inspect title; descriptions and product role need bounded treatment. |
| **High: family/dual-screen identity is absent from equivalence** | Five synthetic titles—Zephyrus G16, Strix G16, Flow X16, TUF F16, Zephyrus Duo 16—with identical supported hardware text become **one group**. Cheapest ID is the synthetic Duo. `cli-cross-family-output.json` retains actual CLI output. | Filter/partition the requested family before comparison; represent product form and secondary displays. `COMPARISON_FIELDS` excludes code/year and has no family. Hardware-vector equality must not imply same product/model. Preserve generic hardware comparisons as an explicitly weaker comparison if desired. |
| **High: negated TGP becomes positive fact** | Replace `TGP 105W` with `not TGP 105W` in an otherwise complete offer: extractor returns `gpu_tgp_w=105`; comparator still forms one complete group. | Apply negation handling consistently to TGP, VRAM, resolution, refresh and size evidence. Existing CPU/GPU negation checks do not cover all fields. Retain the literal negated span as unresolved, not supported power. |
| **Medium: AMD GPU name splits equivalent literal hardware** | Identical G14 synthetic offers differing only by `Radeon RX 6700S` versus `AMD Radeon RX 6700S` produce **two groups**. | Normalize optional vendor prefix while retaining source spans; do not infer GPU suffix, mobile scope, VRAM or TGP. See `synthetic-amd-alias-{input,output}.json`. |
| **Medium: broader family year extraction is G16-biased** | Fully spelled G14 2022, G15 2021, M16 2023 and S17 2021 examples extract CPU/GPU/etc. but `model_year=null`; G16 is specially included in `_PRODUCT`. | Broaden literal family/year identity grammar without deriving missing specs from year or code. |
| **Medium: Chinese and ASUS typography lose literal facts** | `华硕ROG幻14GA402RJ笔记本 R9-6900HS RX6700S 8G显存 内存16GB 固态1TB ...` misses CPU/GPU/VRAM/code. ASUS catalog-style `Intel® Core™ Ultra 9 Processor 386H` and `RTX™ 5060` also remain unknown. | Add evidence-preserving aliases/tokenization for Chinese boundaries, R9/RX shorthand, trademark marks and `Processor`; never guess fields from family. |
| **Medium: equivalent display labels conflict** | ASUS-style `2.5K (2560 x 1600, WQXGA)` yields three conflicting resolution values and null resolution. | Recognize explicit parenthetical aliases around observed pixel dimensions. Do not globally equate ambiguous marketing K labels to a pixel size. |
| **Coverage: legacy codes and multi-display forms** | `GM501GS` is outside `G[AUWX]...`; Max-Q has no dedicated field; only one resolution/refresh/size set exists. | Source-validate additional model grammars; capture dual-screen observations separately. Unverified legacy inputs here are parser examples only. |

Supporting locations at baseline: `hardware.py:21` comparison fields, `:25` product grammar, `:81` CPU, `:99` GPU, `:136` VRAM, `:139` TGP, `:189` display, `:202` codes, `:206` years, `:370` accessory guard, `:377` grouping key; `models.py:214` accessory vocabulary; `guest.py:225` guest search; `browser_guest.py:189` browser index search. The graph project `china-deals` was selected by exact root, project-list pagination completed, and symbol searches/snippets used first. A clipped graph snippet was followed by a focused source read; graph output was not treated as complete evidence.

## Coverage that works, limits that remain

Explicit labeled CPU, RTX/GTX or spelled Radeon GPU, mobile scope, VRAM, TGP, RAM, SSD, pixel dimensions, refresh, display technology/size and condition work on the canonical G14/G15/M16/S17 examples in `extraction-cases.json`. Missing TGP is correctly unknown. Unlabeled capacity and model numbers do not invent RAM. Different literal TGP/VRAM/display/condition stay separate under the baseline suite.

`price-controls-output.json` confirms masked, source-marked unavailable, and search-index numeric prices create **zero comparison groups**. These protections passed, but they do not replace live selected-variant/stock verification. No primary marketplace price, selected variant, seller, condition or availability was obtained in this run; no stockout or masked amount is presented as a deal. No new Blibli freight route or cross-currency winner is asserted.

Baseline verification command: `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v`; 168 tests in 0.397s, OK (`baseline-tests.log`). The offline artifact script exits 0 and verifies price controls, dispatch overrides, no-network query gate and reproductions. The commands above are ready for root to turn into focused regression tests after choosing behavior. Root's later WIP and any future fixes need their own checks; no changes were made to those files.

Unresolved: live specific-query searches; exact returned product-link validation; primary listing SKU/price/condition/stock; additional historical-family primary sources; secondary-screen comparison; optional browser CLI runtime. There are no running validation subprocesses. Root can review the owned reproductions and apply fixes without repeating blocked marketplace calls.
