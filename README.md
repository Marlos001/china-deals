# china-deals

A read-only **0.6 CLI** for researching products on **Taobao, JD.com, Goofish/Xianyu and Blibli**, comparing observed configurations and prices, and estimating **Fansbuy → Brazil** freight and landed costs.

**Guest access is the default. No marketplace account or AI API credentials are required.** Your subscription-backed Codex, Claude Code, Gemini/AGY or other terminal-capable agent supplies translation, analysis and presentation. The CLI makes no LLM calls. Existing OpenCLI sessions are an explicit, optional native mode.

Guest mode does not guarantee accessible search or visible prices. In the [retained live research](docs/research/zephyrus-g16-test.md), JD detail showed a masked price, Blibli returned HTTP 403 / a verification page, and Goofish native guest search produced no verified target results; a readable Goofish item was delisted. These observations do not establish global restrictions or absence of inventory. Search-index leads are discovery evidence, never current purchasable offers.

## Fresh prices and import versus Brazil (0.6)

Use `refresh` to re-read exact native product URLs, optionally retain SQLite observation history with `--store`, and use `--fresh-only --max-age-hours 1` to exclude stale prices. Cached sources never become fresh from today's retrieval time; blocked/masked refreshes retain no current numeric price. `promotions` reads fresh public promotional evidence for your agent to interpret. Coupon evaluation now requires recent primary evidence and a current explicit campaign window by default, plus the real purchasing account's conditions.

`brazil-compare` compares equivalent product/condition/configuration scenarios with all applicable freight, taxes and fees. Unknown costs remain unknown; incomplete scenarios show a conditional remaining-cost budget instead of verified savings. Blibli international freight follows its configurable exclusion policy. [Full fresh-data workflow, commands and limits](docs/FRESH_DATA.md).

## Install and start

Requires Python 3.11+. The HTTP guest core has no runtime dependencies:

```sh
uv tool install git+https://github.com/Marlos001/china-deals.git
# Alternative, in a virtual environment:
pip install git+https://github.com/Marlos001/china-deals.git
china-deals --version
china-deals schema
china-deals config show
```

Start with the [agent guide](docs/AGENT_GUIDE.md). For example, ask your agent:

> Use china-deals in guest mode to research a ROG Zephyrus G16. Translate Chinese marketplace queries, inspect exact source listings and separate configurations, missing evidence and blocked sources. Show dated BRL product estimates, exclude Blibli freight, and estimate China-origin Fansbuy costs only with suitable parcel and import assumptions. Do not select a winner from search snippets. Ask before any purchase.

The CLI accepts keywords rather than conversational prompts. The external agent chooses and translates successive queries.

## Search, detail and the Chinese query gate

Taobao, JD and Goofish require a query containing Chinese characters. Supply the Chinese query directly, use `--zh-query` for all selected Chinese marketplaces, or repeat `--query-for MARKET=QUERY` to override individual sources. A per-market override takes precedence. Without a Chinese query, that source returns `chinese_query_required` and sends no marketplace search request. Brand/model names alone do not pass the gate.

```sh
china-deals search 'ROG Zephyrus G16' --zh-query '华硕 ROG 幻16 笔记本' \
  --markets taobao,jd,goofish --limit 5

china-deals search 'ROG Zephyrus G16' --markets jd,blibli \
  --query-for 'jd=华硕 幻16 笔记本' \
  --query-for 'blibli=laptop ASUS ROG Zephyrus G16' --limit 5

china-deals search '华硕 幻16 笔记本' --markets jd --hydrate 2 \
  --include-offers > search.json
china-deals detail jd 100214660452
```

`--hydrate N` attempts guest detail for up to N discovered links per source. Its `hydration` receipts retain target URLs, access attempts and failures; successful reads preserve the original discovery under `source_detail.discovery`. A failed detail read leaves the indexed lead unverified, and a challenge stops remaining detail attempts for that source. The JD ID above is a research example with a previously masked price, not a recommended offer. `xianyu` aliases `goofish`. Blibli is **Indonesia**, distinct from Bilibili.

JSON is the default. `--format markdown` gives a compact report; use JSON to inspect full provenance, FX, filter plans and unknown fields. `--include-offers` retains the full fetched offer population for later offline filtering and comparison. Without it, ranked groups may be limited. Calls run serially.

Results retain source links, raw displayed prices, native currencies, observation times, access attempts and warnings. Read every source status: `discovery_only`, `blocked`, `auth_required`, `unavailable`, `empty_unverified` and `error` describe evidence or access limits. An empty response does not prove no inventory. Recommendations are not verified keyword matches.

