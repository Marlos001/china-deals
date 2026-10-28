"""Evaluate caller-supplied coupon assertions; never fetch or redeem a coupon.

Public contract:
    evaluate_coupons(offer, campaigns, context=None, as_of=None,
                     require_fresh=False, max_age_hours=1) -> dict
    annotate_offers(offers, payload, require_fresh=False, max_age_hours=1,
                    as_of=None) -> list of copied offers with coupon_estimates
    assess_coupon_freshness(campaign, as_of=None, max_age_hours=1) -> dict

Campaign schema: id (optional), currency (CNY or IDR), discount containing exactly
one of amount or percent (0..100); optional kind (instant, the default, or
cashback), min_spend, cap, marketplace, product_ids, seller, starts_at, ends_at,
requires, confirmed, eligibility, source_url, observed_at, verified_at,
source_mode. Money accepts finite
nonnegative numbers or decimal strings, never booleans. Product IDs are strings
or integers and require one marketplace, as do seller restrictions. Unknown
campaign fields are rejected so misspelled constraints cannot grant eligibility.

requires maps arbitrary context keys (e.g. buyer_account, account_holder,
payment_method, app, member, new_customer) to non-null scalar equality values.
No buyer/account is inferred. Missing/null context is unknown, unequal is fail.
eligible requires confirmed=true, either eligibility='confirmed' or nonempty
matched requires, source_url, observed_at, and no failed/unknown constraints.
eligibility='unconfirmed' or 'unknown' is potential; 'ineligible' fails. Omitted
date boundaries impose no restriction; confirmed asserts the declared scenario
is active at as_of. Supplied boundaries and observation datetimes need offsets;
date-only values mean UTC midnight (end dates include that full UTC day).
as_of defaults to UTC now; pass it explicitly for reproducible results.

Optional source evidence contract: source_mode is product_page,
guest_product_page, retailer_product_page, coupon_page, guest_coupon_page,
checkout_page, guest_checkout_page, or guest_api for freshness consideration.
Other modes (including caches, indexes, user/anonymous observations and missing
modes) never establish freshness. source_url must be HTTPS on the declared
marketplace's first-party host or subdomain, without credentials or a non-443
port. Both starts_at and ends_at must be explicit, with as_of and observed_at
inside that inclusive window. observed_at must be a timezone-aware datetime,
not a date or retrieval/index timestamp, within max_age_hours (positive, default
1) and not in the future. Optional verified_at must also be timezone-aware,
recent, and between observed_at and as_of; it never replaces observed_at.
The helper checks evidence independently of discount or account eligibility and
returns fresh (bool), status, reasons, age_hours and provenance. Missing/invalid
evidence is unverified. Freshness is a caller assertion, never checkout proof.
require_fresh adds an unknown freshness constraint for non-fresh evidence;
otherwise eligible scenarios become potential, while failed constraints remain
ineligible. It never fills missing account/payment/SKU/quantity/quota facts.
annotate_offers' explicit as_of overrides payload.as_of. Raw source timestamps
are assessed before legacy date normalization, preventing timestamp laundering.

Return keys: as_of, currency, listing_amount, campaigns, best_eligible,
best_potential, warnings, evidence_basis, independently_verified,
used_cart_checkout. Each campaign has status (eligible/potential/ineligible),
constraints [{name,status:matched/fail/unknown}], missing_facts, reasons,
discount_amount, amount_due, cashback, and provenance. Monetary outputs are
fixed-scale strings (IDR 0, CNY 2), rounded HALF_UP. Best values are null or
lists retaining ties, ordered by input, ranked by lowest payable then greatest
cashback. Every coupon is an independent alternative; cashback never reduces
amount_due. Listing price is already discounted and is never mutated.

All statuses describe caller assertions, including 'eligible'; none constitute
live, independent, account, cart, checkout, stock, or redemption verification.
Malformed rules/amounts/timestamps raise ValueError; a missing listing amount
produces unknown estimates. annotate_offers validates even with zero offers.
"""

from copy import deepcopy
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation, localcontext
from urllib.parse import urlsplit

from .marketplaces import MONEY_SCALES
from .models import HOSTS, MARKETPLACES

