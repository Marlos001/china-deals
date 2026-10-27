"""Optional, isolated Chromium guest reads. No login, retries, or challenge bypass.

Playwright is imported only when a browser operation is requested. Google result
cards are discovery observations, never current-price quotes.
"""

from __future__ import annotations

import re
import time
from contextlib import contextmanager
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit

from . import adapters, guest
from .models import CURRENCIES, marketplace_name, utc_now

_GOOGLE_HOSTS = {"www.google.com", "google.com"}
_DOMAINS = {"taobao": "item.taobao.com", "jd": "item.jd.com",
            "goofish": "www.goofish.com", "blibli": "www.blibli.com/p/"}
_Failure = adapters._Failure

# Read rendered headings and their actual anchors; never synthesize URLs from
# displayed domains, snippets, or opaque redirect parameters.
_CARDS_JS = """() => Array.from(document.querySelectorAll('h3'))
  .filter(h => h.getClientRects().length && h.innerText.trim())
  .slice(0, 40).flatMap(h => {
    const a = h.closest('a[href]');
    if (!a) return [];
    let card = a;
    for (let i = 0; i < 6 && card.parentElement; i++) {
      const next = card.parentElement;
      if (next === document.body || next.querySelectorAll('h3').length !== 1) break;
      card = next;
      if (card.matches('div.MjjYud, div.g, div[data-sokoban-container]')) break;
    }
    return [{title: h.innerText.trim().slice(0, 4096), href: a.href,
             snippet: card.innerText.trim().slice(0, 6000)}];
  })"""

_STATE_JS = """() => ({title: document.title,
  text: (document.body?.innerText || '').slice(0, 100000),
  verification: Array.from(document.querySelectorAll(
    'iframe[src*="recaptcha"], iframe[src*="captcha"], iframe[src*="challenges.cloudflare.com"], #captcha, #challenge-form, .g-recaptcha, .cf-turnstile'
  )).some(e => e.getClientRects().length)})"""


def _milliseconds(deadline):
    return max(1, int(adapters._remaining(deadline) * 1000))


def _gate_url(url):
    return bool(re.search(r"/(?:sorry|login|signin|captcha|challenge|verify|passport)(?:[/?.]|$)", url, re.I))


def _check_page(page, response=None):
    if response is not None and response.status >= 400:
        status = "blocked" if response.status in {401, 403, 429} else "unavailable"
        raise _Failure(status, f"http_{response.status}", "Browser page returned an error; stopped without retry.")
    state = page.evaluate(_STATE_JS)
    if (_gate_url(page.url) or state.get("verification")
            or re.search(r"captcha|access denied|just a moment|京东验证|登录|\blogin\b|sign in", state.get("title", ""), re.I)
            or re.search(r"unusual traffic|our systems have detected|verify.{0,25}human|"
                         r"verifikasi sedang|非法访问|请使用正常浏览器|滑动验证|安全验证|完成验证|"
                         r"检测到异常流量|我们的系统检测到|请先登录|请登录后|登录后查看|登录后继续|"
                         r"sign in to continue|log in to continue",
                         state.get("text", ""), re.I)):
        raise _Failure("blocked", "challenge", "Browser requested login or verification; stopped without retry or bypass.")
    return state


class _Navigation:
    """Allow an initial URL and at most one ordinary redirect to a product.

    Only main-frame navigation is restricted here; normal page subresources and
    first-party scripts run unchanged. No requests are replayed or signed.
    """

    def __init__(self, marketplace, initial, product=None):
        self.marketplace, self.initial, self.product = marketplace, initial, product
        self.started, self.hops, self.failure, self.denied_url = False, 0, None, None

    def _same_search(self, url):
        if not (guest._valid_url(self.initial, _GOOGLE_HOSTS) and guest._valid_url(url, _GOOGLE_HOSTS)):
            return False
        before, after = urlsplit(self.initial), urlsplit(url)
        query = parse_qs(before.query).get("q")
        return (before.path == after.path == "/search" and query is not None
                and len(query) == 1 and parse_qs(after.query).get("q") == query)

    def handle(self, route):
        request = route.request
        if not request.is_navigation_request() or request.frame != request.frame.page.main_frame:
            route.continue_()
            return
        url = request.url
        failure = None
        if _gate_url(url):
            failure = _Failure("blocked", "challenge", "Navigation reached login or verification; stopped.")
        elif not self.started and url == self.initial:
            self.started = True
        else:
            native = guest._discovery_url(self.marketplace, url)
            self.hops += 1
            allowed = self._same_search(url) or (native and (not self.product or native == self.product))
            if self.hops > 1 or not allowed:
                failure = _Failure("blocked", "redirect_denied", "Navigation left the allowed product or exceeded one hop; stopped.")
        if failure:
            self.failure = failure
            self.denied_url = url
            route.abort()
        else:
            route.continue_()