**All search-index prices remain unranked**, even when a snippet contains a numeric amount. Masked, ranged, page-minimum and unbound amounts also cannot establish an exact SKU price. A retrieved product page may improve evidence; it does not by itself verify stock, checkout, seller authenticity or discounts.

## Product-aware search plans and validation

```sh
china-deals plan 'iPhone 17 Pro Max'
china-deals plan 'AirPods Max USB-C'
china-deals plan 'ASUS ROG Zephyrus'
china-deals search 'iPhone 17 Pro Max' --zh-query '苹果 iPhone 17 Pro Max 手机' \
  --limit 5 --include-offers > iphone.json
china-deals rank iphone.json --query 'iPhone 17 Pro Max'
```

`plan` is offline. It suggests bounded Chinese-market and Blibli queries for iPhone 17 Pro Max, AirPods Max and Zephyrus G14/G15/G16/M16/Duo/S17 families. Refined queries retain model, storage and connector terms; your subscription agent can improve the translations and execute selected queries. Plans do not run searches or claim exhaustive coverage.

For these recognized families, ranking checks title and selected variant independently. Accessories, repair/replica/dummy listings, explicit different products and uncertain model matches stay unranked; deposit and monthly-payment amounts stay unknown. This is conservative relevance checking, not authenticity or performance verification. `intent_query` survives imported rank/coupon/compare workflows. Use `rank --query` to attach intent to a plain imported array. Read all unranked reasons instead of assuming a low displayed amount is the whole device price.

Verification/login/HTTP 401/403/429 responses gate further requests to the same host during one command. `access.attempts` names the actual index or marketplace host and records `skipped_after_challenge`, `network_attempted: false` and the origin. Independent hosts can still be read; a new invocation has a fresh scope. A blocked index does not prove the marketplace itself requires login. Opaque JD product URLs remain unpriced discovery with an unresolved numeric SKU.

The [three-product validation summary](docs/validation/README.md) links real CLI/browser checks and the resulting regressions. Guest access was blocked in these bounded searches; no current best-deal winner was verified.

## Useful observations when a native page is blocked

```sh
china-deals catalog taobao 982744194230
china-deals rank examples/deeper-candidates-2026-10-27.json \
  --fx-from-json examples/fx-reference-2026-10-27.json --format markdown
```

`catalog` performs an optional, account-free Jadeship read for an exact Taobao item. It returns a **third-party catalog observation**, including a separate BRL product reference. Its underlying freshness, variant, stock, condition and coupon eligibility remain unknown; normal `price.amount` remains null. Jadeship coverage is not Taobao catalog coverage, and the example phone is not a verified 1 TB/new-device quote.

Cached exact-product claims can also remain useful: unranked Markdown shows their source amount, separate BRL reference and crawl age when retained. Proxy, cached-product, indexed-product-block and category-card modes cannot become current-price rankings by re-importing. The [deeper validation results](docs/validation/deeper-results.md) contain two freshly rendered Goofish phone candidates, four cached Blibli candidates and external laptop price context, with condition/repair/pickup limits and dated FX. No additional coupon or checkout eligibility was established.

For Goofish, `detail --from-browser-json` can import a retained primary-DOM browser capture without another network request. The requested/final item ID and bounded main-item selectors must agree; recommendations cannot supply prices. Capture authenticity and observation time remain caller-supplied. See the agent guide for the capture contract and current browser-reader limits.

## Optional filters: native submission versus local checks

No price, condition, location or free-shipping restriction is imposed when omitted. Available options include `--min-price`, `--max-price`, `--sort relevance|price-asc|price-desc|sales|newest`, `--condition any|new|used|refurbished`, `--province`, `--city` and `--free-shipping`.

```sh
china-deals filters goofish '华硕 幻16' --max-price 12000 --city 深圳
china-deals search '华硕 幻16' --markets goofish --max-price 12000 \
  --condition new --city 深圳 --free-shipping --strict-filters
```

Price bounds use each marketplace's **native currency**: CNY for China, IDR for Blibli. A shared numeric bound across both currencies is usually inappropriate. `--free-shipping` means seller domestic postage, never international freight.

