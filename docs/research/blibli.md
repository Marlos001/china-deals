# Blibli Indonesia and the OpenCLI boundary

Inspected 2026-10-27. Blibli means the Indonesian marketplace at
[blibli.com](https://www.blibli.com/), **not Bilibili**. Native prices are IDR.
These sources do not establish forwarding through Fansbuy or Indonesia-to-Brazil
shipping eligibility.

## What was actually observed

The unauthenticated read-only request
[`GET /backend/search/products?searchTerm=keyboard&start=0&itemPerPage=3`](https://www.blibli.com/backend/search/products?searchTerm=keyboard&start=0&itemPerPage=3)
returned **HTTP 403**, `Content-Type: text/html; charset=UTF-8`, from this host.
The implemented Python adapter was then run against the same endpoint and returned
`status=blocked`, `error.code=http_403`, and no items. A denial is not proof of
zero matching products, nor proof that login would fix it.

Opening the first-party
[search page](https://www.blibli.com/jual/keyboard) in the T3 browser also returned
403 and the title `Just a moment...`. Visible text included
`Tunggu dulu, verifikasi sedang berjalan.` and a human-verification prompt.
No verification controls were operated. The browser page's automatic challenge
requests are not successful product requests. No account login, purchase,
seller contact, publishing, cookie extraction, or CAPTCHA bypass was performed.

First-party product links use `/p/<slug>/ps--<product-code>`, for example the
[Blibli product page](https://www.blibli.com/p/pokemon-tcg-indonesia-evolusi-mega-impian-ex-mega-dream-ma3-booster-box-3-box-no-promo/ps--BRK-60022-06672).
The first-party search index also exposes variant links using `/is--...`, e.g.
[this native variant URL](https://www.blibli.com/p/kabel-fiting-lampu-bulb-bohlam-cafe-gantung-dekorasi-decor-outdoor-indoor-100m-100-meter/is--MIO-70139-00008-00001).
These are URL-shape evidence from indexed first-party pages, not current stock,
price, successful direct-browser extraction, or a recommendation to buy.

## Implemented Blibli behavior and limits

`search_marketplace('blibli', query)` performs a public GET with URL-encoded
`searchTerm`, `start=0`, and bounded `itemPerPage`. It accepts a JSON object with
`data.products` as an array of raw product objects, retaining nested price fields.
That success shape is covered by **synthetic fixtures only** in this task; the
403 response prevented current first-party success-schema verification. Missing
or malformed `data.products` is an error; an actual empty array remains
`empty_unverified`. HTTP 401 is `auth_required`; 403/429 are `blocked`; connection
and other HTTP failures are `unavailable`. No mock offers are substituted.

The optional keyword argument `browser_fallback=True` reuses **only OpenCLI**:

- Search opens `https://www.blibli.com/jual/<encoded-query>`, checks the page for
  verification/login indicators, and only on an ordinary Blibli page attempts
  the same GET in page context using `fetch` with same-origin credentials. It
  does not inspect credentials, inject a session, or solve challenges. If the
  browser bridge is missing, an already observed direct 403 stays `blocked`.
- `get_item('blibli', native_product_url, browser_fallback=True)` opens that native
  HTTPS product/variant URL and reads `script[type="application/ld+json"]`
  [Schema.org Product](https://schema.org/Product) nodes. Only nodes whose native
  product/offer URL matches the requested URL are returned. Related products and
  unbound nodes are excluded. Product JSON-LD is a standards-based extraction
  candidate; its present availability on Blibli was **not verified**. Missing
  JSON-LD or missing URL binding remains `empty_unverified`.
- Blibli detail requires the **full native URL**, not a bare SKU. Without browser
  opt-in it returns `unavailable` / `browser_opt_in_required`; with a bare SKU or
  foreign URL it returns `unavailable` / `detail_url_required`. No undocumented
  private detail API or SKU resolver is guessed. Both `/ps--` and `/is--` native
  paths are accepted; query parameters are removed, so selections encoded only
  in query parameters remain unverified.

The browser path has source-verified command syntax and synthetic boundary tests,
but is **not live-proven product extraction**. OpenCLI's extension was not
connected in this environment. The T3 browser and OpenCLI bridge are separate
systems. No extension was installed and no browser profile was copied. A bridge
failure is not evidence about the user's marketplace authentication state.

Each browser operation uses a unique `china-deals-<uuid>` owned session, with
`--session` **after `browser` and before the subcommand**. A `finally` block
attempts `close`; cleanup has a bounded allowance of up to five seconds. Cleanup
failures are disclosed in warnings, including the owned session name. Upstream
documents a ten-minute idle timeout for owned interactive sessions.

Root integration: all adapters return raw rows. Blibli API rows retain fields
such as `name`, nested `price`, and `url`; JSON-LD detail retains `name`, `offers`,
and native schema properties. Root owns normalization. Taobao/JD detail is a
**field/value table for one product**, not multiple product offers. The optional
browser keyword needs explicit exposure by any higher-level CLI that wants it;
this worker did not change CLI or schema files.

## OpenCLI 2.0.2 source/package verification

The contract pin is
[`jackwener/opencli@97dc0cd5214b9602bcda78d7422f231ee8a803e9`](https://github.com/jackwener/opencli/tree/97dc0cd5214b9602bcda78d7422f231ee8a803e9).
The isolated npm package identifies itself as `@jackwener/opencli` version
`2.0.2`, Apache-2.0. No AI API is called by this Python module.

Read-only command mapping and upstream search limits:

| Marketplace | Search command | Detail command | Maximum search limit |
| --- | --- | --- | --- |
| taobao | `taobao search` | `taobao detail` | 40 |
| jd | `jd search` | `jd detail` | 30 |
| goofish | `xianyu search` | `xianyu item` | 60 |

Sources: pinned
[Taobao search](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/taobao/search.js),
[Taobao detail](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/taobao/detail.js),
[JD search](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/jd/search.js),
[JD detail](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/jd/detail.js),
[Xianyu search](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/xianyu/search.js),
[Xianyu item](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/clis/xianyu/item.js).

The npm package copies of Taobao search, JD search, and Xianyu item matched the
local pinned snapshots byte-for-byte (SHA-256 respectively
`a748fe066f461b6aab9b8256e45e8ab1cca5d87f8ee589fa6c0edb16cef442de`,
`d7fcd4806b1e795b594b5aa7eaa201c6598eb9e884f850c6945098be66cfe77a`,
`bff303f425ca3591133c46cc76086705dde675e0dbb6e41f50db13f04192bda8`).

Verified from the installed package and source:

- [`src/command-output.ts`](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/src/command-output.ts)
  emits `{ "ok": true, "data": ... }` and `{ "ok": false, "error": ... }`.
  Bare arrays are not this version's CLI wire format. The wrapper rejects an
  invalid envelope and a nonzero process exit accompanying apparent success.
- [`src/commanderAdapter.ts`](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/src/commanderAdapter.ts)
  registers `--format json` on adapter commands and does **not** register named
  `--session` there. Marketplace adapters manage their own site-session lifecycle.
  Search argv puts options before `-- <query>` to preserve leading-dash queries.
- [`src/commands/browser.ts`](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/src/commands/browser.ts)
  registers `browser --session NAME open URL`, `eval JS`, and `close`. `eval`
  emits its evaluation result in the same success envelope. See the pinned
  [bridge guide](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/docs/guide/browser-bridge.md).
- [`src/errors.ts`](https://github.com/jackwener/opencli/blob/97dc0cd5214b9602bcda78d7422f231ee8a803e9/src/errors.ts)
  defines `AUTH_REQUIRED`, `BROWSER_CONNECT`, `EMPTY_RESULT`, and other errors.
  Xianyu detail reports verification as `EMPTY_RESULT` plus a blocked hint;
  the Python wrapper checks that hint before classifying an empty result.
- JD search/detail do not perform Taobao-style explicit page usability checks.
  Empty JD search stays `empty_unverified`; login URLs/titles, verification
  titles, or detail lacking title/price are not admitted as usable detail.

Subprocesses use argv arrays and `shell=False`, close stdin, cap the **combined
stdout and stderr at 2 MiB**, and kill/reap on timeout or overflow. POSIX process
groups cover CLI descendants. Error responses omit raw stderr and backend
messages. JSON decimal literals are retained as strings. Basic `doctor()` runs
only `--version`; bridge diagnostics require explicit `doctor(live=True)`.
Version mismatches fail closed before marketplace commands.

## Exact commands and verification results

These ran from `/home/marlos/projects/china-deals` unless stated otherwise:

```sh
npm install --prefix /tmp/china-deals-opencli-2.0.2 --ignore-scripts --no-audit --no-fund @jackwener/opencli@2.0.2
/tmp/china-deals-opencli-2.0.2/node_modules/.bin/opencli --version
/tmp/china-deals-opencli-2.0.2/node_modules/.bin/opencli taobao search --help
/tmp/china-deals-opencli-2.0.2/node_modules/.bin/opencli browser --help
/tmp/china-deals-opencli-2.0.2/node_modules/.bin/opencli browser eval --help
/tmp/china-deals-opencli-2.0.2/node_modules/.bin/opencli doctor --help
python -m unittest discover -s tests -p test_adapters.py -v
python -m unittest discover -s tests -v
python -m compileall -q china_deals/adapters.py tests/test_adapters.py
```

Package installation exited 0; version output was `2.0.2`. Help/source inspection
verified parser contracts. The adapter suite passed 26 tests at this checkpoint;
the then-current complete project suite passed 44. After adding closed-pipe
timeout/reaping and variant-URL coverage, the final adapter suite passed 28 and
the then-current complete suite passed 52 (other workers also added tests).
The final complete-suite command was `python -m unittest discover -s tests -q`.
Tests cover real temporary
subprocesses and synthetic backend responses. They do not prove marketplace
inventory, authentication, payable prices, or shipping eligibility.

The parser probe below reached a real `BROWSER_CONNECT` error (exit 69), rather
than printing help or accepting `--help` as a CLI option. It produced no product
data and confirms no authenticated operation:

```sh
/tmp/china-deals-opencli-2.0.2/node_modules/.bin/opencli taobao search --limit 1 --format json -- --help
```

Additional probes with a three-second `_run` budget timed out and were killed:
the same search argv, and
`opencli browser --session china-deals-argument-check eval 1`. These timeouts are
not bridge connectivity success. No probe was retried automatically.

The actual public adapter checks ran as follows; the first reported version
availability only, and the second reported the live Blibli 403 described above:

```sh
python - <<'PY'
import json
from china_deals.adapters import doctor, search_marketplace
exe = '/tmp/china-deals-opencli-2.0.2/node_modules/.bin/opencli'
print(json.dumps(doctor(executable=exe)))
print(json.dumps(search_marketplace('blibli', 'keyboard', limit=3, timeout=10)))
PY
```

No commit, push, package configuration change, or global installation was made
by this worker. Only `china_deals/adapters.py`, `tests/test_adapters.py`, and this
research note are worker-owned repository changes.
