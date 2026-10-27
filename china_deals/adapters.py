"""Read-only marketplace boundaries; returned items retain upstream row shapes.

OpenCLI's browser bridge uses the user's existing session. This module never
logs in, solves verification, submits orders, or runs caller-supplied JavaScript.
"""

from __future__ import annotations

import json
import math
import os
import re
import selectors
import signal
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from .models import marketplace_name

OPENCLI_VERSION = "2.0.2"
MAX_OUTPUT_BYTES = 2 * 1024 * 1024
_LIMITS = {"taobao": 40, "jd": 30, "goofish": 60, "blibli": 60}
_SITE = {"taobao": "taobao", "jd": "jd", "goofish": "xianyu"}
_BLIBLI = "https://www.blibli.com"
_WARNINGS = {
    "jd": ["JD 2.0.2 has weak login/challenge detection; empty extraction does not prove zero matches."],
    "blibli": ["Blibli is Indonesia (IDR); China/Fansbuy shipping eligibility is unverified."],
}


class _Failure(Exception):
    def __init__(self, status, code, message):
        self.status, self.code, self.message = status, code, message
        super().__init__(message)


def _result(marketplace, items=None, failure=None, warnings=()):
    rows = items if items is not None else []
    return {
        "marketplace": marketplace,
        "status": failure.status if failure else ("ok" if rows else "empty_unverified"),
        "items": rows if not failure else [],
        "warnings": list(_WARNINGS.get(marketplace, ())) + list(warnings),
        "error": {"code": failure.code, "message": failure.message} if failure else None,
    }


def _marketplace(value):
    return marketplace_name(value)


def _text(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 4096 or "\0" in value:
        raise ValueError(f"{name} must be a nonempty string of at most 4096 characters without NUL")
    return value.strip()


def _timeout(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
        raise ValueError("timeout must be a finite positive number")
    return float(value)


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise _Failure("unavailable", "timeout", "The read-only operation timed out; no automatic retry was made.")
    return remaining


def _run(argv, timeout):
    """Drain both pipes with a hard combined cap; kill/reap on timeout or overflow.

    communicate()/capture_output alone accumulate unbounded output. No shell,
    stdin, or raw stderr is exposed. POSIX process groups cover CLI descendants.
    """
    deadline = time.monotonic() + _timeout(timeout)
    try:
        process = subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=False, start_new_session=(os.name == "posix"),
        )
    except OSError:
        raise _Failure("unavailable", "executable_unavailable", "OpenCLI could not be executed; install the pinned version or supply its executable path.") from None
    streams = {"stdout": bytearray(), "stderr": bytearray()}
    size = 0
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ, "stdout")
            selector.register(process.stderr, selectors.EVENT_READ, "stderr")
            while selector.get_map():
                for key, _ in selector.select(_remaining(deadline)):
                    chunk = os.read(key.fileobj.fileno(), min(65536, MAX_OUTPUT_BYTES - size + 1))
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    size += len(chunk)
                    if size > MAX_OUTPUT_BYTES:
                        raise _Failure("error", "output_limit", "OpenCLI exceeded the bounded output limit; output was discarded.")
                    streams[key.data].extend(chunk)
            process.wait(timeout=_remaining(deadline))
    except subprocess.TimeoutExpired:
        raise _Failure("unavailable", "timeout", "OpenCLI timed out; no automatic retry was made.") from None
    finally:
        # A child may still hold a pipe even after the immediate process exited.
        if process.poll() is None or time.monotonic() >= deadline or size > MAX_OUTPUT_BYTES:
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
        process.wait()
        process.stdout.close()
        process.stderr.close()
    return process.returncode, bytes(streams["stdout"])


def _loads(raw):
    try:
        # Preserve decimal literals without a binary float round-trip.
        return json.loads(raw, parse_float=str, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError):
        raise _Failure("error", "invalid_json", "The backend did not return a complete valid JSON response.") from None