_SCALES = MONEY_SCALES
_FIELDS = {"id", "currency", "discount", "kind", "min_spend", "cap", "marketplace",
           "product_ids", "seller", "starts_at", "ends_at", "requires", "confirmed",
           "eligibility", "source_url", "observed_at", "verified_at", "source_mode"}
_FRESH_SOURCE_MODES = {"product_page", "guest_product_page", "retailer_product_page",
                       "coupon_page", "guest_coupon_page", "checkout_page",
                       "guest_checkout_page", "guest_api"}
_WARNINGS = [
    "Caller-supplied assertions only; eligible/potential are scenarios, not live redemption verification.",
    "Stacking rules unverified; coupons are independent alternatives and are never summed.",
    "Listing price already includes listing discounts; shipping, tax and payment fees are excluded.",
]


def _number(value, name):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError(f"{name} must be a finite nonnegative number")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"{name} must be a finite nonnegative number") from None
    if not result.is_finite() or result < 0:
        raise ValueError(f"{name} must be a finite nonnegative number")
    # Bound arithmetic work and JSON output size for imported data.
    if len(result.as_tuple().digits) > 100 or abs(result.adjusted()) > 100:
        raise ValueError(f"{name} exceeds supported numeric precision/range")
    return result


def _timestamp(value, name, *, end=False):
    try:
        if isinstance(value, datetime):
            result = value
        elif isinstance(value, date):
            result = datetime.combine(value, time.min, timezone.utc)
            if end:
                result += timedelta(days=1, microseconds=-1)
        elif isinstance(value, str) and len(value) == 10:
            result = datetime.combine(date.fromisoformat(value), time.min, timezone.utc)
            if end:
                result += timedelta(days=1, microseconds=-1)
        elif isinstance(value, str):
            result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            raise ValueError
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError
        return result.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise ValueError(f"{name} must be an ISO date or timezone-aware datetime") from None


def _source_timestamp(value, name):
    # Legacy date-only observations remain accepted by the evaluator, but cannot
    # establish source freshness by being converted into UTC midnight.
    if not isinstance(value, (str, datetime)) or isinstance(value, str) and len(value) <= 10:
        raise ValueError(f"{name} must be a timezone-aware datetime")
    return _timestamp(value, name)


def _freshness_limit(max_age_hours):
    limit = _number(max_age_hours, "max_age_hours")
    if limit <= 0:
        raise ValueError("max_age_hours must be positive")
    return limit


def assess_coupon_freshness(campaign, as_of=None, max_age_hours=1):
    """Assess source evidence only; never fetch, refresh or confirm eligibility."""
    if not isinstance(campaign, dict):
        raise ValueError("Campaign must be an object")
    limit = _freshness_limit(max_age_hours)
    now = datetime.now(timezone.utc) if as_of is None else _timestamp(as_of, "as_of")
    result = {"fresh": False, "status": "unverified", "reasons": [],
              "age_hours": None, "max_age_hours": str(limit), "as_of": now.isoformat(),
              "source_url": campaign.get("source_url"), "source_mode": campaign.get("source_mode"),
              "observed_at": None, "verified_at": None,
              "evidence_basis": "caller_assertions", "independently_verified": False,
              "used_cart_checkout": False}
    reasons = result["reasons"]
    mode = campaign.get("source_mode")
    if not isinstance(mode, str) or mode not in _FRESH_SOURCE_MODES:
        reasons.append("source_mode_unverified")
    market = campaign.get("marketplace")
    hosts = HOSTS.get(market, ()) if isinstance(market, str) else ()
    try:
        parsed = urlsplit(_text(campaign.get("source_url"), "source_url"))
        host = parsed.hostname or ""
        first_party = (parsed.scheme == "https" and not parsed.username and not parsed.password
                       and parsed.port in (None, 443)
                       and any(host == domain or host.endswith("." + domain) for domain in hosts))
    except ValueError:
        first_party = False
    if not first_party:
        reasons.append("source_url_not_first_party_https")
    stamps = {}
    for field in ("observed_at", "verified_at", "starts_at", "ends_at"):
        if field == "verified_at" and field not in campaign:
            continue
        try:
            stamps[field] = (_source_timestamp(campaign.get(field), field)
                             if field in ("observed_at", "verified_at")
                             else _timestamp(campaign.get(field), field, end=field == "ends_at"))
        except ValueError:
            reasons.append(f"{field}_missing_or_invalid")
    for field in ("observed_at", "verified_at"):
        if field in stamps:
            result[field] = stamps[field].isoformat()
    if reasons:
        return result
    observed, start, end = (stamps[key] for key in ("observed_at", "starts_at", "ends_at"))
    age = Decimal(str((now - observed).total_seconds())) / Decimal(3600)
    result["age_hours"] = str(age)
    if start > end:
        reasons.append("invalid_validity_window")
    elif now < start:
        result["status"] = "not_started"
        reasons.append("campaign_not_started")
    elif now > end:
        result["status"] = "expired"
        reasons.append("campaign_expired")
    elif observed > now:
        result["status"] = "future_timestamp"
        reasons.append("observed_at_in_future")
    elif not start <= observed <= end:
        reasons.append("observed_at_outside_validity_window")
    elif age > limit:
        result["status"] = "stale"
        reasons.append("observed_at_older_than_limit")
    if "verified_at" in stamps:
        verified = stamps["verified_at"]
        if not observed <= verified <= now:
            reasons.append("verified_at_outside_observation_interval")
        elif Decimal(str((now - verified).total_seconds())) / Decimal(3600) > limit:
            reasons.append("verified_at_older_than_limit")
    if not reasons:
        result.update(fresh=True, status="fresh")
    return result


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _identity(value, name):
    if isinstance(value, bool) or not isinstance(value, (str, int)) or not str(value).strip():
        raise ValueError(f"{name} must be a string or integer")
    return str(value)


