"""Cookie-free, bounded public discovery and conservatively bound item detail.

Search-index text is a discovery lead, never a current offer or inventory count.
No browser, OpenCLI, login, retry, or challenge-solving path is used here.
"""

from __future__ import annotations

import hashlib
import http.client
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from contextvars import ContextVar
from html.parser import HTMLParser

from . import adapters
from .marketplaces import (
    _QUERY_ID_KEYS,
    DISCOVERY_DOMAINS,
    PRODUCT_HOSTS,
    PUBLIC_METADATA_MARKETPLACES,
    canonical_product_url,
    item_url,
    product_id,
)
from .models import CURRENCIES, marketplace_name, utc_now

MAX_RESPONSE_BYTES = 2 * 1024 * 1024

_DOMAINS = DISCOVERY_DOMAINS
_Failure = adapters._Failure
_ACCESS_GATES = ContextVar("china_deals_access_gates", default=None)
_GATE_CODES = {"challenge", "http_401", "http_403", "http_429"}


@contextmanager
def access_session():
    """Share host gates within one command only; never persist credentials or bans."""
    token = _ACCESS_GATES.set({})
    try:
        yield
    finally:
        _ACCESS_GATES.reset(token)


def _gate_key(url):
    return urllib.parse.urlsplit(url).hostname


def _check_gate(attempt):
    gates = _ACCESS_GATES.get()
    origin = gates.get(_gate_key(attempt["url"])) if gates is not None else None
    if origin:
        attempt.update(status="skipped_after_challenge", error_code="skipped_after_challenge",
                       network_attempted=False, gate_origin=dict(origin))
        raise _Failure("blocked", "skipped_after_challenge", "This host already requested verification in this invocation; no new request was sent.")
    attempt["network_attempted"] = True


def _record_gate(attempt, exc):
    if exc.code not in _GATE_CODES:
        return
    url = getattr(exc, "challenge_url", None) or attempt.get("challenge_url") or attempt.get("final_url") or attempt["url"]
    attempt["challenge_url"] = url
    gates = _ACCESS_GATES.get()
    if gates is not None:
        origin = {"url": url, "request_url": attempt["url"], "code": exc.code, "observed_at": utc_now()}
        gates.setdefault(_gate_key(url), origin)



def _valid_url(value, hosts):
    if not isinstance(value, str) or re.search(r"[\\\s\x00-\x1f\x7f]", value):
        return False
    try:
        p = urllib.parse.urlsplit(value)
        return (p.scheme == "https" and p.hostname in hosts and p.netloc == p.hostname
                and p.port is None and not p.username and not p.password)
    except ValueError:
        return False


def _product_url(marketplace, value):
    """Exact first-party product routes only; drop tracking and fragments."""
    if marketplace != "blibli":
        return canonical_product_url(marketplace, value)
    if not _valid_url(value, {"www.blibli.com"}):
        return None
    try:
        return adapters._blibli_product_url(value)
    except _Failure:
        return None


def _discovery_url(marketplace, value):
    """Opaque JD links are leads only; they never establish a numeric SKU."""
    native = _product_url(marketplace, value)
    if native:
        return native
    if marketplace == "jd" and _valid_url(value, {"item.jd.com"}):
        parsed = urllib.parse.urlsplit(value)
        if any(key.casefold() in _QUERY_ID_KEYS for key, _ in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)):
            return None
        path = parsed.path
        if re.fullmatch(r"/product/[A-Za-z0-9_-]{1,128}\.html", path):
            return "https://item.jd.com" + path
    return None


def _item_id(marketplace, url):
    if marketplace in PUBLIC_METADATA_MARKETPLACES:
        return product_id(marketplace, url)
    p = urllib.parse.urlsplit(url)
    if marketplace in {"taobao", "goofish"}:
        return urllib.parse.parse_qs(p.query)["id"][0]
    if marketplace == "jd":
        native = _product_url(marketplace, url)
        if not native:
            return None
        match = re.fullmatch(r"/([0-9]+)\.html", urllib.parse.urlsplit(native).path)
        return match[1] if match else None
    return p.path.rstrip("/").split("--")[-1]