def _backend_failure(error):
    if not isinstance(error, dict):
        return _Failure("error", "invalid_envelope", "OpenCLI returned an invalid error envelope.")
    code = str(error.get("code", "UNKNOWN"))[:80]
    evidence = " ".join(str(error.get(k, ""))[:2000] for k in ("code", "message", "hint")).lower()
    # Xianyu detail encodes a verification block as EMPTY_RESULT with a hint.
    if re.search(r"captcha|verification|risk control|blocked|forbidden|rate.limit|验证码|安全验证|异常访问", evidence):
        return _Failure("blocked", code, "The marketplace requires verification or blocked/rate-limited this read-only request.")
    if code.upper() == "AUTH_REQUIRED":
        return _Failure("auth_required", code, "The marketplace requires an existing authenticated browser session; no login was attempted.")
    if code.upper() == "EMPTY_RESULT":
        return _Failure("empty_unverified", code, "The backend extracted no data; a genuine zero-match result is unverified.")
    if code.upper() == "LOGIN_WALL":
        return _Failure("blocked", code, "The backend reported an ambiguous login wall/WAF response; authentication state is unverified.")
    if code.upper() in {"BROWSER_CONNECT", "CONFIG", "ADAPTER_LOAD", "TIMEOUT"} or code.lower() in {"no_extension", "extension_unavailable", "session_required"}:
        return _Failure("unavailable", code, "The OpenCLI browser bridge, configuration, or adapter is unavailable.")
    return _Failure("error", code, "OpenCLI reported a backend error; private backend output was withheld.")


def _wire(argv, timeout):
    exitcode, stdout = _run(argv, timeout)
    payload = _loads(stdout)
    if not isinstance(payload, dict) or type(payload.get("ok")) is not bool:
        raise _Failure("error", "invalid_envelope", "Expected the OpenCLI 2.0.2 JSON envelope.")
    if payload["ok"] is False:
        raise _backend_failure(payload.get("error"))
    if exitcode != 0:
        raise _Failure("error", "exit_status", "OpenCLI exited unsuccessfully despite a success envelope.")
    if "data" not in payload:
        raise _Failure("error", "invalid_envelope", "OpenCLI's success envelope omitted data.")
    return payload["data"]


def _version(executable, timeout):
    exitcode, stdout = _run([executable, "--version"], timeout)
    version = stdout.decode("utf-8", errors="replace").strip()
    if exitcode != 0 or version != OPENCLI_VERSION:
        raise _Failure("unavailable", "version_mismatch", "This adapter requires exactly OpenCLI 2.0.2; run doctor with the selected executable.")
    return version


def _rows(data):
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        raise _Failure("error", "invalid_rows", "The backend response did not contain an array of product rows.")
    return data


def _china_rows(marketplace, data, detail=False):
    rows = _rows(data)
    if detail and marketplace in {"taobao", "jd"}:
        fields = {row.get("field"): row.get("value") for row in rows if isinstance(row.get("field"), str)}
        title, url = str(fields.get("商品名称", "")), str(fields.get("链接", ""))
        if re.search(r"(?:passport\.jd|login\.taobao)\.com|(?:^|[-_\s])登录|用户登录|京东登录|欢迎登录|请先登录", title + " " + url):
            raise _Failure("auth_required", "login_page", "The detail extraction points to a login page; no login was attempted.")
        if re.search(r"验证码|安全验证|异常访问|captcha|verification|just a moment", title, re.I):
            raise _Failure("blocked", "verification_page", "The detail extraction points to a verification page.")
        if not title.strip() or not str(fields.get("价格", "")).strip():
            raise _Failure("empty_unverified", "incomplete_detail", "Detail lacks a product title or displayed price; page/session state is unverified.")
    return rows


def _blibli_search_url(query, limit):
    return _BLIBLI + "/backend/search/products?" + urllib.parse.urlencode({"searchTerm": query, "start": 0, "itemPerPage": limit})


def _blibli_rows(payload):
    if not isinstance(payload, dict):
        raise _Failure("error", "invalid_rows", "Blibli returned an unexpected product response.")
    code = str(payload.get("code", ""))
    if code in {"401", "403", "429"}:
        raise _Failure("auth_required" if code == "401" else "blocked", "http_" + code, "Blibli denied the product request; no verification or login was attempted.")
    if code and code != "200":
        raise _Failure("error", "blibli_api_error", "Blibli reported a product API error.")
    data = payload.get("data")
    if not isinstance(data, dict) or "products" not in data:
        raise _Failure("error", "invalid_rows", "Blibli response omitted data.products; zero matches cannot be inferred.")
    return _rows(data["products"])