def _scalar(value, name):
    if value is None or not isinstance(value, (str, int, float, bool, Decimal)):
        raise ValueError(f"{name} must be a non-null scalar")
    if isinstance(value, (float, Decimal)) and not Decimal(str(value)).is_finite():
        raise ValueError(f"{name} must be finite")


def _campaigns(campaigns):
    if not isinstance(campaigns, list):
        raise ValueError("campaigns must be a list")
    validated = []
    for index, campaign in enumerate(campaigns):
        if not isinstance(campaign, dict):
            raise ValueError("Each campaign must be an object")
        unknown = set(campaign) - _FIELDS
        if unknown:
            raise ValueError(f"Unknown campaign fields: {', '.join(sorted(map(str, unknown)))}")
        row = deepcopy(campaign)
        row["id"] = _identity(row.get("id", f"campaign-{index + 1}"), "campaign id")
        if not isinstance(row.get("currency"), str) or row["currency"] not in _SCALES:
            raise ValueError("Campaign currency must be a supported explicit source currency")
        row["kind"] = row.get("kind", "instant")
        if row["kind"] not in ("instant", "cashback"):
            raise ValueError("kind must be instant or cashback")
        discount = row.get("discount")
        if not isinstance(discount, dict) or set(discount) not in ({"amount"}, {"percent"}):
            raise ValueError("discount requires exactly one of amount or percent")
        key = next(iter(discount))
        row["discount"] = {key: _number(discount[key], f"discount.{key}")}
        if key == "percent" and row["discount"][key] > 100:
            raise ValueError("discount.percent must be between 0 and 100")
        for field in ("min_spend", "cap"):
            if field in row:
                row[field] = _number(row[field], field)
        if "marketplace" in row and row["marketplace"] not in MARKETPLACES:
            raise ValueError("Unsupported campaign marketplace")
        for field in ("marketplace", "seller"):
            if field in row:
                _text(row[field], field)
        if "product_ids" in row:
            if not isinstance(row["product_ids"], list) or not row["product_ids"]:
                raise ValueError("product_ids must be a nonempty list")
            row["product_ids"] = [_identity(value, "product_id") for value in row["product_ids"]]
        if ("product_ids" in row or "seller" in row) and "marketplace" not in row:
            raise ValueError("Product/seller restrictions require a marketplace")
        for field in ("starts_at", "ends_at", "observed_at"):
            if field in row:
                row[field] = _timestamp(row[field], field, end=field == "ends_at")
        if "verified_at" in row:
            row["verified_at"] = _source_timestamp(row["verified_at"], "verified_at")
        if "source_mode" in row:
            _text(row["source_mode"], "source_mode")
        if "starts_at" in row and "ends_at" in row and row["starts_at"] > row["ends_at"]:
            raise ValueError("starts_at must not be after ends_at")
        if "confirmed" in row and type(row["confirmed"]) is not bool:
            raise ValueError("confirmed must be a boolean")
        if "eligibility" in row and row["eligibility"] not in ("confirmed", "unknown", "unconfirmed", "ineligible"):
            raise ValueError("Invalid eligibility assertion")
        if "source_url" in row:
            parsed = urlsplit(_text(row["source_url"], "source_url"))
            if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("source_url must be an HTTP(S) URL without credentials")
        requires = row.setdefault("requires", {})
        if not isinstance(requires, dict):
            raise ValueError("requires must map context keys to scalar values")
        for key, value in requires.items():
            _text(key, "requires key")
            _scalar(value, f"requires.{key}")
        validated.append(row)
    return validated