`filters` explains documented parameters and a proposed native request. A constructed URL is not proof of applied facets. Check each source's `filter_plan`, especially `submitted_native_filters` and `unverified_or_local_filters`, and each offer's `filter_evaluation`. Local checks use only returned fields. Unknown requested attributes remain unknown; `--strict-filters` excludes those candidates. Indexed discovery does not implement native marketplace facets. Requested sales/newest ordering is unverified unless the source confirms native submission; local displayed-price ordering does not establish it.

## Per-market preferences and BRL reference estimates

```sh
china-deals config show
china-deals config init
# Choose another file explicitly:
china-deals config init --config ./preferences.json
china-deals search '华硕 幻16' --markets jd --config ./preferences.json
```

`config init` creates an editable file and refuses to overwrite an existing one. The default path is `$XDG_CONFIG_HOME/china-deals/config.json` or `~/.config/china-deals/config.json`; `CHINA_DEALS_CONFIG` and command-specific `--config` can select another path. Built-in preferences apply when no default file exists:

```json
{
  "schema_version": 1,
  "display_currency": "BRL",
  "marketplaces": {
    "taobao": {"access": "guest", "shipping": "fansbuy", "currency": "CNY"},
    "jd": {"access": "guest", "shipping": "fansbuy", "currency": "CNY"},
    "goofish": {"access": "guest", "shipping": "fansbuy", "currency": "CNY"},
    "blibli": {"access": "guest", "shipping": "excluded", "currency": "IDR"}
  }
}
```

Access and shipping preferences are per marketplace. Shipping can be `fansbuy`, `excluded` or `manual`; the config rejects Fansbuy routing for Blibli. Native currencies cannot be changed by configuration. Blibli's default excludes freight: the CLI assumes no Indonesia → China/Fansbuy or Indonesia → Brazil route.

Search, detail, rank and compare default to dated **BRL product-cost estimates** using public ECB reference cross-rates. Native amounts remain preserved and price groups stay currency-local.

```sh
china-deals fx > fx.json
china-deals rank search.json --fx-from-json fx.json
china-deals compare search.json --fx-from-json fx.json --min-ram-gb 32 --min-ssd-gb 1024
china-deals rank search.json --currency native
```

Report `rate_date` and source, not just retrieval time. ECB reference rates are not payment rates or customs PTAX; spread, fees and IOF are excluded. `--fx-from-json` supplies a saved snapshot instead of a network fetch, with caller-supplied provenance. If conversion fails, native prices remain with a warning. Product BRL annotations do not include freight or tax and do not create a cross-currency best deal.

## Compare hardware without inventing equivalence

`compare` extracts literal hardware observations and evidence spans. It separates complete exact configuration/currency `groups` from `incomplete`, `unranked`, `filtered`, `requirement_unknown` and `discoveries`. Unknown specifications and conflicting alternatives are not matches.

```sh
china-deals compare search.json --min-ram-gb 32 --min-ssd-gb 1024 --new-only
china-deals compare search.json --gpu 'RTX 4060' --currency native
```

A complete group requires observed CPU, GPU and laptop/desktop scope, VRAM, GPU power (TGP), RAM, SSD, display resolution, refresh rate, technology, size and condition. Model code/year alone cannot fill missing specifications. Similar names such as “G16” do not establish the same generation, panel or performance. Only eligible exact source prices can identify the cheapest observed candidates **within one complete configuration and native currency**; ties remain visible. Search-index records stay discoveries, not winners. Seller claims remain claims, and even a complete group does not prove current availability or checkout cost.

An optional `compare --freight-cny AMOUNT --icms-rate RATE --fx-from-json fx.json` adds a China landed-cost scenario for markets configured for Fansbuy. Supply actual parcel freight and applicable tax assumptions; it does not add Blibli freight or change hardware equivalence.

## Optional fresh guest browser

The default `--guest-engine http` needs no browser. `search` and `detail` also support `--guest-engine browser`, using optional Playwright and a **fresh ephemeral Chromium context**. It loads no saved cookies or user profile and closes its temporary session. It stops at login, CAPTCHA, risk or verification challenges without retrying or bypassing them. A browser is another guest transport, not a promise of unblocked access.

From a checkout, in a virtual environment:

```sh
pip install '.[browser]'
china-deals search '华硕 幻16' --markets jd --guest-engine browser \
  --browser-executable /usr/bin/chromium
china-deals detail jd 100214660452 --guest-engine browser \
  --browser-executable /usr/bin/chromium
```

The default executable is `/usr/bin/chromium`. To use Playwright's downloaded Chromium instead, run `python -m playwright install chromium`, find its executable with the command below, and pass that absolute path to `--browser-executable`:

