# Offline-first onboarding and research workflow

Run these commands from a checkout with Python 3.11 or later. The core has no runtime dependencies. The commands in the first section use bundled files and do not contact a marketplace or FX service; acquiring the checkout or installing packages requires network access. An installed `china-deals` command can replace `python -m china_deals`, but the example file paths still require the checkout.

## First run: no live requests

```sh
python -m china_deals plan 'Sony WH-1000XM6'
python -m china_deals rank examples/synthetic-offers.json --currency native --format markdown
python -m china_deals shipping --from-json tests/fixtures/fansbuy-estimates-2026-10-27.json \
  --weight-g 1000 --dimensions-cm 20 20 15 --ordinary-goods
python -m china_deals brazil-compare examples/brazil-comparison.synthetic.json --format markdown
```

The plan suggests queries and checks; it does not search. The offers and comparison are synthetic, not deals or verified savings. The shipping fixture is a dated captured response for the specified parcel, destination and ordinary-goods classification; metadata supplied with a capture does not prove authenticity or current prices. Use the flag only for goods without special categories. Live shipping, packing, insurance, fees and tax can differ. Missing or ineligible comparison inputs remain unknown or conditional. These examples demonstrate the interface, not a single real product journey.

## From discovery to comparison

1. **Plan locally.** Run the `plan` command above and check the suggested translations and product requirements. Keep model, configuration, condition and intended use explicit.
2. **Search externally.** For example, `python -m china_deals search 'Sony WH-1000XM6' --zh-query '索尼 WH-1000XM6 头戴式耳机' --markets jd --limit 5 --include-offers --currency native > search.json`. This contacts a discovery service. Indexed leads are not live offers or current prices; inspect source statuses, warnings and links. `--currency native` avoids an additional FX lookup.
3. **Read detail externally.** Choose an exact native item ID or URL from the results, then run `python -m china_deals detail jd ITEM_ID --currency native`, replacing `ITEM_ID` with that actual ID. Check the selected variant, condition, price basis, source time, seller and fulfillment. A blocked or masked page supplies no current price; detail alone does not verify stock, authenticity or checkout.
4. **Refresh externally.** Copy `examples/watchlist.example.json` to a private working file, replace the synthetic entries (including their titles and synthetic exclusion) with exact observed native URLs and corresponding marketplace and item IDs, then run `python -m china_deals refresh watchlist.json --currency native --fresh-only --max-age-hours 1 --store /tmp/china-deals-history.sqlite > refresh.json`. Refresh requests first-party detail; it does not turn an old or blocked quote into a current price. The optional SQLite store is local. Review access receipts and freshness before using an observation. See [fresh data](FRESH_DATA.md) for history and capture details.
5. **Compare locally.** Use `examples/brazil-comparison.synthetic.json` as a schema example and prepare your own comparison JSON from the reviewed observations and equivalent Brazilian offer, including known freight, exchange rate, taxes, fees, condition and configuration. Then run `python -m china_deals brazil-compare comparison.json --format markdown`. This command uses payload FX or a supplied local snapshot and does not fetch FX implicitly. This is a separate, manually prepared input: refresh output is not automatically a complete comparison case. Unknown costs and mismatches prevent a verified savings claim.

Search, detail and refresh can return partial or blocked results. Exit code 3 signals partial, discovery-only, blocked, unavailable or unverified-empty coverage; inspect the JSON even when a command completes. An empty result does not establish absence of inventory. Prices, promotions, stock, exchange rates and import rules change; recheck the exact purchase and current official rules before deciding. Use accurate transaction values and descriptions for customs.

## Network, evidence and privacy

Default guest HTTP is cookie-free, but external services receive the requested queries, URLs and ordinary connection information. Browser guest search sends a site-restricted query to Google; a browser page can also load subresources from other hosts. Its fresh ephemeral Chromium context does not load a saved profile, but it is not a network sandbox. Native OpenCLI mode explicitly uses an existing browser session; treat it and its account as sensitive. The CLI itself makes no AI calls; an agent or service you choose separately may receive the material you provide it.

Stop on HTTP 401, 403 or 429, login, CAPTCHA or other verification challenges. Do not switch transports or reuse a session to continue against that host after a gate. Native Blibli search stops after an access gate; its optional browser fallback is limited to eligible network failures. Older installed versions may behave differently. See [browser and native modes](REFERENCE.md#optional-fresh-guest-browser).

Retain source URLs, original observation times, access receipts, exact variant and price basis alongside results. A search snippet, caller-supplied capture or old observation has a different evidentiary weight from a current primary page; even the latter is not checkout proof. JSON retains more provenance than compact Markdown. Local output, browser captures and SQLite history may contain private research or account data: store them privately, review before sharing, and keep credentials, profiles and private captures out of Git. See the [reference](REFERENCE.md) and [validation reports](validation/README.md) for source-specific limits.