def _money(value, currency):
    if value is None:
        return None
    quantum = Decimal(1).scaleb(-_SCALES[currency])
    with localcontext() as ctx:
        ctx.prec = 220
        return format(value.quantize(quantum, rounding=ROUND_HALF_UP), "f")


def _same(actual, expected):
    # bool is an int subclass, but a payment/member boolean is not the number 1.
    return isinstance(actual, bool) == isinstance(expected, bool) and actual == expected


def _evaluate(offer, campaigns, context, now, freshness, require_fresh):
    if not isinstance(offer, dict) or not isinstance(offer.get("price"), dict):
        raise ValueError("offer needs a normalized price object")
    price = offer["price"]
    currency = price.get("currency")
    if not isinstance(currency, str) or currency not in _SCALES:
        raise ValueError("Offer currency must be a supported explicit source currency")
    amount = _number(price["amount"], "price.amount") if price.get("amount") is not None else None
    market = offer.get("marketplace", offer.get("market"))
    if market not in MARKETPLACES:
        raise ValueError("Offer needs a supported marketplace")
    results = []
    for row, source_freshness in zip(campaigns, freshness):
        checks = []

        def check(name, actual, expected, *, predicate=None):
            state = "unknown" if actual is None else "matched" if (
                predicate(actual) if predicate else _same(actual, expected)) else "fail"
            checks.append({"name": name, "status": state})

        check("price.amount", amount, None, predicate=lambda _: True)
        check("currency", currency, row["currency"])
        if "marketplace" in row:
            check("marketplace", market, row["marketplace"])
        # Never compare IDs across known mismatched marketplaces.
        scoped = market == row.get("marketplace")
        if "product_ids" in row:
            item = offer.get("item_id") if scoped else None
            if item is not None:
                item = _identity(item, "offer.item_id")
            check("product_ids", item, None, predicate=lambda value: value in row["product_ids"])
            if item is not None:
                from .guest import _item_id, _product_url
                native_url = _product_url(market, offer.get("url"))
                bound_item = _item_id(market, native_url) if native_url else None
                check("product_url_identity", bound_item, item)
        if "seller" in row:
            check("seller", offer.get("seller") if scoped else None, row["seller"])
        if "min_spend" in row:
            check("min_spend", amount, None, predicate=lambda value: value >= row["min_spend"])
        if "starts_at" in row:
            check("starts_at", now, None, predicate=lambda value: value >= row["starts_at"])
        if "ends_at" in row:
            check("ends_at", now, None, predicate=lambda value: value <= row["ends_at"])
        for key, expected in row["requires"].items():
            check(f"requires.{key}", context.get(key), expected)
        check("confirmed", True if row.get("confirmed") is True else None, True)
        eligibility = row.get("eligibility")
        if eligibility == "ineligible":
            checks.append({"name": "eligibility", "status": "fail"})
        else:
            explicit = eligibility == "confirmed" or eligibility is None and bool(row["requires"])
            check("eligibility", True if explicit else None, True)
        check("source_url", row.get("source_url"), None, predicate=lambda _: True)
        check("observed_at", row.get("observed_at"), None, predicate=lambda _: True)
        if row.get("observed_at") is not None and row["observed_at"] > now:
            checks.append({"name": "observed_at_not_future", "status": "unknown"})
        if require_fresh:
            check("freshness", True if source_freshness["fresh"] else None, True)
        failed = [c["name"] for c in checks if c["status"] == "fail"]
        missing = [c["name"] for c in checks if c["status"] == "unknown"]
        status = "ineligible" if failed else "potential" if missing else "eligible"
        discount = due = cashback = None
        if amount is not None and currency == row["currency"]:
            with localcontext() as ctx:
                ctx.prec = 220
                rule = row["discount"]
                discount = rule["amount"] if "amount" in rule else amount * rule["percent"] / 100
                discount = min(discount, row.get("cap", discount), amount)
                # Round the benefit once, then cap at the rounded listing price.
                listed = Decimal(_money(amount, currency))
                discount = min(Decimal(_money(discount, currency)), listed)
                cashback = discount if row["kind"] == "cashback" else Decimal(0)
                due = listed if row["kind"] == "cashback" else listed - discount
        results.append({
            "id": row["id"], "kind": row["kind"], "status": status,
            "currency": row["currency"], "constraints": checks,
            "missing_facts": missing, "reasons": failed,
            "discount_amount": _money(discount, currency), "amount_due": _money(due, currency),
            "cashback": _money(cashback, currency), "source_url": row.get("source_url"),
            "observed_at": row["observed_at"].isoformat() if row.get("observed_at") else None,
            "verified_at": row["verified_at"].isoformat() if row.get("verified_at") else None,
            "source_mode": row.get("source_mode"), "freshness": deepcopy(source_freshness),
            "independently_verified": False, "used_cart_checkout": False,
        })

    def best(status):
        candidates = [r for r in results if r["status"] == status and r["amount_due"] is not None]
        if not candidates:
            return None
        def key(row):
            return Decimal(row["amount_due"]), Decimal(row["cashback"]).copy_negate()

        rank = min(map(key, candidates))
        return deepcopy([r for r in candidates if key(r) == rank])

    return {"as_of": now.isoformat(), "currency": currency, "listing_amount": _money(amount, currency),
            "campaigns": results, "best_eligible": best("eligible"), "best_potential": best("potential"),
            "warnings": list(_WARNINGS), "evidence_basis": "caller_assertions",
            "independently_verified": False, "used_cart_checkout": False}


