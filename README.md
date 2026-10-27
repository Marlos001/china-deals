# china-deals

A read-only CLI for subscription-backed AI agents to research products on **Taobao, JD.com, Goofish/Xianyu and Blibli**, compare observed prices, and request **Fansbuy → Brazil** shipping estimates.

Your Codex, Claude Code, Gemini/AGY or other terminal-capable agent does the reasoning and translation using your existing subscription. This CLI makes **no LLM calls** and needs **no AI API key**. Marketplace accounts and browser verification can still be required.

**Early release:** Fansbuy's public calculator was tested live. Marketplace adapters require a working browser session; authenticated search coverage is not yet established by this project's tests. Blibli returned an access challenge from the development environment. A working JSON adapter is not a promise of uninterrupted access or complete marketplace coverage.

## Install

Requires Python 3.11+. Install the CLI:

```sh
uv tool install git+https://github.com/Marlos001/china-deals.git
# Alternative, in a virtual environment:
pip install git+https://github.com/Marlos001/china-deals.git
china-deals schema
```

China marketplace access reuses [OpenCLI](https://github.com/jackwener/OpenCLI) **2.0.2** rather than duplicating its adapters. Requires Node.js 20.18.1+ and Chrome with the [OpenCLI Browser Bridge](https://github.com/jackwener/OpenCLI/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/docs/guide/browser-bridge.md). Install the pinned CLI in a directory you control:

```sh
npm install --prefix "$HOME/.local/share/china-deals/backend" --ignore-scripts --save-exact @jackwener/opencli@2.0.2
export CHINA_DEALS_OPENCLI="$HOME/.local/share/china-deals/backend/node_modules/.bin/opencli"
china-deals doctor
```

`--ignore-scripts` skips upstream automatic setup and adapter refresh scripts; the pinned package ships adapters. Install the Browser Bridge yourself, then sign into the marketplaces in Chrome. Complete login/security checks in the browser. This CLI does not import cookies, solve CAPTCHAs, change your browser settings or install extensions.

The CLI also auto-detects this backend under the default XDG data directory if no executable or environment override is supplied.

```sh
china-deals doctor --live
```

The Python CLI has no runtime dependencies. Fansbuy quotes, offline ranking and landed-cost calculations work without OpenCLI.

## Use with your agent

Give your agent [docs/AGENT_GUIDE.md](docs/AGENT_GUIDE.md), or tell it:

> Use `china-deals` to find a Keychron K8 Pro with the layout and switches I specify. Search in the relevant marketplace languages, inspect the shortlisted items, and present comparable offers with source links and all unknowns. For China-origin items, estimate Fansbuy shipping to Brazil when packed weight, dimensions and category are known. Calculate the BRL cost with explicit FX and tax assumptions. Ask before any purchase.

The CLI accepts search keywords, not a built-in conversational prompt. Your agent translates and chooses successive commands. Use different queries for Chinese marketplaces and Blibli Indonesia:

```sh
china-deals search 'Keychron K8 Pro' --markets taobao,jd,goofish --limit 5
china-deals search 'keyboard Keychron K8 Pro' --markets blibli --limit 5
china-deals detail goofish ITEM_ID
china-deals detail blibli 'https://www.blibli.com/p/PRODUCT/ps--PRODUCT-CODE' --browser-fallback
china-deals search 'Keychron K8 Pro' --markets jd --require-term 'K8' --format markdown
```

JSON is the default. `--format markdown` produces a compact human report. Source summaries avoid repeating listing arrays; use `--include-offers` to retain the full fetched population for offline filtering, at the cost of larger output. `xianyu` is an alias for `goofish`. `--opencli /path/to/opencli` overrides the backend. Searches run serially to avoid browser-session races.

Blibli's `--browser-fallback` explicitly permits reuse of your OpenCLI browser after a public API denial. Its current product-extraction behavior is unverified. Taobao/JD detail keeps the raw field table; upstream page-minimum/unbound amounts are excluded from ranking rather than treated as verified SKU prices.

Results preserve source links, original displayed prices, native currency, observation time, unverified fields and per-source failure states. **The lowest displayed price is a candidate, not a verified best deal**: exact variant, condition, quantity, coupon eligibility, authenticity, stock and checkout price still need review. Potential deposits, parts and used/damaged items receive review signals.

CNY and IDR are ranked separately. Blibli is an Indonesian marketplace, **not Bilibili**. No Indonesia-to-China/Fansbuy route is assumed. Fansbuy's integration here is its shipping calculator, not a product catalog or purchasing API.

## Fansbuy → Brazil

Supply **packed** weight in grams, dimensions in centimetres and every applicable category:

```sh
# Only use --ordinary-goods if no special categories apply.
china-deals shipping --weight-g 1000 --dimensions-cm 20 20 15 --ordinary-goods --format markdown

# Electric is Fansbuy's powered/electronics category; Battery refers to its separate battery flag.
# Confirm the correct classification with Fansbuy; do not omit applicable flags.
china-deals shipping --weight-g 1500 --dimensions-cm 30 20 15 --category Electric --category Brand
```

Supported calculator flags: `Electric`, `Brand`, `liquid`, `bag`, `food`, `shoes`, `Battery`, `Knives`, `powder`, `watch`, `cosmetics`, `magnetic`, `perfume`. If categories are omitted, eligibility stays unresolved and routes are rejected conservatively. Disabled, category-incompatible, overweight and oversize routes are retained under `rejected` with reasons. Missing dimensions may also prevent eligibility checks.

Quotes use the live public calculator's **base CNY estimate**; advertised coupon discounts remain conditional. Delivery windows are carrier estimates. Brazil taxes, final packing, insurance, remote-area fees and customs clearance are not established by a freight quote.

```sh
# Illustrative FX/tax assumptions only; replace with current applicable values.
china-deals estimate --goods-cny 300 --freight-cny 168.75 \
  --cny-brl 0.75 --usd-brl 5.40 --icms-rate 0.20 \
  --domestic-cny 10 --agent-fee-cny 0 --insurance-cny 0

china-deals restrictions --condition used --category Electric --ncm 84713012
```

The default indicative RTS calculation assumes **non-Remessa Conforme** treatment: 60% federal import duty on the assumed customs value, then ICMS calculated *por dentro*. Domestic freight is included in that value; a separately supplied buying-agent fee has an explicit valuation caveat. FX and ICMS are required inputs. Values above the USD 3,000 RTS ceiling are rejected.

The policy snapshot was checked against Receita's current manual on **2026-10-27**. For qualifying PRC natural-person purchases with DIR registered from **2026-05-12**, the manual specifies 0% federal duty through USD50 and 60% less USD30 above that. `--remessa-conforme` applies those rules **only as your assertion of eligibility**; it does not verify the retailer, recipient or declaration. Using a shopping agent does not establish PRC eligibility. The old 20%/USD20 figures are historical. Consult [Brazil research](docs/research/shipping-brazil.md) and recheck current official policy before relying on a cost estimate.

`restrictions` provides checks, never legal clearance. Used goods, batteries, liquids, wireless equipment and regulated categories need case-specific verification. A carrier restriction is different from an import prohibition. **Sea/container transport does not make an otherwise prohibited import legal**, and batteries do not universally require containers. A missing air route does not prove a sea-only legal requirement.

## Offline data and automation

```sh
china-deals rank examples/synthetic-offers.json --format markdown
china-deals search '机械键盘' --markets taobao --include-offers > search.json
china-deals rank search.json --require-term '机械'
china-deals shipping --from-json captured-fansbuy-response.json \
  --weight-g 1000 --dimensions-cm 20 20 15 --ordinary-goods
```

Captured input must bind the original response to a matching request and timestamp; bare rate responses are refused. See the real public [fixture](tests/fixtures/fansbuy-estimates-2026-10-27.json): `{ "request": { "destination":"BR", "weight_g":1000, "dimensions_cm":[20,20,15], "categories":[] }, "captured_at":"2026-10-27T13:37:27Z", "response": { "code":0, "data":[] } }`. The timestamp/request metadata are caller-supplied and do not establish authenticity or current pricing. Offline imports preserve unknown observation times. The bundled product offers are **synthetic**, for demonstration only.

Exit codes: `0` command completed (inspect warnings); `2` invalid input/command failure; `3` partial, blocked, unavailable or unverified-empty marketplace coverage. `doctor` reports diagnostic state in JSON. Do not treat empty results as proof the product is unavailable. JSON input is bounded to 4 MiB; upstream subprocesses have time and output limits.

## Why CLI first

A shell-capable subscription agent can invoke the CLI directly. An MCP server also works with subscriptions, but is not required for this workflow. Token and resource use depend on the client, tool schemas, output and browser work; CLI is not universally cheaper. JSON defaults and narrow commands keep the interface small. An optional MCP wrapper can be added later without changing adapters or cost arithmetic.

## Research and development

The [research index](docs/research/README.md) compares Agent-Reach, OpenCLI, marketplace MCPs and browser-to-API frameworks with pinned primary-source links. The implementation composes OpenCLI as an external executable rather than forking a broad social-media tool. See [third-party notices](THIRD_PARTY.md).

```sh
git clone https://github.com/Marlos001/china-deals.git
cd china-deals
uv run python -m unittest discover -s tests -v
uv run china-deals schema
```

Tests use explicit fixtures/mocked boundaries; they do not prove authenticated marketplace access. No order, cart change, message, payment or shipment submission commands are exposed. Keep credentials, browser profiles, local captures and private product research out of Git. Respect marketplace terms and verification controls.

MIT licensed. Contributions welcome, especially real-account adapter validation, Blibli access, documented Fansbuy rate contracts and source-reviewed tax policies.