@contextmanager
def _browser_context(executable_path, deadline):
    try:
        from playwright.sync_api import Error, TimeoutError, sync_playwright
    except ImportError:
        raise _Failure("unavailable", "dependency_missing", "Install the optional china-deals[browser] extra to use guest Chromium.") from None
    browser = context = None
    try:
        with sync_playwright() as playwright:
            try:
                # launch() creates Playwright's disposable temporary user-data
                # directory; new_context() is incognito, with no storage_state.
                browser = playwright.chromium.launch(
                    executable_path=executable_path or "/usr/bin/chromium",
                    headless=True, chromium_sandbox=True, timeout=_milliseconds(deadline),
                )
                context = browser.new_context(accept_downloads=False)
                context.set_default_timeout(_milliseconds(deadline))
                yield context
            finally:
                try:
                    if context is not None:
                        context.close()
                finally:
                    if browser is not None:
                        browser.close()
    except TimeoutError:
        raise _Failure("unavailable", "timeout", "Guest browser timed out; no retry was made.") from None
    except Error:
        raise _Failure("unavailable", "browser_error", "Guest Chromium failed; check the executable and optional dependency. No retry was made.") from None


def _navigate(context, url, marketplace, result, deadline, product=None):
    attempt = {"url": url, "source_mode": result["source_mode"], "attempted_at": utc_now(), "status": "unavailable"}
    result["access"]["attempts"].append(attempt)
    guest._check_gate(attempt)
    page = context.new_page()
    guard = _Navigation(marketplace, url, product)
    page.route("**/*", guard.handle)
    try:
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=_milliseconds(deadline))
        except Exception:
            if guard.failure:
                raise guard.failure from None
            raise
        if guard.failure:
            raise guard.failure
        attempt["final_url"] = page.url
        _check_page(page, response)
        adapters._remaining(deadline)
        attempt.update(status="ok", final_url=page.url)
        return page
    except _Failure as exc:
        attempt.update(status=exc.status, error_code=exc.code)
        if guard.denied_url:
            attempt["denied_url"] = guard.denied_url
            if exc.code == "challenge":
                attempt["challenge_url"] = guard.denied_url
        guest._record_gate(attempt, exc)
        page.close()
        raise
    except Exception:
        attempt.update(status="unavailable", error_code="browser_error")
        page.close()
        raise


def _redirect_link(href):
    url = urljoin("https://www.google.com", href)
    return url if guest._valid_url(url, _GOOGLE_HOSTS) and urlsplit(url).path in {"/url", "/goto"} else None


def _base(marketplace, filters=None):
    result = guest._envelope(marketplace, filters)
    result["access"].update(backend="playwright_chromium", profile="ephemeral_incognito")
    return result


def search_browser_guest(marketplace, query, limit=10, timeout=30, filters=None, executable_path=None) -> dict:
    """One Google page, at most ten product leads; never parse indexed prices."""
    marketplace = marketplace_name(marketplace)
    original_query = query
    query = adapters._text(query, "query")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("limit must be an integer from 1 to 1000")
    deadline = time.monotonic() + adapters._timeout(timeout)
    result = _base(marketplace, filters)
    search_query = f"site:{_DOMAINS[marketplace]} {query}"
    result.update(source_mode="search_index", coverage="discovery_only", query=original_query, search_query=search_query)
    result["warnings"].append("Discovery only: indexed text may be stale; no current prices, stock, native filters or complete inventory are established.")
    if limit > 10:
        result["warnings"].append("Requested limit capped at 10; only one index page is read.")
    limit = min(limit, 10)
    search_url = "https://www.google.com/search?" + urlencode({"q": search_query})
    try:
        with _browser_context(executable_path, deadline) as context:
            page = _navigate(context, search_url, marketplace, result, deadline)
            try:
                # A single bounded wait lets an ordinary rendered result arrive;
                # it does not reload or retry a request after a challenge.
                try:
                    page.wait_for_function("() => document.querySelector('h3') || /did not match any documents|No results found|找不到和|没有找到|unusual traffic|verify.{0,25}human|非法访问|安全验证/i.test(document.body.innerText)", timeout=_milliseconds(deadline))
                except Exception:
                    _check_page(page)
                    raise
                state = _check_page(page)
                cards = page.evaluate(_CARDS_JS)
                index_url = page.url
                seen, resolved = set(), set()
                result["rejected_routes"] = {"count": 0, "reason": "not_a_supported_first_party_product_route"}
                for card in cards[:40]:
                    adapters._remaining(deadline)
                    href, title = card.get("href", ""), card.get("title", "")
                    if not isinstance(href, str) or not isinstance(title, str) or not title.strip():
                        continue
                    url = guest._discovery_url(marketplace, href)
                    redirect = _redirect_link(href) if not url else None
                    if redirect and redirect not in resolved:
                        resolved.add(redirect)
                        # Bound work even if all index entries are irrelevant.
                        if len(resolved) > 10:
                            continue
                        target = _navigate(context, redirect, marketplace, result, deadline)
                        try:
                            url = guest._discovery_url(marketplace, target.url)
                        finally:
                            target.close()
                    if not url:
                        result["rejected_routes"]["count"] += 1
                        continue
                    if url in seen:
                        continue
                    seen.add(url)
                    snippet = card.get("snippet", "")
                    snippet = snippet if isinstance(snippet, str) else ""
                    result["items"].append({"title": title.strip(), "snippet": snippet, "description": snippet,
                                            "item_id": guest._item_id(marketplace, url), "url": url, "nativeURL": url,
                                            "price": None, "currency": CURRENCIES[marketplace],
                                            "price_basis": "indexed_text_only", "source_mode": "search_index",
                                            "coverage": "discovery_only", "discovered_at": utc_now(),
                                            "index_source_url": index_url, "index_result_href": href})
                    if len(result["items"]) >= limit:
                        break
                if result["items"]:
                    result["status"] = "discovery_only"
                elif cards or re.search(r"did not match any documents|No results found|找不到和|没有找到", state.get("text", "")):
                    result.update(status="empty_unverified", error={"code": "index_no_results", "message": "No validated native product leads; native matches remain unknown."})
                else:
                    raise _Failure("unavailable", "index_parse_error", "No recognized rendered index result cards.")
            finally:
                page.close()
        return result
    except _Failure as exc:
        return guest._failure(result, exc)