def _context(context):
    if context is None:
        return {}
    if not isinstance(context, dict):
        raise ValueError("context must be an object")
    for key, value in context.items():
        _text(key, "context key")
        if value is not None:
            _scalar(value, f"context.{key}")
    return context


def evaluate_coupons(offer, campaigns, context=None, as_of=None, require_fresh=False, max_age_hours=1):
    """Return independent coupon scenarios without changing the normalized offer."""
    now = datetime.now(timezone.utc) if as_of is None else _timestamp(as_of, "as_of")
    validated = _campaigns(campaigns)
    if type(require_fresh) is not bool:
        raise ValueError("require_fresh must be a boolean")
    limit = _freshness_limit(max_age_hours)
    freshness = [assess_coupon_freshness(row, now, limit) for row in campaigns]
    return _evaluate(offer, validated, _context(context), now, freshness, require_fresh)


def annotate_offers(offers, payload, require_fresh=False, max_age_hours=1, as_of=None):
    """Copy offers, adding only coupon_estimates; payload uses campaigns/context/as_of."""
    if not isinstance(payload, dict) or set(payload) - {"campaigns", "context", "as_of"}:
        raise ValueError("Coupon payload must contain campaigns, optional context and as_of")
    campaigns = _campaigns(payload.get("campaigns"))
    context = _context(payload.get("context"))
    as_of = payload.get("as_of") if as_of is None else as_of
    now = datetime.now(timezone.utc) if as_of is None else _timestamp(as_of, "as_of")
    if type(require_fresh) is not bool:
        raise ValueError("require_fresh must be a boolean")
    limit = _freshness_limit(max_age_hours)
    freshness = [assess_coupon_freshness(row, now, limit) for row in payload["campaigns"]]
    result = []
    for offer in offers:
        estimate = _evaluate(offer, campaigns, context, now, freshness, require_fresh)
        annotated = deepcopy(offer)
        annotated["coupon_estimates"] = estimate
        result.append(annotated)
    return result
