"""Bounded first-party refresh orchestration; no cache, login or transport fallback.

Input: an array, {offers: [...]}, {items: [...]}, or a ranking envelope with
groups and unranked. All rows require marketplace and an exact native item URL.
Output: {schema_version, generated_at, backend, items, storage, ...}; each item
is a normalized *new* observation with refresh/status/attempts, price_freshness,
previous_observation, original_context and price_delta. Missing facts stay null.

Limits: 50 items, 2 MiB input/raw receipt, 64 KiB per row/sanitized receipt, 16 JSON nesting levels,
20 attempts per receipt, 0 < timeout <= 300 seconds for the entire acquisition,
and 0 < max_age_hours <= 8760. SQLite waits at most 5 seconds per operation,
outside the acquisition deadline. force is a boolean compatibility flag: both
values fetch detail and neither resets host gates or permits a stale fallback.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from contextlib import nullcontext
from datetime import datetime, timezone
from decimal import Decimal, DecimalException, localcontext
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, urlunsplit

from . import adapters, browser_guest, freshness, guest
from .models import decimal_value, marketplace_name, normalize_offer, utc_now
from .ranking import apply_product_intent, apply_transaction_scope

MAX_ITEMS = 50
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_RECORD_BYTES = 64 * 1024
_PRIMARY = {"guest_product_page", "guest_api", "product_detail", "detail", "listing", "listing_content"}
_CONTEXT = ("intent_query", "query", "query_intent", "relevance", "ranking_exclusions", "exclusions",
            "require_terms", "exclude_terms", "candidate_id", "price_freshness_policy")
_PRIVATE = {"cookie", "cookies", "setcookie", "authorization", "headers", "requestheaders",
            "responseheaders", "storage", "storagestate", "localstorage", "sessionstorage",
            "capture", "rawcapture", "html", "rawhtml", "mainhtml", "outerhtml", "innerhtml", "dom",
            "body", "responsebody", "screenshot",
            "token", "accesstoken", "refreshtoken", "password", "secret"}
_OBSERVATION_FIELDS = (
    "marketplace", "item_id", "title", "url", "url_basis", "identity_evidence", "offers", "price",
    "seller", "description", "source_mode", "model", "variant_evidence", "hardware", "source_detail", "index_source_url",
    "discovered_at", "location", "domestic_free_shipping", "variant", "condition", "availability",
    "seller_trust", "observed_at", "signals", "warnings", "source_warnings", "selected_variant",
    "conditions", "payment", "discount_claims", "transaction_evidence", "ranking_exclusions", "price_freshness_policy",
)


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _bounded(value, limit):
    """Validate before copying or retaining arbitrary caller/adapter structures."""
    count = 0

    def visit(node, depth):
        nonlocal count
        count += 1
        if depth > 16 or count > 10000:
            raise ValueError("JSON exceeds nesting or value-count limit")
        if isinstance(node, dict):
            for key, child in node.items():
                if not isinstance(key, str):
                    raise ValueError("JSON object keys must be strings")
                visit(child, depth + 1)
        elif isinstance(node, list):
            for child in node:
                visit(child, depth + 1)
        elif node is not None and not isinstance(node, (str, int, float, bool)):
            raise ValueError("Payload must contain JSON values")

    visit(value, 0)
    try:
        encoded = _json(value)
        if len(encoded.encode("utf-8")) > limit:
            raise ValueError("JSON exceeds byte limit")
    except (TypeError, OverflowError, UnicodeError, RecursionError):
        raise ValueError("Payload must contain bounded JSON values") from None
    return value


def _safe_link(value):
    if not isinstance(value, str) or len(value) > 4096:
        return None
    try:
        parts = urlsplit(value)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.port:
            return None
        for market in ("jd", "taobao", "goofish", "blibli"):
            native = guest._product_url(market, value)
            if native:
                return native
        # Gate URLs sometimes contain session tokens. Retain host/path only.
        return urlunsplit(("https", parts.hostname, parts.path, "", ""))
    except ValueError:
        return None


def _clean(value):
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            folded = "".join(c for c in key.lower() if c.isalnum())
            if folded in _PRIVATE or any(part in folded for part in ("cookie", "capture", "token", "password")):
                continue
            result[key] = _safe_link(child) if folded.endswith("url") else _clean(child)
        return result
    if isinstance(value, list):
        return [_clean(child) for child in value]
    return value


def _clock(value):
    if value is None:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
        if not isinstance(parsed, datetime) or parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("as_of must be a timezone-aware timestamp") from None


def _rows(payload):
    _bounded(payload, MAX_INPUT_BYTES)
    context = {}
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        context = {key: payload[key] for key in _CONTEXT if key in payload}
        inherited = payload.get('original_context')
        policy = _required_policy(context.get('price_freshness_policy'),
                                  inherited.get('price_freshness_policy') if isinstance(inherited, dict) else None)
        if policy:
            context['price_freshness_policy'] = policy
        rows = payload.get("offers", payload.get("items"))
        if rows is None and isinstance(payload.get("groups"), dict):
            groups = list(payload["groups"].values()) + [payload.get("unranked", [])]
            if not all(isinstance(group, list) for group in groups):
                raise ValueError("Ranking groups and unranked must be arrays")
            rows = [row for group in groups for row in group]
    else:
        rows = None
    if not isinstance(rows, list) or len(rows) > MAX_ITEMS:
        raise ValueError("Refresh requires an array of at most 50 items")
    _bounded(context, MAX_RECORD_BYTES)
    prepared = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each refresh item must be an object")
        _bounded(row, MAX_RECORD_BYTES)
        market = marketplace_name(row.get("marketplace"))
        value = row.get("url")
        url = guest._product_url(market, value) if isinstance(value, str) and len(value) <= 4096 else None
        if not url:
            raise ValueError("Each refresh item requires an exact native product URL")
        if market in {"taobao", "goofish"} and len(parse_qs(urlsplit(value).query, keep_blank_values=True).get("id", [])) != 1:
            raise ValueError("Product URL has ambiguous item IDs")
        item_id = guest._item_id(market, url)
        for field in {"jd": ("item_id", "sku", "skuId"), "taobao": ("item_id", "itemId", "num_iid"),
                      "goofish": ("item_id", "itemId"), "blibli": ("item_id", "sku", "productSku")}[market]:
            if row.get(field) is not None and str(row[field]) != item_id:
                raise ValueError("Source item ID conflicts with the native URL")
        original = context | {key: row[key] for key in _CONTEXT if key in row}
        if isinstance(row.get("original_context"), dict):
            original = {key: row["original_context"][key] for key in _CONTEXT if key in row["original_context"]} | original
        policy = _required_policy(context.get('price_freshness_policy'), row.get('price_freshness_policy'),
                                  row['original_context'].get('price_freshness_policy') if isinstance(row.get('original_context'), dict) else None)
        if policy:
            original['price_freshness_policy'] = policy
        _bounded(original, MAX_RECORD_BYTES)
        query = original.get("intent_query") or original.get("query")
        if query is not None and (not isinstance(query, str) or len(query) > 4096):
            raise ValueError("Intent query must be a string of at most 4096 characters")
        for key in ("ranking_exclusions", "exclusions", "require_terms", "exclude_terms"):
            if key in original and (not isinstance(original[key], list) or len(original[key]) > 50
                                    or any(not isinstance(v, str) or len(v) > 500 for v in original[key])):
                raise ValueError(f"{key} must contain at most 50 bounded strings")
        prepared.append((row, market, url, item_id, _clean(original)))
    return prepared, _clean(context)


def _required_policy(*policies):
    limits = [decimal_value(value.get('max_age_hours'), positive=True) for value in policies
              if isinstance(value, dict) and value.get('required') is True]
    if limits:
        return {'required': True, 'max_age_hours': str(min(limits))}
    return None


def _observation(row, market, url, item_id):
    source = _clean(row)
    title = source.get("title") or source.get("name") or source.get("productName")
    # models requires a title; the temporary placeholder is never exported.
    if not title:
        source["title"] = "Unknown product"
    if "variant" not in source and isinstance(source.get("selected_variant"), str):
        source["variant"] = source["selected_variant"]
    result = normalize_offer(market, source, source.get("observed_at"))
    apply_transaction_scope(result)
    if not title:
        result["title"] = None
    result.update(marketplace=market, item_id=item_id, url=url)
    selected = source.get("selected_variant", result.get("variant"))
    result["selected_variant"] = selected.strip() if isinstance(selected, str) and selected.strip() else None
    detail = result.get("source_detail") or {}
    if (result["selected_variant"] in {"unknown", "unspecified", "unselected", "unverified"}
            or (source.get("selected_variant") and result.get("variant")
                and result["selected_variant"] != result["variant"])
            or any("selected_sku_id" in evidence and not evidence["selected_sku_id"]
                   for evidence in (source, detail))):
        result["selected_variant"] = None
    result["conditions"] = source.get("conditions")
    result["payment"] = source.get("payment", source.get("payment_method", source.get("payment_terms")))
    claims = {key: source[key] for key in ("original_price", "list_price", "crossed_out_price", "discount", "discount_percent")
              if key in source}
    result["discount_claims"] = {"claims": claims, "verified_historic_savings": False,
                                 "basis": "seller_claim_only"}
    if not claims and isinstance(source.get("discount_claims"), dict):
        result["discount_claims"]["claims"] = source["discount_claims"].get("claims", {})
    return {key: result.get(key) for key in _OBSERVATION_FIELDS}


def _previous(row, market, url, item_id):
    source = row
    if isinstance(row.get("previous_observation"), dict) and not (isinstance(row.get("price"), dict) and row["price"].get("amount")):
        source = row["previous_observation"]
    if not any(source.get(key) is not None for key in ("price", "observed_at", "title", "source_mode")):
        return None
    if source.get("marketplace", market) != market or source.get("item_id", item_id) != item_id:
        return None
    if source.get("url") and guest._product_url(market, source["url"]) != url:
        return None
    return _observation(source, market, url, item_id)


def _access(receipt):
    raw = receipt.get("access") or {}
    if not isinstance(raw, dict):
        raise ValueError("Detail access receipt must be an object")
    attempts = raw.get("attempts", [])
    if not isinstance(attempts, list) or len(attempts) > 20 or any(not isinstance(a, dict) for a in attempts):
        raise ValueError("Detail attempts exceed the receipt contract")
    keys = ("url", "final_url", "denied_url", "challenge_url", "source_mode", "attempted_at",
            "status", "error_code", "network_attempted", "gate_origin")
    return {"mode": "guest", "authenticated": False,
            "attempts": [_clean({key: attempt[key] for key in keys if key in attempt}) for attempt in attempts]}


def _failure(code, status="unavailable", attempts=None):
    return {"status": status, "error": {"code": code}, "items": [],
            "access": {"attempts": attempts or []}}


def _get(market, url, backend, deadline):
    # The actual HTTP JD request uses the mobile host. Guard it before calling
    # a backend, including browser setup, and retain the backend's own receipts.
    request_url = f"https://item.m.jd.com/product/{guest._item_id(market, url)}.html" if backend == "http" and market == "jd" else url
    attempt = {"url": request_url, "attempted_at": utc_now(), "source_mode": "guest_product_page"}
    called = False
    try:
        remaining = adapters._remaining(deadline)
        guest._check_gate(attempt)
        getter = guest.get_guest_item if backend == "http" else browser_guest.get_browser_guest_item
        called = True
        receipt = getter(market, url, timeout=remaining)
        if not isinstance(receipt, dict):
            raise ValueError("Invalid detail receipt")
        # Capture bounded access facts even if the product body is oversized.
        access = _access(receipt)
        _bounded(access, MAX_RECORD_BYTES)
        try:
            _bounded(receipt, MAX_INPUT_BYTES)
            receipt = _clean(receipt)
            _bounded(receipt, MAX_RECORD_BYTES)
        except ValueError:
            return _failure("detail_output_limit", attempts=access["attempts"])
        error = receipt.get("error") or {}
        code = error.get("code") if isinstance(error, dict) else None
        if code in guest._GATE_CODES:
            origin = dict(access["attempts"][-1]) if access["attempts"] else attempt
            exc = adapters._Failure("blocked", code, "Guest access gate")
            guest._record_gate(origin, exc)
            # Gate the initiating host too if verification redirects elsewhere.
            guest._record_gate(attempt, exc)
        if time.monotonic() > deadline:
            return _failure("timeout", attempts=access["attempts"])
        return receipt
    except adapters._Failure as exc:
        if called:
            attempt["network_attempted"] = None  # An exception is not proof of an actual request.
        elif "network_attempted" not in attempt:
            attempt["network_attempted"] = False
        attempt.update(status=exc.status, error_code=exc.code)
        guest._record_gate(attempt, exc)
        return _failure(exc.code, exc.status, [attempt])
    except Exception:
        # Do not leak arbitrary adapter exceptions (URLs, HTML or credentials).
        attempt.update(status="unavailable", error_code="detail_error", network_attempted=None)
        return _failure("detail_error", attempts=[attempt])


def _freshness(offer, max_age_hours, now):
    policy = offer.get("price_freshness_policy")
    if isinstance(policy, dict) and policy.get("required") is True:
        max_age_hours = min(decimal_value(max_age_hours, positive=True), decimal_value(policy.get("max_age_hours"), positive=True))
    return freshness.assess_price_freshness(offer, max_age_hours=max_age_hours, as_of=now)


def _delta(current, previous, max_age_hours, now):
    result = {"status": "not_comparable", "reason": "no_previous_observation", "amount": None,
              "percent": None, "currency": current["price"]["currency"], "verified_historic_savings": False}
    if previous is None:
        return result
    reason = None
    if any(current.get(k) != previous.get(k) for k in ("marketplace", "item_id")):
        reason = "different_identity"
    elif current["price"]["currency"] != previous["price"]["currency"]:
        reason = "different_currency"
    elif not current.get("selected_variant") or not previous.get("selected_variant"):
        reason = "selected_variant_unknown"
    elif current["selected_variant"] != previous["selected_variant"]:
        reason = "different_selected_variant"
    elif (current.get("condition") in (None, "", "unknown") or previous.get("condition") in (None, "", "unknown")
          or any(not offer.get("payment") or offer["payment"] in ("unknown", "unspecified", "unverified")
                 for offer in (current, previous))):
        reason = "conditions_or_payment_unknown"
    elif any(current.get(key) != previous.get(key) for key in ("condition", "conditions", "payment")):
        reason = "different_conditions_or_payment"
    elif any(offer.get("source_mode") not in _PRIMARY or not _freshness(offer, max_age_hours, now)["recent_observation"]
             for offer in (current, previous)):
        reason = "requires_recent_primary_observations"
    elif not current["price"]["amount"] or not previous["price"]["amount"]:
        reason = "price_unknown"
    elif _clock(current["observed_at"]) <= _clock(previous["observed_at"]):
        reason = "observation_not_newer"
    if reason:
        result["reason"] = reason
        return result
    try:
        amounts = (previous["price"]["amount"], current["price"]["amount"])
        if any(len(value) > 100 for value in amounts):
            raise ValueError
        with localcontext() as ctx:
            ctx.prec = 220
            before, after = map(Decimal, amounts)
            change = format(after - before, "f")
            percent = format((100 * (after - before) / before).quantize(Decimal(".01")), "f")
        result.update(status="comparable_observed_change", reason="same_explicit_quote_scope",
                      amount=change, percent=percent,
                      previous_observed_at=previous["observed_at"], observed_at=current["observed_at"])
    except (ValueError, DecimalException):
        result["reason"] = "amount_outside_comparison_bounds"
    return result


def _path(store_path):
    if not isinstance(store_path, (str, Path)) or not str(store_path) or len(str(store_path)) > 4096 or "\0" in str(store_path):
        raise ValueError("store_path must be a nonempty filesystem path of at most 4096 characters")
    if str(store_path) == ":memory:":
        raise ValueError("store_path must be persistent")
    return Path(store_path).expanduser().absolute()


def history(store_path, marketplace=None, item_id=None, limit=50):
    """Read newest inserted receipts first; 1..50 rows, no file creation/writes.

    Each row contains observation_hash, recorded_at, observation and refresh.
    A missing store returns []; corrupt/incompatible stores raise sqlite errors.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_ITEMS:
        raise ValueError("history limit must be an integer from 1 to 50")
    market = marketplace_name(marketplace) if marketplace is not None else None
    if item_id is not None and (not isinstance(item_id, str) or not item_id or len(item_id) > 256):
        raise ValueError("item_id must be a nonempty string of at most 256 characters")
    path = _path(store_path)
    if not path.exists():
        return []
    clauses, params = [], []
    for field, value in (("marketplace", market), ("item_id", item_id)):
        if value is not None:
            clauses.append(field + " = ?")
            params.append(value)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    connection = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)
    try:
        # A concurrent writer may have created the file but not committed the
        # first schema yet. That snapshot has no observations, not a read failure.
        if not connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'refresh_observations'").fetchone():
            return []
        rows = connection.execute("SELECT substr(payload, 1, ?), length(CAST(payload AS BLOB)) FROM refresh_observations"
                                  + where + " ORDER BY sequence DESC LIMIT ?",
                                  (4 * MAX_RECORD_BYTES + 1, *params, limit)).fetchall()
        result = []
        for raw, size in rows:
            if size > 4 * MAX_RECORD_BYTES:
                raise ValueError("Stored observation exceeds output bounds")
            result.append(_bounded(json.loads(raw), 4 * MAX_RECORD_BYTES))
        return result
    finally:
        connection.close()