class _Redirects(urllib.request.HTTPRedirectHandler):
    def __init__(self, hosts, deadline):
        self.hosts, self.deadline = hosts, deadline

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        try:
            adapters._remaining(self.deadline)
            if not _valid_url(newurl, self.hosts):
                raise _Failure("blocked", "redirect_denied", "Guest redirect left the allowed HTTPS host; stopped.")
            if re.search(r"/(?:login|signin|captcha|challenge|verify|punish|_____tmd_____)(?:[/?]|$)", newurl, re.I):
                raise _Failure("blocked", "challenge", "Guest request reached login or verification; stopped.")
        except _Failure as exc:
            if exc.code == "challenge":
                exc.challenge_url = newurl
            if fp is not None:
                fp.close()
            raise
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None:
            req.timeout = redirected.timeout = adapters._remaining(self.deadline)
        return redirected


def _fetch(url, hosts, deadline):
    if not _valid_url(url, hosts):
        raise _Failure("blocked", "url_denied", "Guest URL is outside the allowed HTTPS host.")
    # A new opener has no cookie jar, auth handlers, or dependency on global/browser state.
    opener = urllib.request.build_opener(_Redirects(hosts, deadline))
    request = urllib.request.Request(url, headers={"User-Agent": "china-deals/0.6", "Accept": "text/html,application/json",
                                                   "Cache-Control": "no-cache", "Pragma": "no-cache"})
    try:
        with opener.open(request, timeout=adapters._remaining(deadline)) as response:
            if not _valid_url(response.geturl(), hosts):
                raise _Failure("blocked", "redirect_denied", "Guest response left the allowed HTTPS host.")
            chunks, size = [], 0
            while True:
                remaining = adapters._remaining(deadline)
                sock = getattr(getattr(getattr(response, "fp", None), "raw", None), "_sock", None)
                if sock is not None:
                    sock.settimeout(remaining)
                # read1 returns after one buffered/raw read, allowing deadline checks between chunks.
                chunk = response.read1(min(65536, MAX_RESPONSE_BYTES + 1 - size))
                adapters._remaining(deadline)
                size += len(chunk)
                if size > MAX_RESPONSE_BYTES:
                    raise _Failure("error", "output_limit", "Guest response exceeded 2 MiB.")
                if not chunk:
                    # HTTPResponse.read1() can silently reach EOF before a fixed
                    # Content-Length is satisfied (unlike read()).
                    outstanding = getattr(response, "length", None)
                    if isinstance(outstanding, int) and outstanding > 0:
                        raise _Failure("unavailable", "incomplete_response", "Guest response ended before its declared length; no retry was made.")
                    break
                chunks.append(chunk)
            charset = response.headers.get_content_charset() or "utf-8"
            try:
                body = b"".join(chunks).decode(charset, errors="replace")
            except LookupError:
                body = b"".join(chunks).decode("utf-8", errors="replace")
            return body, response.geturl()
    except urllib.error.HTTPError as exc:
        exc.close()
        status = "auth_required" if exc.code == 401 else "blocked" if exc.code in {403, 429} else "unavailable"
        failure = _Failure(status, f"http_{exc.code}", f"Guest request returned HTTP {exc.code}; no retry was made.")
        failure.challenge_url = exc.url
        raise failure from None
    except (urllib.error.URLError, OSError, TimeoutError, http.client.HTTPException):
        raise _Failure("unavailable", "network_error", "Guest request failed or timed out; no retry was made.") from None


