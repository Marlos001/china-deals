# Optional guest Chromium backend

`china_deals.browser_guest` provides two Python entry points. CLI wiring and the
`browser` dependency extra belong to the integration owner.

```python
from china_deals.browser_guest import search_browser_guest, get_browser_guest_item

leads = search_browser_guest("jd", "ROG 幻16 Air", limit=10, timeout=30)
detail = get_browser_guest_item("goofish", "985148706040", timeout=30)
```

Both functions return the existing guest result envelope: `marketplace`, `status`,
`items`, `warnings`, `error`, `access`, and `native_filters`. `executable_path` is
optional and defaults to `/usr/bin/chromium`. The dependency is imported lazily:
missing Playwright returns `status=unavailable`, `error.code=dependency_missing`;
a missing or unusable executable returns `browser_error`. Importing this module
does not require Playwright or start a browser.

## Isolation and stop conditions

Each call launches its own Chromium process using Playwright's temporary profile,
then creates a fresh incognito context. It never reads a saved profile, imports
storage state, attaches to the user's browser, asks for an account, or calls an
AI API. Anonymous cookies created by the sites exist only inside that disposable
context. Contexts and browser processes close on success and failure. Downloads
are disabled; page scripts, service workers and ordinary subresources retain
their normal behavior. Chromium's sandbox remains on.
No extensions, global settings, fingerprint changes, CAPTCHA handling, signed API
requests, or anti-bot-control changes are used.

HTTP 401/403/429, verification/login navigation, visible CAPTCHA, Google's unusual
traffic text, Cloudflare-style challenge titles, and Goofish's `非法访问` /
`请使用正常浏览器` message stop the operation. There is no automatic retry or
provider fallback. A blocked result contains no product rows, including earlier
partial leads. One overall timeout budget covers launch and reads; it is not
reset per link. Browser/driver startup and cleanup overhead can exceed that budget.

## Indexed search contract

Search reads one rendered Google Web page for the supplied query, prefixed with
the marketplace's `site:` domain. Chinese marketplace queries must be supplied in
Chinese by the caller when appropriate; this module does not translate, expand,
or silently replace them. `query` preserves the original input and `search_query`
records the submitted site-scoped query. The requested limit is capped at ten;
no pagination, inventory coverage claim, or native filter submission is made.

Only visible `h3` result headings with actual enclosing anchors are considered.
The heading and bounded enclosing-card text are retained. Displayed domains and
snippet text never become synthesized product links. Direct links must pass
`guest._product_url` for the requested marketplace. Duplicate native URLs,
unrelated hosts, malformed URLs, search/category routes, and HTTP URLs are omitted.

Google `/url` and `/goto` links are resolved by one ordinary browser navigation,
with at most one hop to a validated native product URL. Their opaque parameters
are never decrypted or decoded into target URLs. A Google search may also make
one same-query redirect, such as adding `sei`; changing the query or leaving
the permitted route is denied. At most ten distinct wrapper links are attempted.
Challenge or denied navigation stops the call, rather than trying another link.

Every indexed row has `source_mode=search_index`, `coverage=discovery_only`,
`price=None`, and `price_basis=indexed_text_only`. Card price text is merely a
discovery observation, with `discovered_at`, `index_source_url`, and the actual
`index_result_href` retained. It does not establish current price, seller status,
availability, checkout price, or stock. Such rows cannot support price ranking.
An index page without validated product leads is `empty_unverified`; it does not
mean the marketplace has no matching products. Unrecognized or timed-out pages
are unavailable. Requested filters remain residual and explicitly unapplied.

## Public item detail limits

`get_browser_guest_item` accepts an exact native product URL, or an ASCII numeric
ID for JD, Taobao, and Goofish. Blibli requires a product URL. Main-frame redirects
must preserve the exact canonical requested item identity and stay within one hop.

JD and Blibli reuse `guest.py`'s existing SKU-bound JD JSON and URL-bound Blibli
Product/Offer JSON-LD parsers, inspecting only state already delivered to the
ordinary rendered page. They do not issue separate API requests. These parsers
may be unavailable on the desktop rendered variant; no guessed alternative
schema is used. Masked or ambiguous prices remain null. A successful parse still
does not establish checkout availability or the selected purchasable variant.

No verified primary-item DOM contract is implemented for Goofish or Taobao.
After an ordinary page read, these return `item_schema_unverified`, or `blocked`
when a gate is encountered. Body-wide `¥` text, recommendations, and listing
metadata are never treated as a primary-item quote. In particular, the previously
observed [Goofish item 985148706040](https://www.goofish.com/item?id=985148706040)
was **delisted** in the separate guest-browser research; its historical ¥7,999
must not become a current offer. See [guest-access.md](guest-access.md). Because
this backend cannot currently bind its primary price and listing-status DOM, it
returns no detail row, rather than dropping the delisted/sold qualification.

## Verification

Offline tests use stub Playwright adapters and synthetic minimal schemas, with
no browser launch or network dependency:

```sh
python -m unittest discover -s tests -p 'test_browser_guest.py' -v
python -m unittest discover -s tests -p 'test_guest.py' -q
```

They cover all four marketplaces' URL boundaries, query receipts, null indexed
prices, encrypted-link navigation without decoding, one-hop and identity guards,
unrelated and duplicate results, HTTP/challenge stop behavior, partial-result
discarding, missing optional dependency, incognito configuration and cleanup,
and rejection of unbound Goofish body prices.

Live verification is separate from those synthetic checks. On 2026-10-27, local
sandboxed headless `/usr/bin/chromium` loaded the Goofish URL above with HTTP 200
but rendered `非法访问 / 为了保障您的体验，请使用正常浏览器访问闲鱼~`; the read
stopped. This differs from the earlier T3 preview observation and demonstrates
why successful browser research is not a promise of product-runtime access.

A subsequent Google JD search for `ROG 幻16 Air` allowed Google's one same-query
`sei` redirect, then returned `status=blocked`, `error.code=challenge`, with no
rows and no retry. Actual search results across the four marketplaces are
therefore **not established in this local product runtime**. Earlier T3 preview
success is separate evidence. No browser configuration was changed to evade
the gates and no further searches were made after that challenge.

Those external smoke checks preceded removal of a redundant service-worker
restriction. The final context leaves service workers at Playwright's normal
default; it has not been retested against external sites after the challenge.