def get_browser_guest_item(marketplace, url_or_id, timeout=30, executable_path=None) -> dict:
    """Read an exact public product; unsupported schemas remain unavailable.

    JD and Blibli reuse identity-bound JSON contracts. Goofish uses bounded
    primary-item DOM; Taobao still has no validated detail contract.
    """
    marketplace = marketplace_name(marketplace)
    value = adapters._text(url_or_id, "url_or_id")
    deadline = time.monotonic() + adapters._timeout(timeout)
    result = _base(marketplace)
    result["source_mode"] = "guest_product_page"
    if marketplace != "blibli" and re.fullmatch(r"[0-9]+", value):
        value = {"jd": f"https://item.jd.com/{value}.html", "taobao": f"https://item.taobao.com/item.htm?id={value}",
                 "goofish": f"https://www.goofish.com/item?id={value}"}[marketplace]
    url = guest._product_url(marketplace, value)
    if not url and guest._discovery_url(marketplace, value):
        return guest._failure(result, _Failure("unavailable", "numeric_sku_unresolved", "Opaque product link is discovery only; numeric SKU is unresolved."))
    if not url:
        return guest._failure(result, _Failure("unavailable", "detail_url_required", "An exact native product URL or Chinese marketplace numeric item ID is required."))
    result["product_url"] = url
    try:
        with _browser_context(executable_path, deadline) as context:
            page = _navigate(context, url, marketplace, result, deadline, product=url)
            try:
                if guest._product_url(marketplace, page.url) != url:
                    raise _Failure("unavailable", "item_url_mismatch", "Rendered URL does not match the requested item.")
                if marketplace == "goofish":
                    from .goofish_public import CAPTURE_JS, parse_capture
                    page.wait_for_function(
                        "() => document.querySelector('[class^=\"item-main-container--\"] [class^=\"notLoginContainer--\"] [class^=\"main--\"]') || /宝贝被删掉|已下架|商品不存在|非法访问|安全验证|请登录后/.test(document.body.innerText)",
                        timeout=_milliseconds(deadline))
                    _check_page(page)
                    try:
                        rows = [parse_capture(page.evaluate(CAPTURE_JS), url)]
                    except ValueError:
                        raise _Failure("unavailable", "item_schema_unverified", "No complete identity-bound Goofish primary item DOM was validated.") from None
                else:
                    parser = guest._html(page.content())
                    if marketplace == "jd":
                        rows = guest._jd_detail(parser, guest._item_id(marketplace, url), url)
                    elif marketplace == "blibli":
                        rows = guest._blibli_detail(parser, url)
                    else:
                        raise _Failure("unavailable", "item_schema_unverified", "No verified primary-item DOM contract; description, price and availability remain unknown.")
                result.update(status="ok", items=rows)
                result["warnings"].append("Public source claims only; availability, selected variant and checkout price remain unverified.")
            finally:
                page.close()
        return result
    except _Failure as exc:
        return guest._failure(result, exc)