class _HTML(HTMLParser):
    """Capture DDG result anchors/snippets and script bodies without executing them."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.results, self.scripts, self.visible = [], [], []
        self.capture = None
        self.script = None
        self.no_results = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get("class", "").split()
        if "no-results" in classes or "result--no-result" in classes:
            self.no_results = True
        if tag == "script":
            self.script = [attrs.get("type", ""), []]
        if "result__a" in classes and tag == "a":
            self.results.append({"href": attrs.get("href", ""), "title": "", "snippet": ""})
            self.capture = [tag, "title", []]
        elif "result__snippet" in classes and self.results:
            self.capture = [tag, "snippet", []]

    def handle_data(self, data):
        if self.script is not None:
            self.script[1].append(data)
        else:
            self.visible.append(data)
            if self.capture:
                self.capture[2].append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.script is not None:
            self.scripts.append((self.script[0], "".join(self.script[1])))
            self.script = None
        if self.capture and tag == self.capture[0]:
            self.results[-1][self.capture[1]] = " ".join("".join(self.capture[2]).split())
            self.capture = None


def _html(body):
    parser = _HTML()
    parser.source_body = body
    parser.feed(body)
    text = " ".join(parser.visible).lower()
    if (re.search(r"anomaly\.js|anomaly-modal|challenge-form|cf-chl-|(?:id|class)\s*=\s*['\"][^'\"]*(?:captcha|recaptcha)", body, re.I)
            or re.search(r"<title[^>]*>[^<]*(?:captcha|access denied|just a moment|security check|登录|登陆|验证|\blogin\b|sign in)", body, re.I)
            or re.search(r"verify.{0,25}human|just a moment|access denied|verifikasi sedang|京东验证|"
                         r"unusual traffic|our systems have detected|非法访问|请使用正常浏览器|滑动验证|安全验证|完成验证|"
                         r"检测到异常流量|我们的系统检测到|请先登录|请登录后|登录后查看|登录后继续|"
                         r"sign in to continue|log in to continue|slide.{0,20}verif", text)):
        raise _Failure("blocked", "challenge", "Guest page requested login or verification; no retry or bypass was attempted.")
    return parser


def _unwrap(href):
    url = urllib.parse.urljoin("https://html.duckduckgo.com", href)
    if _valid_url(url, {"duckduckgo.com", "html.duckduckgo.com"}):
        p = urllib.parse.urlsplit(url)
        if p.path == "/l/":
            targets = urllib.parse.parse_qs(p.query).get("uddg", [])
            return targets[0] if len(targets) == 1 else ""
    return url


def _filters(filters):
    if filters is not None and not isinstance(filters, dict):
        raise ValueError("filters must be an object or None")
    return {"status": "not_applied" if filters else "not_requested", "requested": dict(filters or {}),
            "applied": {}, "residual": dict(filters or {}),
            "reason": "Guest search does not apply native marketplace filters; local review is required."}


def _envelope(marketplace, filters=None):
    return {"marketplace": marketplace, "status": "unavailable", "items": [], "warnings": [], "error": None,
            "access": {"mode": "guest", "authenticated": False, "attempts": []},
            "native_filters": _filters(filters)}


def _failure(result, exc):
    attempts = result.get("access", {}).get("attempts", [])
    if attempts and exc.code in _GATE_CODES:
        attempts[-1].update(status=exc.status, error_code=exc.code)
        _record_gate(attempts[-1], exc)
    result.update(status=exc.status, items=[], error={"code": exc.code, "message": exc.message})
    for key in ('parser_reason', 'response_text_sha256'):
        value = getattr(exc, key, None)
        if isinstance(value, str):
            result['error'][key] = value
    return result


def _read(result, url, hosts, deadline, mode):
    attempt = {"url": url, "source_mode": mode, "attempted_at": utc_now(), "status": "unavailable"}
    result["access"]["attempts"].append(attempt)
    _check_gate(attempt)
    try:
        body, final_url = _fetch(url, hosts, deadline)
        attempt["final_url"] = final_url
        _html(body)  # Also reject HTTP-200 challenge bodies before JSON parsing.
        attempt.update(status="ok", final_url=final_url)
        return body, final_url
    except _Failure as exc:
        attempt.update(status=exc.status, error_code=exc.code)
        _record_gate(attempt, exc)
        raise


def search_guest(marketplace, query, limit=10, timeout=30, filters=None) -> dict:
    """Read one public page. Index leads deliberately carry no numeric prices."""
    marketplace = marketplace_name(marketplace)
    query = adapters._text(query, "query")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("limit must be an integer from 1 to 1000")
    deadline = time.monotonic() + adapters._timeout(timeout)
    result = _envelope(marketplace, filters)
    requested_limit = limit
    limit = min(limit, 60 if marketplace == "blibli" else 10)
    if limit != requested_limit:
        result["warnings"].append(f"Requested limit capped at {limit}; guest search reads page one only.")
    if marketplace == "blibli":
        result["warnings"].append("Blibli prices are IDR; no Fansbuy freight route is established.")
        url = adapters._blibli_search_url(query, limit)
        try:
            body, _ = _read(result, url, {"www.blibli.com"}, deadline, "guest_api")
            rows = adapters._blibli_rows(json.loads(body))[:limit]
            result.update(status="ok" if rows else "empty_unverified", items=rows)
            result["source_mode"] = "guest_api"
            return result
        except (_Failure, ValueError, RecursionError) as exc:
            code = exc.code if isinstance(exc, _Failure) else "invalid_json"
            attempt = result["access"]["attempts"][-1]
            if attempt["status"] != "skipped_after_challenge":
                attempt.update(status=getattr(exc, "status", "error"), error_code=code)
            result["warnings"].append(f"Public Blibli API unavailable ({code}); index discovery is separate evidence.")
    result.update(source_mode="search_index", coverage="discovery_only")
    result["warnings"].append("Discovery only: search-index text may be stale; it proves neither current prices nor full inventory. Native filters were not applied.")
    search_url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": f"site:{_DOMAINS[marketplace]} {query}"})
    try:
        body, final_url = _read(result, search_url, {"html.duckduckgo.com"}, deadline, "search_index")
        parser = _html(body)
        seen = set()
        result["rejected_routes"] = {"count": 0, "reason": "not_a_supported_first_party_product_route"}
        for entry in parser.results:
            url = _discovery_url(marketplace, _unwrap(entry["href"]))
            if not url:
                result["rejected_routes"]["count"] += 1
                continue
            if url in seen or not entry["title"]:
                continue
            seen.add(url)
            result["items"].append({"title": entry["title"], "snippet": entry["snippet"],
                                    "description": entry["snippet"], "item_id": _item_id(marketplace, url),
                                    "url": url, "nativeURL": url, "price": None,
                                    "price_basis": "indexed_text_only", "currency": CURRENCIES[marketplace],
                                    "source_mode": "search_index", "coverage": "discovery_only",
                                    "discovered_at": utc_now(), "index_source_url": final_url})
            if len(result["items"]) >= limit:
                break
        if result["items"]:
            result["status"] = "discovery_only"
        elif parser.results or parser.no_results:
            result.update(status="empty_unverified", error={"code": "index_no_results", "message": "No validated product leads on this index page; native matches remain unknown."})
        else:
            raise _Failure("unavailable", "index_parse_error", "No recognized index result schema; zero matches cannot be inferred.")
        return result
    except _Failure as exc:
        return _failure(result, exc)


def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("Duplicate JSON key")
        obj[key] = value
    return obj


def _reject_constant(value):
    raise ValueError(f"Non-JSON constant: {value}")


def _decode_assignment(text):
    """Decode a balanced JSON object, allowing only JS trailing commas.

    JD's retained public response has one trailing outer-object comma. Remove
    commas before closing braces/brackets only outside strings; all other JS
    syntax (comments, expressions, executable values) still fails JSON decoding.
    """
    text = text.lstrip()
    if text.startswith("("):
        text = text[1:].lstrip()
    if not text.startswith("{"):
        raise ValueError("Expected JSON object")
    stack, quoted, escaped, out = [], False, False, []
    for i, char in enumerate(text):
        if quoted:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char in "{[":
            stack.append(char)
        elif char in "}]":
            if not stack or stack.pop() != {"}": "{", "]": "["}[char]:
                raise ValueError("Unbalanced JSON")
        following = i + 1
        if char == ",":
            while following < len(text) and text[following].isspace():
                following += 1
        if char != "," or following >= len(text) or text[following] not in "}]":
            out.append(char)
        if not stack:
            decoder = json.JSONDecoder(object_pairs_hook=_unique_object, parse_constant=_reject_constant)
            return decoder.raw_decode("".join(out))[0]
    raise ValueError("Unterminated JSON")


def _amount(value):
    # No currency stripping, ranges, localized separators, exponents, or masks.
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    text = str(value).strip()
    if len(text) < 24 and re.fullmatch(r"[0-9]+(?:\.[0-9]{1,2})?", text) and float(text) > 0:
        return text
    return None


def _jd_detail(parser, item_id, url):
    matches = []
    for _, script in parser.scripts:
        for match in re.finditer(r"\bwindow\._itemInfo\s*=\s*", script):
            try:
                data = _decode_assignment(script[match.end():])
            except (ValueError, RecursionError):
                continue
            product = data.get("product")
            if not isinstance(product, dict) or str(product.get("skuId")) != item_id:
                continue
            if not isinstance(product.get("skuName"), str) or not product["skuName"].strip():
                continue
            selected = {key: product[key] for key in ("skuId", "skuName", "spec", "specName", "color", "size", "brandName", "salesAttr") if key in product}
            floor = data.get("priceFloor")
            floor = floor if isinstance(floor, dict) else {}
            price = _amount(floor.get("price"))
            if "skuId" in floor and str(floor["skuId"]) != item_id:
                price = None
            matches.append({"title": product["skuName"].strip(),
                            "description": "; ".join(f"{k}: {v}" for k, v in selected.items() if isinstance(v, (str, int))),
                            "item_id": item_id, "url": url, "nativeURL": url,
                            "currency": "CNY", "price": price, "source_mode": "guest_product_page",
                            "observed_at": utc_now(), "detail": {"product": selected, "priceFloor": {k: floor[k] for k in ("price", "skuId", "type") if k in floor}}})
    if len(matches) != 1:
        raise _Failure("unavailable", "item_schema_unverified", "No unique SKU-bound JD product JSON was validated.")
    return matches


def _jsonld_nodes(value):
    if isinstance(value, list):
        for entry in value:
            yield from _jsonld_nodes(entry)
    elif isinstance(value, dict):
        yield value
        yield from _jsonld_nodes(value.get("@graph"))


def _stock_claims(product, offer):
    def enum(value):
        return value.rsplit("/", 1)[-1].rsplit("#", 1)[-1] if isinstance(value, str) else None
    values = [enum(obj.get("availability")) for obj in (product, offer) if obj.get("availability") is not None]
    unavailable = {"OutOfStock", "SoldOut", "Discontinued"}
    warnings = []
    if any(v in unavailable for v in values):
        availability = "unavailable"
    elif values and all(v == "InStock" for v in values):
        availability = "source_claimed_available"
    else:
        availability = "unknown"
    if len(set(values)) > 1:
        warnings.append("Product and Offer availability claims conflict; checkout stock is unresolved.")
    conditions = [enum(obj.get("itemCondition")) for obj in (product, offer) if obj.get("itemCondition") is not None]
    mapping = {"NewCondition": "new", "UsedCondition": "used", "RefurbishedCondition": "refurbished", "DamagedCondition": "damaged"}
    condition = mapping.get(conditions[0], "unknown") if conditions and len(set(conditions)) == 1 else "unknown"
    if len(set(conditions)) > 1:
        warnings.append("Product and Offer condition claims conflict.")
    return availability, condition, warnings


def _blibli_detail(parser, url, observed_at=None):
    observed_at = observed_at or utc_now()
    source_body = getattr(parser, 'source_body', '')
    if "__PRODUCT_DETAIL_INITIAL_STATE__" in source_body:
        from .blibli_public import parse_product_state
        try:
            row = parse_product_state(source_body, url, observed_at)
            row['source_detail']['response_text_sha256'] = hashlib.sha256(source_body.encode('utf-8')).hexdigest()
            return [row]
        except ValueError as exc:
            text = str(exc).casefold()
            reason = ('currency_conflict' if 'currency' in text else
                      'selected_option_or_attributes_invalid' if 'attribute' in text or 'option' in text or 'dimensionless' in text else
                      'identity_binding_invalid' if 'sku' in text or 'pickup' in text or 'url' in text else
                      'price_object_invalid' if 'price' in text else 'primary_state_invalid')
            failure = _Failure("unavailable", "item_state_unverified", "Primary Blibli state could not establish a unique selected product price.")
            failure.parser_reason = reason
            failure.response_text_sha256 = hashlib.sha256(source_body.encode('utf-8')).hexdigest()
            raise failure from None
    matches = []
    for kind, script in parser.scripts:
        if kind.lower() != "application/ld+json":
            continue
        try:
            payload = json.loads(script, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        except (ValueError, RecursionError):
            continue
        for product in _jsonld_nodes(payload):
            types = product.get("@type")
            if types != "Product" and not (isinstance(types, list) and "Product" in types):
                continue
            if (_product_url("blibli", product.get("url")) != url
                    or not isinstance(product.get("name"), str) or not product["name"].strip()):
                continue
            offers = product.get("offers")
            offers = offers if isinstance(offers, list) else [offers]
            if len(offers) != 1 or not isinstance(offers[0], dict) or offers[0].get("@type") != "Offer":
                continue
            offer = offers[0]
            if offer.get("url") is not None and _product_url("blibli", offer["url"]) != url:
                continue
            price = _amount(offer.get("price")) if offer.get("priceCurrency") == "IDR" else None
            availability, condition, stock_warnings = _stock_claims(product, offer)
            matches.append({"availability": availability, "condition": condition, "source_warnings": stock_warnings,
                            "title": product["name"], "description": product.get("description", ""),
                            "item_id": _item_id("blibli", url), "url": url, "nativeURL": url,
                            "currency": "IDR", "price": price, "source_mode": "guest_product_page",
                            "observed_at": observed_at, "detail": {"product": {k: product[k] for k in ("name", "description", "sku", "url", "availability", "itemCondition") if k in product}, "offer": offer}})
    if len(matches) != 1:
        raise _Failure("unavailable", "item_schema_unverified", "No unique URL-bound Blibli Product and Offer JSON-LD was validated.")
    return matches


def get_guest_item(marketplace, item_id, timeout=30) -> dict:
    """Read validated public JD JSON / Blibli selected product state or JSON-LD."""
    marketplace = marketplace_name(marketplace)
    item_id = adapters._text(item_id, "item_id")
    deadline = time.monotonic() + adapters._timeout(timeout)
    result = _envelope(marketplace)
    if marketplace in PUBLIC_METADATA_MARKETPLACES:
        url = _product_url(marketplace, item_id) or item_url(marketplace, item_id)
        if not url:
            raise ValueError("Supply an ASCII numeric item ID or exact native product URL")
        result["product_url"] = url
        try:
            body, final_url = _read(result, url, PRODUCT_HOSTS[marketplace], deadline, "guest_product_page")
            if _product_url(marketplace, final_url) != url:
                raise _Failure("unavailable", "item_url_mismatch", "Guest detail redirected away from the requested product.")
            from .china_public import parse_product_page
            try:
                row = parse_product_page(body, marketplace, url, utc_now())
            except ValueError:
                failure = _Failure("unavailable", "item_schema_unverified", "No identity-bound primary product evidence was validated.")
                failure.response_text_sha256 = hashlib.sha256(body.encode('utf-8')).hexdigest()
                raise failure from None
            result.update(status="ok", items=[row], source_mode="guest_product_page")
            result['warnings'].append("Public product evidence only; selected variant, current inventory, full payable price and checkout remain unverified.")
            return result
        except _Failure as exc:
            return _failure(result, exc)
    if marketplace == "blibli":
        url = _product_url(marketplace, item_id)
        if not url:
            return _failure(result, _Failure("unavailable", "detail_url_required", "Blibli detail requires an exact native product URL."))
        fetch_url = url
        hosts = {"www.blibli.com"}
    else:
        if not re.fullmatch(r"[0-9]+", item_id):
            native_url = _product_url(marketplace, item_id)
            if not native_url and _discovery_url(marketplace, item_id):
                return _failure(result, _Failure("unavailable", "numeric_sku_unresolved", "Opaque product link retained as discovery; a numeric SKU is not verified."))
            if not native_url:
                raise ValueError("Supply an ASCII numeric item ID or an exact native product URL")
            item_id = _item_id(marketplace, native_url)
        url = {"jd": f"https://item.jd.com/{item_id}.html", "taobao": f"https://item.taobao.com/item.htm?id={item_id}",
               "goofish": f"https://www.goofish.com/item?id={item_id}"}[marketplace]
        fetch_url = f"https://item.m.jd.com/product/{item_id}.html"
        hosts = {"item.m.jd.com"}
    result["product_url"] = url
    if marketplace in {"taobao", "goofish"}:
        return _failure(result, _Failure("unavailable", "item_schema_unverified", "No validated first-party guest detail schema is implemented; product link only."))
    try:
        body, final_url = _read(result, fetch_url, hosts, deadline, "guest_product_page")
        if _product_url(marketplace, final_url) != url:
            raise _Failure("unavailable", "item_url_mismatch", "Guest detail redirected away from the requested product.")
        parser = _html(body)
        rows = _jd_detail(parser, item_id, url) if marketplace == "jd" else _blibli_detail(parser, url)
        result.update(status="ok", items=rows, source_mode="guest_product_page")
        result["warnings"].append("Public product fields are source claims; availability, variant and checkout price remain unverified.")
        if rows[0]["price"] is None:
            result["warnings"].append("Price is masked, missing or ambiguous; no amount is available for ranking.")
        return result
    except _Failure as exc:
        return _failure(result, exc)