```sh
python -c 'from playwright.sync_api import sync_playwright; p = sync_playwright().start(); print(p.chromium.executable_path); p.stop()'
```

Browser search reads indexed discovery, not a native marketplace catalog. The current browser detail backend can attempt SKU-bound JD/Blibli extraction and bounded Goofish primary DOM with phone-style model/storage reconciliation. Taobao has no validated primary-item detail contract. Fresh T3 capture plus CLI ingestion was verified for Goofish; live CLI browser transport remains unverified. The [browser backend report](docs/research/browser-guest.md) records these limits and the local smoke check that stopped at a challenge.

## Optional OpenCLI native sessions

Choose `--access native` explicitly, or set that marketplace's config preference to `native`, only when you want to use an existing OpenCLI browser session. **OpenCLI, Node.js, Browser Bridge and marketplace login are not prerequisites for default guest use.**

Native China adapters compose [OpenCLI](https://github.com/jackwener/OpenCLI) **2.0.2** as an external executable. Its setup requires Node.js 20.18.1+ and Chrome with the [OpenCLI Browser Bridge](https://github.com/jackwener/OpenCLI/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/docs/guide/browser-bridge.md):

```sh
npm install --prefix "$HOME/.local/share/china-deals/backend" --ignore-scripts --save-exact @jackwener/opencli@2.0.2
export CHINA_DEALS_OPENCLI="$HOME/.local/share/china-deals/backend/node_modules/.bin/opencli"
china-deals doctor
china-deals doctor --live
china-deals search '华硕 幻16' --markets jd --access native --limit 5
```

`--ignore-scripts` skips upstream automatic setup/adapter refresh. Install the bridge yourself and manage any login/verification in your browser. `doctor` diagnoses this optional backend; missing native setup does not prevent HTTP guest use. `--opencli /path/to/opencli` overrides the executable, otherwise the CLI checks the environment, PATH and default XDG data location.

Blibli native search can explicitly permit session reuse after public API denial with `--access native --browser-fallback`; native Blibli detail also needs that fallback flag and a validated product URL. This is separate from the fresh guest browser engine. Live Blibli product extraction remains unverified. Taobao/JD native detail retains raw source fields while unverified page amounts stay unranked. No CLI mode imports user cookies, solves CAPTCHAs or installs extensions.

## Fansbuy → Brazil and truthful declarations

Use China-origin parcel data and every applicable category:

```sh
# Only use --ordinary-goods when no special categories apply.
china-deals shipping --market jd --weight-g 1000 --dimensions-cm 20 20 15 \
  --ordinary-goods --format markdown

# Confirm electronics/battery/brand classification with Fansbuy.
china-deals shipping --market taobao --weight-g 1500 --dimensions-cm 30 20 15 \
  --category Electric --category Brand

# Default Blibli policy returns excluded_by_market_policy without requesting freight.
china-deals shipping --market blibli
```

Weight is **packed grams**, dimensions centimetres. Calculator categories are `Electric`, `Brand`, `liquid`, `bag`, `food`, `shoes`, `Battery`, `Knives`, `powder`, `watch`, `cosmetics`, `magnetic`, `perfume`. Fansbuy's `Electric` and `Battery` flags are separate; do not omit an applicable flag. Omitted categories leave eligibility unresolved. Disabled, incompatible, overweight and oversize routes remain under `rejected`; missing dimensions may prevent eligibility checks.

Quotes are live public-calculator **base CNY estimates**. Coupon discounts stay conditional and delivery windows are carrier estimates. Final packing, insurance, remote fees, clearance and Brazil taxes remain separate.

```sh
# Illustrative assumptions only; replace with applicable values.
china-deals estimate --goods-cny 300 --freight-cny 168.75 \
  --cny-brl 0.75 --usd-brl 5.40 --icms-rate 0.20 \
  --domestic-cny 10 --agent-fee-cny 0 --insurance-cny 0
china-deals restrictions --condition used --category Electric --ncm 84713012
```

The default indicative RTS calculation assumes non-Remessa Conforme treatment: 60% federal duty on assumed customs value, then ICMS *por dentro*. Domestic freight is included; buying-agent fees have an explicit valuation caveat. FX and ICMS are required; values above the USD 3,000 RTS ceiling are rejected.

The [2026-10-27 policy research](docs/research/shipping-brazil.md) records qualifying PRC natural-person DIR rules effective 2026-05-12: 0% federal duty through USD50 and 60% less USD30 above it. `--remessa-conforme` is your assertion of separately confirmed eligibility, not verification of retailer, recipient or declaration. A shopping agent does not establish PRC eligibility. Recheck current official rules before relying on an estimate.

Use a **truthful, specific customs description and the actual transaction value** with supporting records. Never recommend a reduced declared value, invented gift status, false description or omitted batteries/brands to lower charges or evade restrictions. This CLI does not submit customs declarations.

`restrictions` returns checks, never legal clearance. Used goods, batteries, liquids, wireless equipment and other regulated categories need case-specific confirmation. Carrier acceptance is not import permission. Sea/container shipping does not make a prohibited import legal, and a missing air quote does not prove a sea-only legal requirement.

## Offline data, automation and validation

```sh
china-deals rank examples/synthetic-offers.json --currency native --format markdown
china-deals shipping --from-json tests/fixtures/fansbuy-estimates-2026-10-27.json \
  --weight-g 1000 --dimensions-cm 20 20 15 --ordinary-goods
```

Captured freight input must bind the response to matching destination, package, categories and timestamp metadata; bare responses are refused. Caller-supplied metadata does not establish authenticity or current pricing. Offline offers preserve unknown observation times; bundled product offers are **synthetic**, not live deals. JSON input is bounded to 4 MiB.

Exit codes: `0` command completed (inspect warnings); `2` invalid input/command failure; `3` partial, discovery-only, blocked, unavailable or unverified-empty marketplace coverage. Preserve usable evidence and report each failed source rather than turning an empty result into “not sold.”

See [validation](docs/VALIDATION.md) for checks and their limits, and these reports for retained evidence:

- [Guest access and native filter research](docs/research/guest-access.md).
- [Optional browser backend and verification limits](docs/research/browser-guest.md).
- [Zephyrus G16 Blibli findings](docs/research/zephyrus-g16-blibli.md) and [verification notes](docs/research/zephyrus-g16-test.md).
- [Research index](docs/research/README.md), including frameworks, marketplaces, Blibli and Brazil policy sources.
- [Third-party notices](THIRD_PARTY.md).

For development:

```sh
git clone https://github.com/Marlos001/china-deals.git
cd china-deals
uv run python -m unittest discover -s tests -v
uv run china-deals schema
```

Fixture/mocked checks do not prove live marketplace access. No order, cart change, seller message, payment or shipment-submission commands are exposed. Keep credentials, profiles, private captures and product research out of Git. Respect marketplace terms and verification controls.

A subscription agent can invoke this CLI directly; an MCP wrapper is optional and neither protocol inherently guarantees lower token use or requires paid AI APIs. MIT licensed.


### Coupons and newer G16 evidence (0.3)

The CLI evaluates imported coupon rules with `coupons` or `--coupons-from-json` on `search`, `detail`, `rank` and `compare`. It does not claim or redeem vouchers, and does not automatically discover every current campaign. Your subscription agent supplies source-linked rules after reading the actual terms.

```sh
china-deals coupons examples/g16-user-observations-2026-10-27.json \
  --rules examples/blibli-coupons-research-2026-10-27.json
```

`campaigns` supports a fixed amount or percentage, caps, minimum spend, marketplace/product/seller scope, dates, and explicit `requires` context for the actual purchasing account, payment method, app/member status or quota. `best_eligible` means eligible **under caller-supplied assertions**, not live checkout proof. Unknown facts produce `potential`; contradicting facts produce `ineligible`. Cashback stays separate from amount payable. Coupons are independent alternatives; stacking is not assumed. The original listing price never changes, so its sale percentage is not deducted twice. BRL fields use the same dated reference FX snapshot.

The [example coupon schema](examples/coupons.example.json) is synthetic. The [Blibli research rules](examples/blibli-coupons-research-2026-10-27.json) are real promotional leads with **unverified applicability**, not promised discounts. Some displayed prices may already incorporate a voucher. Rules must follow the purchasing account: the customer's personal entitlement is not automatically transferable to Fansbuy or another purchasing agent.

The [updated Blibli report](docs/research/zephyrus-g16-blibli-v2.md) records the user's newer prices, full configuration claims and screenshots. The selected AMD 5060 variant is out of stock in the supplied screenshot. The [second Goofish search](docs/research/zephyrus-g16-goofish-v2.md) and [expanded access-solution review](docs/research/access-solutions-v2.md) document broader searches, extensions, public endpoints and buying-agent alternatives; no newly available Goofish G16 or working universal account-free access path was established.
