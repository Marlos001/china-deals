# iPhone 17 Pro Max search validation

Validated 2026-10-27 against **0.3.0 / `1a096f326da6b89e0b2b1732dcdc1eca0870e4bb`**. This is a CLI validation and root-agent handoff, not a purchase recommendation. Initial checkout was clean. Other agents subsequently changed implementation files; those changes were preserved. Offline reproductions below explicitly import a retained copy of the baseline, not peers' evolving code.

## Actual CLI execution

From `/home/marlos/projects/china-deals`:

```sh
python -m china_deals search 'iPhone 17 Pro Max' \
  --zh-query '苹果 iPhone 17 Pro Max 手机' \
  --query-for 'blibli=iPhone 17 Pro Max' \
  --markets taobao,jd,goofish,blibli --access guest --guest-engine http \
  --timeout 12 --limit 5 --include-offers --currency native
```

One network-bearing CLI invocation, started **15:54:07.875784 UTC**, elapsed **3.236 seconds**, exit **3**. Zero offers, zero ranked groups, zero unranked items, zero filter exclusions. Five recorded attempts: four DuckDuckGo HTML index requests and one Blibli public API request. No detail hydration, native session, FX request, price budget, or native filters. Parent process was bounded to 90 seconds; CLI timeout was 12 seconds per source.

- Taobao: `blocked / challenge`, 0 items; challenged host was `html.duckduckgo.com`, **not proof that Taobao product pages require login**.
- JD: same index challenge, 0 items.
- Goofish: same index challenge, 0 items.
- Blibli: API `http_403`, then index `challenge`, 0 items.

The first attempted command included `--hydrate 0`; argparse rejected it with exit 2, `must be between 1 and 100`, before network access. The corrected invocation omitted hydration. Both receipts are retained. This is an input-boundary observation, not a security-challenge retry. `--version`, `search --help`, `schema`, and `config show` were also inspected. The documented 168-test baseline was **not rerun** and is not a new test result.

Private evidence: `.local/search-validation/iphone17/cli-search.{receipt.json,stdout.json,stderr.txt}`, `cli-invalid-hydrate-zero.*`, and `schema.json`. No follow-up CLI network requests were made. The single invocation itself continued using the shared challenged index; see F1.

## Independent web/browser comparison

Exactly **12 targeted connector search queries** were submitted (batches 4 + 3 + 2 + 3). They covered Apple specifications, Blibli product routes, JD, Goofish, Taobao and Tmall. Search results are external discovery leads, never merged into CLI `offers`. Some queries returned category pages or unrelated results; these are not successful exact-product matches. Taobao/Tmall yielded no sufficiently bound product URL in this bounded pass; that is not an inventory claim. Blibli category snippets showed differing cached prices, but no handset SKU/stock/price binding was established.

T3 preview: `preview_status`, then a new tab with `profileId=incognito`, `reuseExistingTab=false`, `open=false`. Owned tab: `tab_s_4cac2679-3846-4860-a3d7-8c794cdb6e4b`; every subsequent inspection/navigation targeted that ID. Exactly **four product opens**, using exact connector-returned URLs:

