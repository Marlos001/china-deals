"""Optional public buying-catalog observations, distinct from marketplace offers.

Jadeship disclaims affiliation and aggregates third-party data. Its displayed
price has no established selected variant, stock, or underlying fetch time.
No catalog amount is promoted to a rankable marketplace price.
"""

import json
import re
import time

from . import adapters, guest
from .models import normalize_offer, utc_now


def _taobao_id(value):
    if not isinstance(value, str):
        raise ValueError("Supply a Taobao numeric ID or exact native product URL")
    if re.fullmatch(r"[0-9]{1,30}", value):
        return value
    url = guest._product_url("taobao", value)
    item_id = guest._item_id("taobao", url) if url else None
    if not item_id or len(item_id) > 30:
        raise ValueError("Supply a Taobao numeric ID or exact native product URL")
    return item_id


def parse_jadeship(body, item_id, observed_at=None):
    """Decode bounded literal Next flight item props without executing scripts."""
    item_id = _taobao_id(item_id)
    if not isinstance(body, str) or len(body.encode("utf-8")) > guest.MAX_RESPONSE_BYTES:
        raise ValueError("Catalog HTML must be text within 2 MiB")
    parser = guest._html(body)
    matches = []
    prop_count = 0
    for _, script in parser.scripts:
        wrapper = re.fullmatch(r"\s*self\.__next_f\.push\((\[.*\])\)\s*;?\s*", script, re.S)
        if not wrapper:
            continue
        try:
            chunk = json.loads(wrapper[1], object_pairs_hook=guest._unique_object, parse_constant=guest._reject_constant)
        except (ValueError, RecursionError):
            continue
        if not (isinstance(chunk, list) and len(chunk) == 2 and chunk[0] == 1 and isinstance(chunk[1], str)):
            continue
        # Only literal object-valued item props; never scan unrelated prices or
        # evaluate React reference tokens, JavaScript, or embedded expressions.
        for match in re.finditer(r'"item"\s*:\s*(\{)', chunk[1]):
            prop_count += 1
            if prop_count > 100:
                raise adapters._Failure("unavailable", "catalog_schema_limit", "Too many item props to establish a unique quote; none admitted.")
            try:
                item, _ = json.JSONDecoder(object_pairs_hook=guest._unique_object,
                                          parse_constant=guest._reject_constant).raw_decode(chunk[1][match.start(1):])
            except (ValueError, RecursionError):
                raise adapters._Failure("unavailable", "catalog_schema_unverified", "Malformed item props prevent unique-quote verification.") from None
            if not isinstance(item, dict) or item.get("marketplace") != "taobao" or str(item.get("id")) != item_id:
                continue
            currencies = [item[key] for key in ("currency", "priceCurrency") if key in item]
            if any(not isinstance(value, str) or value.upper() != "CNY" for value in currencies):
                raise adapters._Failure("unavailable", "catalog_currency_conflict", "Explicit catalog currency conflicts with CNY; no quote admitted.")
            amount = guest._amount(item.get("price"))
            if amount is None or not isinstance(item.get("title"), str) or not item["title"].strip():
                raise adapters._Failure("unavailable", "catalog_schema_unverified", "Ambiguous same-item price/title prevents a unique catalog quote.")
            matches.append((item, amount))
    identities = {(item["title"], amount) for item, amount in matches}
    if len(identities) != 1:
        raise adapters._Failure("unavailable", "catalog_schema_unverified",
                                "No unique item-bound catalog title/price was validated; no price inferred.")
    title, amount = next(iter(identities))
    source_url = f"https://www.jadeship.com/item/taobao/{item_id}"
    native_url = f"https://item.taobao.com/item.htm?id={item_id}"
    observed_at = observed_at or utc_now()
    observation = {
        "provider": "jadeship", "marketplace": "taobao", "item_id": item_id,
        "title": title, "source_url": source_url, "native_url": native_url,
        "amount": amount, "currency": "CNY", "observed_at": observed_at,
        "price_basis": "third_party_catalog_display", "underlying_fetched_at": None,
        "variant": None, "condition": "unknown", "availability": "unknown", "coupon_eligibility": "unknown",
        "evidence": [item for item, _ in matches],
        "warnings": ["Catalog display only; underlying freshness, exact variant, stock and authenticity are unknown.",
                     "The catalog is a third-party aggregator, not a Taobao offer or verified checkout quote.",
                     "No coupon, account entitlement or Fansbuy purchasing acceptance was established."],
    }
    row = normalize_offer("taobao", {
        "title": title, "item_id": item_id, "url": native_url, "price": amount,
        "price_basis": "catalog_quote_unverified", "currency": "CNY", "source_mode": "proxy_catalog",
        "detail": {"catalog_observation": observation},
    }, observed_at)
    return observation, row


def get_catalog_item(marketplace, value, timeout=30):
    """One unauthenticated Jadeship read. Only Taobao is currently validated."""
    if marketplace != "taobao":
        raise ValueError("The validated Jadeship catalog reader currently supports Taobao only")
    item_id = _taobao_id(value)
    source_url = f"https://www.jadeship.com/item/taobao/{item_id}"
    deadline = time.monotonic() + adapters._timeout(timeout)
    result = guest._envelope(marketplace)
    result.update(schema_version="1", provider="jadeship", source_mode="proxy_catalog",
                  catalog_observations=[], coverage="one_third_party_catalog_item")
    try:
        body, final_url = guest._read(result, source_url, {"www.jadeship.com"}, deadline, "proxy_catalog")
        if final_url != source_url:
            raise adapters._Failure("unavailable", "catalog_url_mismatch", "Catalog response moved away from the requested item.")
        observation, row = parse_jadeship(body, item_id)
        result.update(status="catalog_only", catalog_observations=[observation], items=[row])
        result["warnings"].extend(observation["warnings"])
        return result
    except adapters._Failure as exc:
        return guest._failure(result, exc)
