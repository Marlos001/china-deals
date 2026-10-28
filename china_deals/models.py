"""Small, conservative normalization boundary for untrusted marketplace records."""

import json
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, urlparse, urlunsplit

from .marketplaces import (
    ALIASES,
    CURRENCIES,
    HOSTS,
    ID_FIELDS,
    INTERNATIONAL_MARKETPLACES,
    MARKETPLACES,
    MONEY_SCALES,
    PUBLIC_METADATA_MARKETPLACES,
    item_url,
    product_id,
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def marketplace_name(value):
    if not isinstance(value, str):
        raise ValueError("Marketplace must be a string")
    name = ALIASES.get(value.lower(), value.lower())
    if name not in MARKETPLACES:
        raise ValueError(f"Unknown marketplace: {value}")
    return name


def decimal_value(value, name="amount", *, positive=False):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{name} must be a finite number") from None
    if not result.is_finite() or result < 0 or (positive and result <= 0):
        raise ValueError(f"{name} must be {'positive' if positive else 'nonnegative'} and finite")
    return result


def parse_price(value, currency):
    """Only accept a single explicit amount. Ranges/coupons/deposits remain unpriced."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            amount = decimal_value(value)
            return format(amount, "f") if amount > 0 else None
        except ValueError:
            return None
    text = str(value).strip()
    if currency == "CNY":
        text = re.sub(r"^(?:CNY\s*|RMB\s*|[¥￥]\s*)", "", text, flags=re.I)
        if not re.fullmatch(r"(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?", text):
            return None
        text = text.replace(",", "")
    elif currency == "IDR":
        text = re.sub(r"^(?:IDR\s*|Rp\.?\s*)", "", text, flags=re.I)
        if not re.fullmatch(r"(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,2})?", text):
            return None
        text = text.replace(".", "").replace(",", ".")
    elif currency in MONEY_SCALES:
        # International imports must provide an explicit currency. Do not guess
        # locale from commas or a bare dollar sign. Machine decimal strings are
        # portable; explicitly marked BRL supports its standard localized form.
        if currency == "BRL" and text.startswith("R$"):
            text = text[2:].strip()
            if not re.fullmatch(r"(?:[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+)(?:,[0-9]{1,2})?", text):
                return None
            text = text.replace(".", "").replace(",", ".")
        else:
            text = re.sub(r"^" + re.escape(currency) + r"\s+", "", text)
            if currency == "USD":
                text = re.sub(r"^(?:US\s*)?\$\s*", "", text)
            scale = MONEY_SCALES[currency]
            if not re.fullmatch(r"[0-9]+" + (rf"(?:\.[0-9]{{1,{scale}}})?" if scale else ""), text):
                return None
    else:
        return None
    try:
        amount = decimal_value(text)
        return format(amount, "f") if amount > 0 else None
    except ValueError:
        return None


def safe_url(value, marketplace):
    if not isinstance(value, str):
        return None
    if value.startswith("//"):
        value = "https:" + value
    if value.startswith("/") and marketplace == "blibli":
        value = "https://www.blibli.com" + value
    if re.search(r"[\\\s\x00-\x1f\x7f]", value):
        return None
    try:
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower()
        valid_host = any(host == h or host.endswith("." + h) for h in HOSTS[marketplace])
        if (parsed.scheme != "https" or not valid_host or parsed.username or parsed.password
                or parsed.port is not None or "%" in parsed.netloc or "@" in parsed.netloc):
            return None
        return urlunsplit(("https", host, parsed.path, parsed.query, ""))
    except ValueError:
        return None


def _text(row, *keys):
    for key in keys:
        value = row.get(key)
        if isinstance(value, (str, int)) and not isinstance(value, bool) and str(value).strip():
            return str(value).strip()
    return None


def _variant_text(value):
    """Bound one selected observation without nesting normalized envelopes."""
    if isinstance(value, dict):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return value.strip()[:8000].rstrip() if isinstance(value, str) and value.strip() else None


def _variant_observations(row):
    """Keep independent observations flat, deduplicated and stable on re-import.

    Current source fields take priority within the 20-observation bound. Sorting
    keeps the output stable when a dictionary variant moves to legacy evidence.
    Existing observations are strings, never wrappers around prior exports.
    """
    values = set()
    for key in ("variant", "selected_variant", "variant_evidence"):
        value = _variant_text(row.get(key))
        if value:
            values.add(value)
    variant = _variant_text(_text(row, "variant", "spec"))
    if variant:
        values.add(variant)
    retained = row.get("variant_observations")
    if isinstance(retained, list):
        for value in retained:
            if len(values) >= 20:
                break
            if isinstance(value, str):
                value = _variant_text(value)
                if value:
                    values.add(value)
    return sorted(values)


def _url_item_ids(value, marketplace):
    """Read only known product routes; opaque tokens are never numeric item IDs."""
    if marketplace in PUBLIC_METADATA_MARKETPLACES:
        identity = product_id(marketplace, value)
        return [identity] if identity is not None else []
    url = safe_url(value, marketplace)
    if not url:
        return []
    parsed = urlparse(url)
    if marketplace == "jd":
        pattern = {"item.jd.com": r"/([0-9]+)\.html",
                   "item.m.jd.com": r"/product/([0-9]+)\.html"}.get(parsed.hostname)
        match = re.fullmatch(pattern, parsed.path) if pattern else None
        return [match[1]] if match else []
    if marketplace in ("taobao", "goofish"):
        hosts, path = ({"item.taobao.com", "detail.tmall.com"}, "/item.htm") if marketplace == "taobao" else (
            {"www.goofish.com", "goofish.com"}, "/item")
        if parsed.hostname in hosts and parsed.path == path:
            return parse_qs(parsed.query, keep_blank_values=True).get("id", [])
    elif marketplace == "blibli" and parsed.hostname == "www.blibli.com":
        match = re.fullmatch(r"/p/[^/]+/(?:ps|is)--([A-Za-z0-9-]+)/?", parsed.path)
        return [match[1]] if match else []
    return []


def _identity_evidence(row, id_fields, original_price):
    """Retain every supplied identity, including aliases that normalization drops."""
    evidence = []

    def add(field, kind, value):
        entry = {"field": field, "kind": kind, "value": value}
        if value is not None and value != "" and entry not in evidence:
            evidence.append(entry)

    prior = row.get("identity_evidence")
    if isinstance(prior, list):
        for entry in prior:
            if (isinstance(entry, dict) and isinstance(entry.get("field"), str)
                    and entry.get("kind") in ("id", "url")):
                add(entry["field"], entry["kind"], entry.get("value"))

    def collect(source, prefix):
        if not isinstance(source, dict):
            return
        for field in (*id_fields, "productID"):
            add(prefix + field, "id", source.get(field))
        for field in ("url", "productUrl", "link"):
            add(prefix + field, "url", source.get(field))

    collect(row, "")
    offers = row.get("offers")
    if isinstance(offers, list):
        for index, offer in enumerate(offers):
            collect(offer, f"offers[{index}].")
    else:
        collect(offers, "offers.")
    if isinstance(original_price, dict):
        collect(original_price.get("structured_offer"), "price.structured_offer.")
    return evidence


def _identity_warnings(evidence, marketplace):
    ids, warnings = set(), []
    pattern = r"[A-Za-z0-9-]+" if marketplace == "blibli" else r"[0-9]+"
    for entry in evidence:
        value = entry["value"]
        values = _url_item_ids(value, marketplace) if entry["kind"] == "url" else [value]
        if not values or any(not isinstance(v, (str, int)) or isinstance(v, bool)
                             or not re.fullmatch(pattern, str(v).strip()) for v in values):
            warnings.append(f"Source identity at {entry['field']} cannot be bound to a marketplace item ID; price is not ranked.")
        else:
            ids.update(str(v).strip() for v in values)
    if len(ids) > 1:
        warnings.append("Source item IDs and product/Offer URL IDs conflict; price is not ranked.")
    return list(dict.fromkeys(warnings))


def _source_warnings(row):
    values = row.get("source_warnings") if "source_warnings" in row else row.get("warnings")
    if not isinstance(values, list):
        return []
    result = []
    for value in values:
        if isinstance(value, str):
            result.append(value[:500])
            if len(result) == 20:
                break
    return result


def normalize_offer(marketplace, row, observed_at=None):
    marketplace = marketplace_name(marketplace)
    if not isinstance(row, dict):
        raise ValueError("Each marketplace row must be an object")
    title = _text(row, "title", "name", "productName")
    if not title:
        raise ValueError("Marketplace row has no title")
    currency = CURRENCIES[marketplace]
    source_mode = _text(row, "source_mode") or "unspecified"
    original_price = row.get("price")
    # Direct normalization and rank/import must read the same retained source amount.
    price_envelope = original_price if isinstance(original_price, dict) and "basis" in original_price else {}
    if price_envelope:
        original_price = price_envelope.get("raw")
    structured_offer = row.get("offers")
    if isinstance(original_price, dict) and isinstance(original_price.get("structured_offer"), dict):
        structured_offer = original_price["structured_offer"]
    if isinstance(structured_offer, list):
        structured_offer = structured_offer[0] if len(structured_offer) == 1 else None
    machine_amount = None
    if (original_price is None or isinstance(original_price, dict) and "structured_offer" in original_price) and isinstance(structured_offer, dict):
        if structured_offer.get("@type") in (None, "Offer") and "price" in structured_offer:
            if original_price is None:
                original_price = {"structured_offer": structured_offer}
            try:
                machine_amount = format(decimal_value(structured_offer["price"], "structured price", positive=True), "f")
            except ValueError:
                pass
    selected_price = original_price
    if isinstance(original_price, dict):
        selected_price = original_price.get("priceDisplay")
    amount = machine_amount or parse_price(selected_price, currency)
    declared_currency = row.get("currency") or row.get("priceCurrency") or price_envelope.get("source_currency")
    if isinstance(structured_offer, dict):
        declared_currency = structured_offer.get("priceCurrency") or declared_currency
    if isinstance(original_price, dict):
        declared_currency = original_price.get("currency") or declared_currency
    currency_mismatch = declared_currency is not None and str(declared_currency).upper() != currency
    currency_observations = []
    currency_problem = None
    if marketplace in INTERNATIONAL_MARKETPLACES:
        retained = row.get("currency_observations", [])
        if not isinstance(retained, list) or len(retained) > 20 or any(not isinstance(v, str) for v in retained):
            retained = ["invalid_or_overflow_currency_evidence"]
        declarations = list(retained)
        for obj, keys in ((row, ("currency", "priceCurrency")),
                          (price_envelope, ("source_currency",)),
                          (original_price, ("currency", "priceCurrency")),
                          (structured_offer, ("priceCurrency",))):
            if isinstance(obj, dict):
                declarations.extend(str(obj[k]) for k in keys if obj.get(k) is not None)
        currency_observations = sorted({v.strip().upper()[:100] for v in declarations})
        if len(currency_observations) > 20:
            currency_observations = ["INVALID_OR_OVERFLOW_CURRENCY_EVIDENCE"]
        if len(currency_observations) != 1 or currency_observations[0] not in MONEY_SCALES:
            currency_problem = "International price currency is missing, unsupported or conflicting; numeric price withheld."
        else:
            currency = declared_currency = currency_observations[0]
        currency_mismatch = currency_problem is not None
        amount = machine_amount or parse_price(selected_price, currency)
    if currency_mismatch:
        amount = None
    price_basis = row.get("price_basis", price_envelope.get("basis", "displayed"))
    if source_mode == "search_index":
        price_basis = "search_index_unverified"
    elif source_mode in {"proxy_catalog", "indexed_product_block", "connector_product_open_cached", "category_card"}:
        price_basis = "source_observation_unverified"
    if price_basis != "displayed":
        amount = None
    purchase_constraints = None
    quantity_hold = False
    if marketplace in INTERNATIONAL_MARKETPLACES:
        quantity_keys = {"moq", "minOrderQuantity", "minimum_order_quantity", "min_order_quantity", "quantity", "lot_size"}
        tier_keys = {"price_tiers", "priceTiers", "tiers", "eligibleQuantity", "minQuantity", "maxQuantity", "numberOfItems"}
        retained = row.get("purchase_constraints", {})
        purchase_constraints = dict(retained) if isinstance(retained, dict) else {"invalid_evidence": True}
        for obj in (row, original_price, structured_offer):
            if isinstance(obj, dict):
                purchase_constraints.update({k: obj[k] for k in quantity_keys | tier_keys if k in obj})
        try:
            serialized = json.dumps(purchase_constraints, ensure_ascii=False, allow_nan=False)
            if len(serialized.encode("utf-8")) > 8000 or len(purchase_constraints) > 20:
                raise ValueError
        except (ValueError, TypeError, RecursionError):
            purchase_constraints = {"invalid_or_overflow_evidence": True}
        for key, value in purchase_constraints.items():
            # Only an explicit single-unit constraint is compatible with unit
            # ranking. Tier/order totals need a separately verified quantity.
            if (key not in quantity_keys or isinstance(value, bool)
                    or not re.fullmatch(r"1(?:\.0+)?(?:\s*(?:pieces?|units?))?", str(value).strip(), re.I)):
                quantity_hold = True
        if quantity_hold:
            amount, price_basis = None, "quantity_price_unverified"
    availability = row.get("availability", "unknown")
    if isinstance(availability, str) and availability.casefold() in {"out_of_stock", "outofstock", "https://schema.org/outofstock"}:
        availability = "unavailable"
    if availability not in {"unknown", "source_claimed_available", "delisted", "sold", "unavailable"}:
        availability = "unknown"
    if availability in {"delisted", "sold", "unavailable"}:
        amount = None
    item_id = _text(row, *ID_FIELDS[marketplace])
    identity_evidence = _identity_evidence(row, ID_FIELDS[marketplace], original_price)
    identity_warnings = _identity_warnings(identity_evidence, marketplace)
    source_url = row.get("url") or row.get("productUrl") or row.get("link")
    if not source_url and isinstance(structured_offer, dict):
        source_url = structured_offer.get("url")
    url = safe_url(source_url, marketplace)
    url_basis = "source_url" if url else "unknown"
    url_ids = _url_item_ids(url, marketplace)
    url_item_id = url_ids[0] if len(url_ids) == 1 else None
    if not item_id and url_item_id and (marketplace == "blibli" or re.fullmatch(r"[0-9]+", url_item_id)):
        item_id = url_item_id
    if not url and item_id:
        url = item_url(marketplace, item_id)
        if url:
            url_basis = "constructed_from_source_item_id"
    warnings = ["Displayed price; stock, exact variant, seller claims and checkout total are unverified."]
    if currency_mismatch:
        warnings.append(currency_problem or f"Explicit source currency {declared_currency} conflicts with expected {currency}; price is not ranked.")
    if price_basis != "displayed":
        warnings.append("Upstream price is a page minimum or other non-comparable amount; excluded from ranking.")
    if quantity_hold:
        warnings.append("MOQ, quantity or tier-price evidence does not establish a single-unit payable price.")
    if source_mode == "search_index":
        warnings.append("Search-index discovery only; current product price, stock and exact variant are not verified.")
    if availability in {"delisted", "sold", "unavailable"}:
        warnings.append(f"Source marks this listing {availability}; it is not a current purchase candidate.")
    if identity_warnings:
        warnings.extend(identity_warnings)
        amount = None
    if url_basis == "constructed_from_source_item_id":
        warnings.append("URL constructed from source item ID; product identity still needs confirmation.")
    if amount is None:
        warnings.append("No unambiguous positive single price; excluded from price ranking.")
    if not url:
        warnings.append("No verified marketplace URL; do not invent a product link.")
    if marketplace == "blibli":
        warnings.append("Blibli is in Indonesia. China-origin Fansbuy freight is not a verified route for this item.")
    # Signals are prompts for review, not a product-classification or authenticity decision.
    signals = []
    if marketplace == "goofish":
        signals.append("secondhand_marketplace_condition_needs_review")
    folded = title.casefold()
    for label, words in {
        "possible_deposit": ("定金", "订金", "deposit", "uang muka"),
        "possible_accessory_or_parts": ("配件", "拆机", "仅外壳", "for parts", "spare part"),
        "possible_used_or_damaged": ("二手", "故障", "维修", "闲置", "自用", "9成新", "95新", "used", "bekas", "rusak"),
    }.items():
        if any((re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", folded) is not None)
               if word.isascii() else word in folded for word in words):
            signals.append(label)
    if observed_at is not None:
        try:
            parsed_time = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
            if parsed_time.tzinfo is None:
                raise ValueError
        except (ValueError, TypeError, AttributeError):
            observed_at = None
            warnings.append("Invalid observation timestamp discarded.")
    if observed_at is None:
        warnings.append("Observation time unknown.")
    transaction_evidence = dict(row.get("transaction_evidence") or {}) if isinstance(row.get("transaction_evidence"), dict) else {}
    for key in ("payment_method", "payment_terms", "payment", "price_scope"):
        if isinstance(row.get(key), str):
            transaction_evidence[key] = row[key][:1000]
    for key in ("scope", "type"):
        if isinstance(price_envelope.get(key), str):
            transaction_evidence["price_" + key] = price_envelope[key][:1000]
    return {
        "marketplace": marketplace,
        "item_id": item_id,
        "title": title,
        "url": url,
        "url_basis": url_basis,
        "identity_evidence": identity_evidence,
        "currency_observations": currency_observations,
        "purchase_constraints": purchase_constraints,
        "offers": row.get("offers"),
        "price": {"amount": amount, "currency": currency, "raw": original_price, "basis": price_basis,
                  "source_currency": str(declared_currency).upper() if declared_currency is not None else None,
                  "currency_basis": "unverified_international_currency" if currency_problem else "explicit_source_field" if declared_currency else "marketplace_adapter_contract"},
        "seller": _text(row, "shop", "seller", "merchantName"),
        "description": (_text(row, "description", "desc", "snippet") or "")[:8000],
        "source_mode": source_mode,
        "model": _text(row, "model"),
        "selected_variant": _variant_text(row.get("selected_variant")),
        "variant_observations": _variant_observations(row),
        "variant_evidence": row.get("variant_evidence") if isinstance(row.get("variant_evidence"), dict) else row.get("variant") if isinstance(row.get("variant"), dict) else None,
        "transaction_evidence": transaction_evidence,
        "ranking_exclusions": [value[:500] for value in row.get("ranking_exclusions", [])[:20] if isinstance(value, str)] if isinstance(row.get("ranking_exclusions"), list) else [],
        "price_freshness_policy": row.get("price_freshness_policy") if isinstance(row.get("price_freshness_policy"), dict) else None,
        "hardware": row.get("hardware") if isinstance(row.get("hardware"), dict) else None,
        "candidate_id": _text(row, "candidate_id"),
        "source_detail": row.get("detail", row.get("source_detail")) if isinstance(row.get("detail", row.get("source_detail")), dict) else None,
        "index_source_url": _text(row, "index_source_url"),
        "discovered_at": _text(row, "discovered_at"),
        "location": _text(row, "location"),
        "domestic_free_shipping": row.get("domestic_free_shipping") if type(row.get("domestic_free_shipping")) is bool else None,
        "variant": _text(row, "variant", "spec"),
        "condition": _text(row, "condition") or "unknown",
        "availability": availability,
        "seller_trust": "unverified",
        "observed_at": observed_at,
        "signals": signals,
        "warnings": warnings,
        "source_warnings": _source_warnings(row),
    }