1. [Goofish 1087872356879](https://www.goofish.com/item?categoryId=0&id=1087872356879). Public page says **“糟糕！宝贝被删掉了”** (item deleted), followed by **“为你推荐”** (recommendations). Search snippets had mixed iPhone offers/prices from that recommendation region. The requested item is delisted; none of those cards supplies its model, storage, condition or price. No login gate established.
2. [JD opaque product route](https://item.jd.com/product/6QDM9CaD9ZAa0SxjEPbKrg.html). Connector title identifies iPhone 17 Pro Max, deep blue, 256GB, and **“需当面激活”** (in-person activation required). Browser redirected to `passport.jd.com/new/login.aspx`, preserving the exact product URL in `ReturnUrl`; visible page is **“个人用户登录” / “企业用户登录”**. This is a destination login gate, not merely an invitation overlay on readable product content. No current main-item price, stock, warranty or promotion was verified. Mixed recommendation amounts in the indexed excerpt were rejected.
3. [Blibli ZAGG case, GAS-60045-02344-00003](https://www.blibli.com/p/zagg-manhattan-snap-case-iphone-17-pro-max-17-pro-magsafe-casing/is--GAS-60045-02344-00003). Exact connector title is a **case**, not a handset. Browser redirected to `/challenge/landing/` and displayed **“Ada aktivitas yang tidak biasa”**. Stopped; no retry, challenge interaction or proxy rotation. This independently tests accessory relevance and product-page access; it does not validate a Blibli handset. An earlier connector category-page open also returned HTTP 403.
4. [Goofish 1023378656793](https://www.goofish.com/item?categoryId=126862528&id=1023378656793). Main product was publicly readable; details below. No account/login/contact/cart/purchase action occurred.

Captures are DOM text and bounded accessibility snapshots, **not screenshot evidence**. Full retained tool responses are `browser-*.json`; Goofish main-item text is additionally isolated in `goofish2-primary-only.json`. Public report omits IP/reference codes from the private Blibli challenge capture. Four product opens are exhausted; no more were attempted.

### Readable Goofish main item: contradictory configuration

Exact primary-item evidence, captured before `为你推荐`:

- Title: **“纯原装17ProMax 1T原装正品官网可查 苹果美版无锁”**. Structured model: **“iPhone 17 Pro Max”**. This is a source claim of the target model, not 17 Pro/plain 17/16; authenticity remains unverified.
- Displayed amount: **¥6999**. Description: **“内存: 256G”**, **“蓝色6999橙色7099白色7499”**, **“512G加1000 1T加 1800”**. Structured storage: **“512GB”**. Title, description and structured attribute disagree (1TB / 256GB / 512GB). **Do not bind ¥6999 to 512GB or 1TB, calculate a winning variant price, or assume 2TB is offered.** The text explicitly requests a separate quote by storage/color; none was requested.
- Region: **“美版纯无锁 开孔支持双卡双待 5G”**; structured **“海外无锁”**. Seller claims US unlocked plus a physical modification/dual-SIM capability. Preserve the claim and conflict with Apple's US eSIM-only specification; do not silently map it to a factory US or China SKU.
- Condition: **“全新未拆封”**, **“无任何维修”**, and prose denying refurbishment/modification. Those are seller claims; they are not independent confirmation and conflict with the physical-SIM wording sufficiently to require review. “无维修” must not be classified as a positive repair admission solely because it contains `维修`.
- Warranty: **“支持半年质量保修”**, conditional on keeping the anti-tamper seal intact, with damage/wear exclusions. This is a seller six-month warranty claim, not verified Apple warranty or Brazilian service coverage.
- A purchase button and displayed price were visible, but no stock quantity, exact selected SKU, checkout price or account/payment eligibility was verified. Domestic `包邮` is not international freight. No primary-item deposit or installment price was established. Financing text elsewhere belonged to recommendations and was excluded.

### Apple primary-source guardrails

[Apple China specifications](https://support.apple.com/zh-cn/125091), [Apple US specifications](https://support.apple.com/en-us/125091), and [Apple Indonesia specifications](https://support.apple.com/id-id/125091) explicitly list **256GB, 512GB, 1TB and 2TB** for iPhone 17 Pro Max. These establish model capacities, not availability of every seller/color/region combination. No 128GB Pro Max variant is established by these sources.

China lists **“双卡 (nano‑SIM 卡)”**. US lists **“Dual eSIM”** and **“not compatible with physical SIM cards”**. Indonesia lists **“SIM Ganda (nano-SIM dan eSIM)”** and dual-eSIM support. Region must be bound to the actual offered unit; marketplace country alone does not establish its region. Primary-source excerpts are retained in `web-discovery-03.json`, `web-primary-04.json`, and `web-discovery-05.json`.

## Reproduced findings and exact root-owned recommendations

**F1 — High: shared-host challenge does not stop later requests.** Live receipt shows four sequential DuckDuckGo challenges in the one search. Offline `_fetch` spy confirms four requests to the same discovery host plus one Blibli API request despite the first challenge. Scope: `cli.py` market loop and `guest.py:search_guest`. Add invocation-scoped challenge state keyed by actual host/access surface; skip subsequent calls to that challenged surface and record `skipped_after_challenge` with the originating attempt. Do not claim every marketplace is blocked when only the index is challenged. An independent unchallenged marketplace API can retain its own status. No automatic retry/rearm/transport change.

**F2 — High: Blibli JSON-LD availability/condition are retained raw but ignored operationally.** Synthetic exact-URL-bound `Product`/`Offer`, price IDR 24999000, `availability=https://schema.org/OutOfStock`, `itemCondition=https://schema.org/UsedCondition`: actual `detail` CLI returns exit 0, `availability=unknown`, `condition=unknown`; `rank_offers` admits one priced IDR candidate. Scope: `guest.py:_blibli_detail` and normalization. Map explicit schema availability/condition into normalized fields while preserving literal evidence. OutOfStock/SoldOut/Discontinued must not rank; absent availability stays unknown, and `InStock` remains only a source claim. Add fixtures for these states, unknown enum and contradictions. This is **offline parser proof**, not a claim that a live Blibli iPhone was out of stock.

**F3 — High: hydration erases failure provenance and continues after challenge.** Two synthetic JD index leads plus `--hydrate 2`; first detail returns a challenge. Getter is still invoked twice. Search output retains only the index attempt and `status=discovery_only`; the detail error/attempts disappear. Even `Guest detail was unavailable...`, attached to the row, disappears because normalization replaces warnings. Scope: `cli.py` hydration branch and `models.py:normalize_offer`. Append per-item detail receipts without overwriting discovery receipts; preserve failure code, exact URL, timestamp, status and scoped warnings. Stop subsequent hydration on the challenged host. Successful hydration should likewise retain both discovery and detail provenance rather than replacing the row wholesale.

**F4 — Medium: real JD opaque route is silently discarded by discovery admission.** `_product_url('jd', exact URL above)` returns `None`; a one-result synthetic index fixture returns `empty_unverified / index_no_results`. The connector and browser establish that this is a JD-served route (browser gate, not a numeric SKU). Scope: `guest.py:_product_url`, `search_guest`, and detail routing. Preserve such first-party opaque URLs as **unverified discovery links**, with `item_id=unknown` until a primary page binds a numeric SKU. Do not fabricate the SKU from the opaque token or loosen host validation. Expose rejected-route counts/reasons; a parser coverage gap must remain distinguishable from an index with no matches. The existing numeric detail parser need not claim support before evidence exists.

**F5 — Medium, output-quality gap: literal terms are insufficient product classification.** Baseline `rank --require-term 'iPhone 17 Pro Max'` on 10 synthetic rows admits 6: case, dummy, replica, deposit, installment, repair item; it filters 4 including the true compact alias `iPhone17ProMax`. Case/dummy/replica/installment have no risk signals. Deposit/repair signals exist but do not exclude ranking. Generic rank already declares comparability unverified; this is not a claim it promised verified handsets. Add query-aware model family/alias handling with separate exact-model match and whole-handset classification, literal evidence and unknown states. Distinguish Pro Max from Pro/plain/previous generations. Cover 手机壳/保护套/casing, 模型机/dummy, 仿/复刻, 定金/deposit, 每月/月供/installment, and repair/negation. Preserve full raw titles and use conservative review exclusions rather than assuming every suspicious substring is a confirmed fake or repair.

The readable Goofish item should become a source-bound regression for conflicting storage and regional-SIM claims: 1TB title + 256GB description + 512GB attribute must remain conflicting, with an unbound amount. Never use recommendation text to resolve missing primary-item facts. Root owns implementation and regression-test integration; **no production code was changed by this validation task**.

## Minimal offline reproductions

All network access is mocked in this block. Run from repository root. The retained `baseline/china_deals/` was exported with `git archive 1a096f3 china_deals`, so peer edits do not change the outcome. HTML/JSON fixtures under the same private directory are explicitly synthetic; no real listing is assigned their invented prices/IDs.

<!-- offline-repro -->
```python
import copy, io, json, pathlib, sys
from contextlib import redirect_stdout
from unittest.mock import patch

p = pathlib.Path('.local/search-validation/iphone17')
sys.path.insert(0, str((p / 'baseline').resolve()))
from china_deals import guest
from china_deals.cli import main
from china_deals.ranking import rank_offers

def invoke(argv):
    out = io.StringIO()
    with redirect_stdout(out):
        code = main(argv)
    return code, json.loads(out.getvalue())

base = ['search', 'iPhone 17 Pro Max', '--zh-query',
        '苹果 iPhone 17 Pro Max 手机', '--currency', 'native']
result = {'baseline': '1a096f326da6b89e0b2b1732dcdc1eca0870e4bb',
          'imported_guest': guest.__file__}
with patch.object(guest, '_fetch', side_effect=guest._Failure(
        'blocked', 'challenge', 'SYNTHETIC challenge')) as fetch:
    code, data = invoke(base + ['--markets', 'taobao,jd,goofish,blibli'])
result['F1'] = {'exit': code, 'fetch_count': fetch.call_count,
                'urls': [call.args[0] for call in fetch.call_args_list]}

url = 'https://www.blibli.com/p/synthetic-iphone-17-pro-max/ps--SYN-17000-00001'
with patch.object(guest, '_fetch', return_value=(
        (p / 'synthetic-out-of-stock.html').read_text(), url)):
    code, data = invoke(['detail', 'blibli', url, '--currency', 'native'])
row = data['items'][0]
ranked = rank_offers([dict(row, marketplace='blibli')])
result['F2'] = {'exit': code, 'availability': row['availability'],
                'condition': row['condition'],
                'raw_offer': row['source_detail']['offer'],
                'ranked_count': len(ranked['groups'].get('IDR', []))}

rows = [{'title': 'iPhone 17 Pro Max 256GB', 'item_id': str(i),
         'url': f'https://item.jd.com/{i}.html', 'source_mode': 'search_index'}
        for i in [17001, 17002]]
search = {'status': 'discovery_only', 'source_mode': 'search_index',
          'items': rows, 'warnings': [], 'access': {'attempts': [
              {'url': 'https://html.duckduckgo.com/html/?q=synthetic', 'status': 'ok'}]}}
detail = {'status': 'blocked', 'items': [], 'warnings': ['synthetic challenge'],
          'error': {'code': 'challenge'}, 'access': {'attempts': [
              {'url': 'https://item.m.jd.com/product/17001.html',
               'status': 'blocked', 'error_code': 'challenge'}]}}
with patch.object(guest, 'search_guest', return_value=copy.deepcopy(search)), \
     patch.object(guest, 'get_guest_item', return_value=detail) as get:
    code, data = invoke(base + ['--markets', 'jd', '--hydrate', '2', '--include-offers'])
result['F3'] = {'exit': code, 'detail_call_count': get.call_count,
                'source': data['sources'][0],
                'offer_warnings': [x['warnings'] for x in data['offers']]}

with patch.object(guest, '_fetch', return_value=(
        (p / 'synthetic-jd-index.html').read_text(), 'https://html.duckduckgo.com/html/')):
    data = guest.search_guest('jd', '苹果 iPhone 17 Pro Max 手机')
result['F4'] = {'status': data['status'], 'count': len(data['items']), 'error': data['error']}

data = rank_offers(json.loads((p / 'synthetic-relevance.json').read_text()),
                   require_terms=['iPhone 17 Pro Max'])
result['F5'] = {'ranked': [{'title': x['title'], 'signals': x['signals']}
                         for x in data['groups'].get('CNY', [])],
                'filtered_count': data['filtered_count']}
(p / 'offline-baseline-results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False, indent=2))
```

Expected baseline results: F1 = 5 fetches (4 shared-index); F2 = 1 ranked out-of-stock candidate, condition/availability unknown; F3 = 2 detail calls and lost challenge receipt; F4 = 0 items / `empty_unverified`; F5 = 6 ranked / 4 filtered. These are reproductions of defects/gaps, not passing behavior assertions. `offline-baseline-results.json` is the frozen-revision rerun; the earlier `offline-results.json` was exploratory during concurrent work and is secondary.

An additional offline actual CLI command is:

```sh
cd .local/search-validation/iphone17/baseline
python -m china_deals rank ../synthetic-relevance.json \
  --require-term 'iPhone 17 Pro Max' --currency native
```

## Handoff boundary

Five findings reproduced offline; one live HTTP search; four browser product inspections; twelve connector search queries. No verified purchasable, exact-variant offer or eligible promotion was established. No coupon terms, account eligibility or stock was invented. Public browser access to one Goofish main item does not prove the CLI can extract it: baseline HTTP guest detail explicitly lacks Goofish/Taobao schemas.

Only this document and `.local/search-validation/iphone17/` are task-owned. No commit/push, external communication, login, cart, purchase, seller contact, or proxy rotation. Root's next action is to triage F1–F5, integrate narrowly scoped offline regressions, and rerun those against the revised code before considering another authorized live pass. Do not replay the exhausted live search/browser budget automatically.
