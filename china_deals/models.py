"""Small, conservative normalization boundary for untrusted marketplace records."""

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, urlparse, urlunsplit

MARKETPLACES = ("taobao", "jd", "goofish", "blibli")
ALIASES = {"xianyu": "goofish", "jd.com": "jd", "blibli.com": "blibli"}
CURRENCIES = {"taobao": "CNY", "jd": "CNY", "goofish": "CNY", "blibli": "IDR"}
HOSTS = {
    "taobao": ("taobao.com", "tmall.com"),
    "jd": ("jd.com",),
    "goofish": ("goofish.com",),
    "blibli": ("blibli.com",),
}


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
    structured_offer = row.get("offers")
    if isinstance(original_price, dict) and isinstance(original_price.get("structured_offer"), dict):
        structured_offer = original_price["structured_offer"]
    if isinstance(structured_offer, list):
        structured_offer = structured_offer[0] if len(structured_offer) == 1 else None
    machine_amount = None
    if (original_price is None or isinstance(original_price, dict) and "structured_offer" in original_price) and isinstance(structured_offer, dict):
        if structured_offer.get("@type") in (None, "Offer") and "price" in structured_offer:
            original_price = {"structured_offer": structured_offer}
            try:
                machine_amount = format(decimal_value(structured_offer["price"], "structured price", positive=True), "f")
            except ValueError:
                pass
    selected_price = original_price
    if isinstance(original_price, dict):
        selected_price = original_price.get("priceDisplay")
    amount = machine_amount or parse_price(selected_price, currency)
    declared_currency = row.get("currency") or row.get("priceCurrency")
    if isinstance(structured_offer, dict):
        declared_currency = structured_offer.get("priceCurrency") or declared_currency
    if isinstance(original_price, dict):
        declared_currency = original_price.get("currency") or declared_currency
    currency_mismatch = declared_currency is not None and str(declared_currency).upper() != currency
    if currency_mismatch:
        amount = None
    price_basis = row.get("price_basis", "displayed")
    if source_mode == "search_index":
        price_basis = "search_index_unverified"
    if price_basis != "displayed":
        amount = None
    availability = row.get("availability", "unknown")
    if availability not in {"unknown", "source_claimed_available", "delisted", "sold", "unavailable"}:
        availability = "unknown"
    if availability in {"delisted", "sold", "unavailable"}:
        amount = None
    id_fields = {"taobao": ("item_id", "itemId", "num_iid"),
                 "jd": ("item_id", "sku", "skuId"),
                 "goofish": ("item_id", "itemId"),
                 "blibli": ("item_id", "productSku", "sku")}
    item_id = _text(row, *id_fields[marketplace])
    source_url = row.get("url") or row.get("productUrl") or row.get("link")
    if not source_url and isinstance(structured_offer, dict):
        source_url = structured_offer.get("url")
    url = safe_url(source_url, marketplace)
    url_basis = "source_url" if url else "unknown"
    url_item_id = None
    if url:
        parsed = urlparse(url)
        if marketplace in ("taobao", "goofish"):
            url_item_id = parse_qs(parsed.query).get("id", [None])[0]
        elif marketplace == "jd":
            match = re.fullmatch(r"/(\d+)\.html", parsed.path)
            url_item_id = match.group(1) if match else None
        elif marketplace == "blibli":
            match = re.fullmatch(r"/p/[^/]+/(?:ps|is)--([A-Za-z0-9-]+)/?", parsed.path)
            url_item_id = match.group(1) if match else None
    if not item_id and url_item_id:
        item_id = url_item_id
    if not item_id and url:
        parsed = urlparse(url)
        candidate = parse_qs(parsed.query).get("id", [None])[0]
        if candidate and candidate.isdigit():
            item_id = candidate
        elif marketplace == "jd":
            match = re.fullmatch(r"/(\d+)\.html", parsed.path)
            item_id = match.group(1) if match else None
    if not url and item_id and item_id.isdigit():
        url = {
            "taobao": f"https://item.taobao.com/item.htm?id={item_id}",
            "jd": f"https://item.jd.com/{item_id}.html",
            "goofish": f"https://www.goofish.com/item?id={item_id}",
        }.get(marketplace)
        if url:
            url_basis = "constructed_from_source_item_id"
    warnings = ["Displayed price; stock, exact variant, seller claims and checkout total are unverified."]
    if currency_mismatch:
        warnings.append(f"Explicit source currency {declared_currency} conflicts with expected {currency}; price is not ranked.")
    if price_basis != "displayed":
        warnings.append("Upstream price is a page minimum or other non-comparable amount; excluded from ranking.")
    if source_mode == "search_index":
        warnings.append("Search-index discovery only; current product price, stock and exact variant are not verified.")
    if availability in {"delisted", "sold", "unavailable"}:
        warnings.append(f"Source marks this listing {availability}; it is not a current purchase candidate.")
    if item_id and url_item_id and item_id != url_item_id:
        warnings.append("Source item ID and product URL ID conflict; price is not ranked.")
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
    return {
        "marketplace": marketplace,
        "item_id": item_id,
        "title": title,
        "url": url,
        "url_basis": url_basis,
        "price": {"amount": amount, "currency": currency, "raw": original_price, "basis": price_basis,
                  "source_currency": str(declared_currency).upper() if declared_currency is not None else None,
                  "currency_basis": "explicit_source_field" if declared_currency else "marketplace_adapter_contract"},
        "seller": _text(row, "shop", "seller", "merchantName"),
        "description": (_text(row, "description", "desc", "snippet") or "")[:8000],
        "source_mode": source_mode,
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
    }