def _blibli_http(query, limit, timeout):
    request = urllib.request.Request(_blibli_search_url(query, limit), headers={"Accept": "application/json", "User-Agent": "china-deals/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(MAX_OUTPUT_BYTES + 1)
            if len(body) > MAX_OUTPUT_BYTES:
                raise _Failure("error", "output_limit", "Blibli exceeded the bounded response limit.")
            content_type = response.headers.get("Content-Type", "").lower()
            if "json" not in content_type:
                raise _Failure("blocked", "non_json_response", "Blibli returned a non-JSON page, possibly a login wall or verification challenge.")
            return _blibli_rows(_loads(body))[:limit]
    except urllib.error.HTTPError as exc:
        exc.close()
        status = "auth_required" if exc.code == 401 else "blocked" if exc.code in {403, 429} else "unavailable"
        raise _Failure(status, f"http_{exc.code}", f"Blibli search returned HTTP {exc.code}; no login or verification was attempted.") from None
    except (urllib.error.URLError, OSError, TimeoutError):
        raise _Failure("unavailable", "network_error", "Blibli search could not be reached within the requested timeout.") from None


def _blibli_product_url(value):
    parsed = urllib.parse.urlsplit(value)
    slug = urllib.parse.unquote(parsed.path.split("/")[2]) if parsed.path.startswith("/p/") else ""
    if parsed.scheme == "https" and parsed.netloc == "www.blibli.com" and slug not in {"", ".", ".."} and not any(c in slug for c in "/\\") and re.fullmatch(r"/p/[A-Za-z0-9%._~-]+/(?:ps|is)--[A-Za-z0-9-]+/?", parsed.path):
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        pickup = query.get("pickupPointCode")
        if pickup is not None:
            if len(pickup) != 1 or not re.fullmatch(r"PP-[A-Z0-9-]+", pickup[0]):
                raise _Failure("unavailable", "detail_url_required", "Blibli pickupPointCode must identify one explicit pickup point.")
            return _BLIBLI + parsed.path + "?" + urllib.parse.urlencode({"pickupPointCode": pickup[0]})
        return _BLIBLI + parsed.path
    raise _Failure("unavailable", "detail_url_required", "Blibli detail needs the full native https://www.blibli.com/p/.../ps--... (or is--) product URL from search; no SKU-to-URL route is guessed.")


_PAGE_GUARD = """
const text = (document.title + ' ' + (document.body?.innerText || '').slice(0, 6000));
if (/just a moment|verify.*human|verifikasi sedang|captcha|access denied/i.test(text))
  return {state: 'blocked'};
if (/\\/(?:login|signin)(?:[/?]|$)/i.test(location.pathname)) return {state: 'auth_required'};
if (location.hostname !== 'www.blibli.com') return {state: 'unavailable'};
"""


def _blibli_browser(query_or_url, limit, deadline, executable, detail=False, warnings=None):
    _version(executable, _remaining(deadline))
    session = "china-deals-" + uuid.uuid4().hex
    prefix = [executable, "browser", "--session", session]
    if detail:
        url = _blibli_product_url(query_or_url)
        # JSON-LD is a standard product representation, not a claim that this
        # specific page currently provides it. Missing data stays unverified.
        script = """(() => {""" + _PAGE_GUARD + """
const products = [];
const walk = (v, depth=0) => {
  if (!v || typeof v !== 'object' || depth > 8 || products.length >= 60) return;
  if (Array.isArray(v)) { v.forEach(x => walk(x, depth+1)); return; }
  const types = Array.isArray(v['@type']) ? v['@type'] : [v['@type']];
  if (types.includes('Product')) products.push(v);
  if (v['@graph']) walk(v['@graph'], depth+1);
};
for (const node of Array.from(document.querySelectorAll('script[type="application/ld+json"]')).slice(0,100)) {
  if (node.textContent.length > 500000) continue;
  try { walk(JSON.parse(node.textContent)); } catch (_) {}
}
return {state: 'ok', products, url: location.href};
})()"""
    else:
        url = _BLIBLI + "/jual/" + urllib.parse.quote(query_or_url, safe="")
        endpoint = _blibli_search_url(query_or_url, limit)
        script = "(async () => {" + _PAGE_GUARD + """
const controller = new AbortController();
const timer = setTimeout(() => controller.abort(), 15000);
try {
  const response = await fetch(""" + json.dumps(endpoint) + """, {method:'GET', credentials:'same-origin', signal:controller.signal});
  if (!response.ok) return {state:response.status === 401 ? 'auth_required' : [403,429].includes(response.status) ? 'blocked' : 'unavailable', http_status:response.status};
  const body = await response.text();
  if (body.length > 1000000) return {state:'error'};
  try { return {state:'ok', payload:JSON.parse(body)}; } catch (_) { return {state:'blocked'}; }
} finally { clearTimeout(timer); }
})()"""
    try:
        _wire(prefix + ["open", url], _remaining(deadline))
        data = _wire(prefix + ["eval", script], _remaining(deadline))
        if not isinstance(data, dict) or data.get("state") not in {"ok", "blocked", "auth_required", "unavailable", "error"}:
            raise _Failure("error", "invalid_rows", "Blibli browser returned an unexpected extraction result.")
        if data["state"] != "ok":
            raise _Failure(data["state"], "browser_" + data["state"], "Blibli browser could not read products; no login or verification was attempted.")
        if not detail:
            return _blibli_rows(data.get("payload"))[:limit]
        # A related/recommended product JSON-LD node is not the requested item.
        rows = _rows(data.get("products"))
        requested_url = _blibli_product_url(query_or_url)
        matches = []
        for row in rows:
            offers = row.get("offers")
            offer = offers[0] if isinstance(offers, list) and len(offers) == 1 else offers
            native_url = row.get("url") or (offer.get("url") if isinstance(offer, dict) else None)
            if isinstance(native_url, str) and urllib.parse.urljoin(_BLIBLI, native_url).split("?")[0].rstrip("/") == requested_url.rstrip("/"):
                matches.append(row)
        return matches
    finally:
        # Reserve a small bounded cleanup allowance even after the work timeout.
        try:
            _wire(prefix + ["close"], min(5.0, max(0.1, deadline - time.monotonic())))
        except _Failure as exc:
            if warnings is not None:
                warnings.append(f"Browser session close failed ({exc.code}); session {session} may remain until OpenCLI idle timeout.")


def search_marketplace(marketplace: str, query: str, limit: int = 10, timeout: float = 90,
                       executable: str = "opencli", *, browser_fallback: bool = False, filters=None) -> dict:
    """Search one page; Blibli browser reuse is explicitly opt-in.

    Limit is capped at the upstream adapter maximum and disclosed in warnings.
    No extracted rows means empty_unverified, including upstream EMPTY_RESULT.
    """
    marketplace, query = _marketplace(marketplace), _text(query, "query")
    from .filters import native_plan
    plan = native_plan(marketplace, query, filters)
    executable, timeout = _text(executable, "executable"), _timeout(timeout)
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("limit must be an integer from 1 to 1000")
    if type(browser_fallback) is not bool:
        raise ValueError("browser_fallback must be a boolean")
    if marketplace not in _LIMITS:
        return _result(marketplace, failure=_Failure(
            "unavailable", "native_adapter_unavailable",
            "No validated OpenCLI native adapter for this marketplace; use guest discovery/detail or imported observations."))
    actual_limit = min(limit, _LIMITS[marketplace])
    warnings = [] if actual_limit == limit else [f"Requested limit capped at upstream maximum {actual_limit}."]
    deadline = time.monotonic() + timeout
    try:
        if marketplace == "blibli":
            try:
                rows = _blibli_http(query, actual_limit, _remaining(deadline))
            except _Failure as direct_error:
                if not browser_fallback:
                    raise
                warnings += [f"Direct Blibli search failed ({direct_error.code}); optional browser reuse attempted.",
                             "Browser session close is best effort; OpenCLI owned sessions expire after idle timeout."]
                try:
                    rows = _blibli_browser(query, actual_limit, deadline, executable, warnings=warnings)
                except _Failure as fallback_error:
                    warnings.append(f"Browser fallback failed ({fallback_error.code}).")
                    # A missing bridge must not overwrite an observed HTTP block.
                    raise direct_error if fallback_error.status == "unavailable" else fallback_error
        else:
            _version(executable, _remaining(deadline))
            argv = [executable, _SITE[marketplace], "search", "--limit", str(actual_limit), "--format", "json"] + plan["opencli_argv"] + ["--", query]
            rows = _china_rows(marketplace, _wire(argv, _remaining(deadline)))[:actual_limit]
        result = _result(marketplace, rows, warnings=warnings)
        submitted = [x[2:].replace("-", "_") for x in plan["opencli_argv"][::2]]
        plan["submitted_native_filters"] = submitted
        plan["unverified_or_local_filters"] = sorted(set(plan["requested"]) - set(submitted))
        result["filters"] = plan
        return result
    except _Failure as exc:
        return _result(marketplace, failure=exc, warnings=warnings)


def get_item(marketplace: str, item_id: str, timeout: float = 90, executable: str = "opencli",
             *, browser_fallback: bool = False) -> dict:
    """Read detail. Blibli needs a native product URL and opt-in browser reuse.

    Taobao/JD items retain their raw field/value table, not one offer per field.
    """
    marketplace, item_id = _marketplace(marketplace), _text(item_id, "item_id")
    if marketplace not in _LIMITS:
        return _result(marketplace, failure=_Failure(
            "unavailable", "native_adapter_unavailable",
            "No validated OpenCLI native detail adapter for this marketplace; use guest detail or imported observations."))
    executable, timeout = _text(executable, "executable"), _timeout(timeout)
    if type(browser_fallback) is not bool:
        raise ValueError("browser_fallback must be a boolean")
    if marketplace != "blibli" and not re.fullmatch(r"[0-9]+", item_id):
        raise ValueError("Chinese marketplace item_id must contain only ASCII digits")
    deadline = time.monotonic() + timeout
    warnings = []
    try:
        if marketplace == "blibli":
            _blibli_product_url(item_id)
            if not browser_fallback:
                raise _Failure("unavailable", "browser_opt_in_required", "Blibli detail requires browser_fallback=True and the OpenCLI browser bridge; no private detail endpoint is guessed.")
            warnings += ["Browser detail reads URL-bound Product JSON-LD only; missing JSON-LD remains unverified.",
                         "Browser session close is best effort; OpenCLI owned sessions expire after idle timeout."]
            rows = _blibli_browser(item_id, 1, deadline, executable, detail=True, warnings=warnings)
        else:
            _version(executable, _remaining(deadline))
            command = "item" if marketplace == "goofish" else "detail"
            argv = [executable, _SITE[marketplace], command, item_id, "--format", "json"]
            rows = _china_rows(marketplace, _wire(argv, _remaining(deadline)), detail=True)
        return _result(marketplace, rows, warnings=warnings)
    except _Failure as exc:
        return _result(marketplace, failure=exc, warnings=warnings)


def doctor(executable: str = "opencli", live: bool = False) -> dict:
    """Version-only by default. live=True explicitly permits bridge diagnostics."""
    executable = _text(executable, "executable")
    if type(live) is not bool:
        raise ValueError("live must be a boolean")
    result = {"status": "unavailable", "required_version": OPENCLI_VERSION,
              "version": None, "live_checked": False, "bridge": None, "error": None}
    try:
        result["version"] = _version(executable, 10)
        result["status"] = "ok"
        if live:
            result["live_checked"] = True
            report = _wire([executable, "doctor"], 30)
            if not isinstance(report, dict):
                raise _Failure("error", "invalid_envelope", "OpenCLI doctor returned an unexpected report.")
            # Do not return profile identities or raw issue strings.
            result["bridge"] = {k: report.get(k) for k in ("daemonRunning", "extensionConnected", "daemonStale", "extensionOutdated")}
            if report.get("daemonRunning") is not True or report.get("extensionConnected") is not True:
                raise _Failure("unavailable", "bridge_unavailable", "OpenCLI doctor could not confirm both daemon and browser extension connectivity.")
    except _Failure as exc:
        result["status"] = exc.status
        result["error"] = {"code": exc.code, "message": exc.message}
    return result