def _persist(path, items, observations):
    connection = sqlite3.connect(path, timeout=5)
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("""CREATE TABLE IF NOT EXISTS refresh_observations (
            sequence INTEGER PRIMARY KEY, observation_hash TEXT NOT NULL UNIQUE,
            marketplace TEXT NOT NULL, item_id TEXT NOT NULL, payload TEXT NOT NULL)""")
        connection.execute("CREATE INDEX IF NOT EXISTS refresh_identity ON refresh_observations(marketplace, item_id, sequence)")
        inserted = 0
        for item, observation in zip(items, observations):
            digest = item["observation_hash"]
            entry = {"observation_hash": digest, "recorded_at": utc_now(), "observation": observation,
                     "refresh": item["refresh"]}
            _bounded(entry, 4 * MAX_RECORD_BYTES)
            cursor = connection.execute("INSERT OR IGNORE INTO refresh_observations(observation_hash, marketplace, item_id, payload) VALUES (?, ?, ?, ?)",
                                        (digest, item["marketplace"], item["item_id"], _json(entry)))
            inserted += cursor.rowcount
        connection.commit()
        return inserted
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def refresh_offers(payload, backend="http", timeout=30, max_age_hours=24, as_of=None, store_path=None, force=False):
    """Attempt every validated native URL once within a shared acquisition budget.

    Input/options errors raise ValueError before acquisition. Adapter failures
    become per-item receipts. Persistence failures are reported under storage
    and never discard completed acquisition receipts. No live access is made
    by history, and no persistent store is touched unless store_path is given.
    """
    if backend not in ("http", "browser"):
        raise ValueError("backend must be http or browser")
    timeout = adapters._timeout(timeout)
    if timeout > 300:
        raise ValueError("timeout must be at most 300 seconds")
    if not isinstance(force, bool):
        raise ValueError("force must be boolean")
    fixed_now = _clock(as_of) if as_of is not None else None
    _freshness({}, max_age_hours, fixed_now or _clock(None))
    prepared, context = _rows(payload)
    path = _path(store_path) if store_path is not None else None
    storage = {"status": "not_requested" if path is None else "ok", "inserted": 0, "errors": []}
    previous = []
    for row, market, url, item_id, _ in prepared:
        prior = _previous(row, market, url, item_id)
        if path is not None:
            try:
                entries = history(path, market, item_id)
                candidates = [prior] if prior else []
                candidates.extend(entry["observation"] for entry in entries
                                  if isinstance(entry.get("observation"), dict) and entry["observation"].get("observed_at"))
                dated = []
                for candidate in candidates:
                    try:
                        candidate = _previous(candidate, market, url, item_id)
                        if candidate is not None and candidate.get("observed_at"):
                            dated.append((_clock(candidate.get("observed_at")), candidate))
                    except (TypeError, ValueError, KeyError):
                        continue
                if dated:
                    prior = max(dated, key=lambda pair: pair[0])[1]
            except (OSError, sqlite3.Error, ValueError, KeyError, TypeError):
                if not storage["errors"]:
                    storage["errors"].append({"operation": "read", "code": "history_read_failed"})
                storage["status"] = "error"
        previous.append(prior)
    items, observations = [], []
    deadline = time.monotonic() + timeout
    # Preserve an outer command's gates instead of resetting them in a nested refresh.
    session = guest.access_session() if guest._ACCESS_GATES.get() is None else nullcontext()
    with session:
        for (_, market, url, item_id, original), prior in zip(prepared, previous):
            receipt = _get(market, url, backend, deadline)
            now = fixed_now or _clock(None)
            access = _access(receipt)
            status = receipt.get("status", "unavailable")
            error = receipt.get("error")
            current = _observation({}, market, url, item_id)
            if status == "ok":
                rows = receipt.get("items")
                try:
                    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
                        raise ValueError("Detail must return one item")
                    row = rows[0]
                    if row.get("marketplace", market) != market or guest._product_url(market, row.get("url")) != url:
                        raise ValueError("Detail item does not match requested identity")
                    current = _observation(row, market, url, item_id)
                    if current["identity_evidence"] and any("identity" in w.lower() or "IDs" in w for w in current["warnings"]):
                        raise ValueError("Detail identity evidence conflicts")
                    if row.get("item_id") is not None and str(row["item_id"]) != item_id:
                        raise ValueError("Detail ID conflicts")
                    status = "refreshed"
                except (ValueError, TypeError, KeyError):
                    current = _observation({}, market, url, item_id)
                    status, error = "unavailable", {"code": "detail_identity_or_schema_unverified"}
            observation = _clean(current)
            observations.append(observation)
            # Hash source facts, not TTL policy, query assessment or run clocks.
            current["observation_hash"] = hashlib.sha256(_json({"observation": observation, "error": _clean(error)}).encode("utf-8")).hexdigest()
            policy = _required_policy(original.get('price_freshness_policy'), current.get('price_freshness_policy'))
            if policy:
                current["price_freshness_policy"] = policy
            current["price_freshness"] = _freshness(current, max_age_hours, now)
            if status == "refreshed":
                if current["source_mode"] not in _PRIMARY or not current["price_freshness"]["recent_observation"]:
                    current["price"].update(amount=None, basis="nonrecent_or_nonprimary_observation")
                    status = "nonrecent_observation"
                elif current["price"]["amount"] is None:
                    status = "unpriced"
            current["original_context"] = original
            query = original.get("intent_query") or original.get("query")
            if query:
                apply_product_intent(current, query)
            if status == "refreshed" and current["price"]["amount"] is None:
                status = "unpriced"
            retained = [reason for reason in original.get("ranking_exclusions", [])
                        if not reason.startswith(("product_relevance_", "price_freshness_"))
                        and reason not in {"refresh_price_unavailable", "possible_deposit_or_installment_price",
                                           "possible_rental_price", "possible_starting_price"}]
            exclusions = list(dict.fromkeys(retained + current.get("ranking_exclusions", [])))
            if current["price"]["amount"] is None:
                exclusions.append("refresh_price_unavailable")
            current["ranking_exclusions"] = list(dict.fromkeys(exclusions))
            current["previous_observation"] = prior
            current["refresh"] = {"status": status, "backend": backend, "requested_url": url,
                                  "checked_at": now.isoformat(), "error": _clean(error), "access": access}
            current["price_delta"] = _delta(current, prior, max_age_hours, now)
            items.append(current)
    if path is not None:
        try:
            storage["inserted"] = _persist(path, items, observations)
        except (OSError, sqlite3.Error, ValueError, TypeError):
            storage["status"] = "error"
            storage["errors"].append({"operation": "write", "code": "history_write_failed"})
    return {"schema_version": "1", "generated_at": utc_now(), "backend": backend, "force": force,
            "refresh_policy": "always_attempt_first_party_detail", "original_context": context,
            "items": items, "storage": storage,
            "warnings": ["Displayed prices and seller discounts remain source claims; checkout is unverified.",
                         "Negative observed deltas are not verified historic savings."]}
