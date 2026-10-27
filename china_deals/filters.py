"""Filters disclose native submission separately from local observed-field checks."""

from decimal import Decimal
from urllib.parse import urlencode

from .models import decimal_value

SORTS = ("relevance", "price-asc", "price-desc", "sales", "newest")
CONDITIONS = ("any", "new", "used", "refurbished")
KEYS = {"min_price", "max_price", "sort", "condition", "province", "city", "free_shipping"}


def validate_filters(filters=None):
    filters = dict(filters or {})
    if set(filters) - KEYS:
        raise ValueError("Unknown marketplace filter")
    for key in ("min_price", "max_price"):
        if filters.get(key) is not None:
            filters[key] = str(decimal_value(filters[key], key))
    if filters.get("min_price") is not None and filters.get("max_price") is not None:
        if Decimal(filters["min_price"]) > Decimal(filters["max_price"]):
            raise ValueError("min_price cannot exceed max_price")
    if filters.get("sort", "relevance") not in SORTS or filters.get("condition", "any") not in CONDITIONS:
        raise ValueError("Invalid sort or condition filter")
    for key in ("province", "city"):
        value = filters.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip() or len(value) > 100 or any(ord(c) < 32 for c in value)):
            raise ValueError("Location filters must be short nonempty strings")
    if filters.get("free_shipping") not in (None, True, False):
        raise ValueError("free_shipping must be boolean")
    return {key: value for key, value in filters.items()
            if value is not None and value is not False and not (key == "sort" and value == "relevance")
            and not (key == "condition" and value == "any")}


def native_plan(market, query, filters=None):
    filters = validate_filters(filters)
    params = {"q" if market in ("taobao", "goofish") else "keyword" if market == "jd" else "searchTerm": query}
    supported = set()
    if market == "taobao":
        for key, param in (("min_price", "startPrice"), ("max_price", "endPrice")):
            if key in filters:
                params[param] = filters[key]
                supported.add(key)
        if filters.get("sort") in {"price-asc", "price-desc", "sales"}:
            params["sort"] = {"price-asc": "price-asc", "price-desc": "price-desc", "sales": "sale-desc"}[filters["sort"]]
            supported.add("sort")
    roots = {"taobao": "https://s.taobao.com/search", "jd": "https://search.jd.com/Search",
             "goofish": "https://www.goofish.com/search", "blibli": "https://www.blibli.com/backend/search/products"}
    opencli = []
    if market == "goofish":
        for key in ("min_price", "max_price", "province", "city"):
            if key in filters:
                opencli += ["--" + key.replace("_", "-"), str(filters[key])]
                supported.add(key)
    elif market == "taobao" and filters.get("sort") in {"price-asc", "sales"}:
        opencli += ["--sort", {"price-asc": "price", "sales": "sale"}[filters["sort"]]]
    native_url = roots[market] + "?" + urlencode(params) if market in roots else None
    return {"marketplace": market, "requested": filters, "native_search_url": native_url,
            "documented_native_filters": sorted(supported), "opencli_argv": opencli,
            "submitted_native_filters": [], "unverified_or_local_filters": sorted(filters),
            "note": "A constructed URL or documented parameter does not prove native filtering was applied. Indexed discovery does not implement native facets."}


def evaluate_offer(offer, filters=None):
    filters = validate_filters(filters)
    failed, unknown, matched = [], [], []
    amount = offer.get("price", {}).get("amount")
    for key in ("min_price", "max_price"):
        if key not in filters:
            continue
        if amount is None:
            unknown.append(key)
        else:
            okay = Decimal(amount) >= Decimal(filters[key]) if key == "min_price" else Decimal(amount) <= Decimal(filters[key])
            (matched if okay else failed).append(key)
    if "condition" in filters:
        condition = str(offer.get("condition", "unknown")).casefold()
        known = {"new": {"new", "全新", "全新未使用", "baru"},
                 "used": {"used", "二手", "bekas"}, "refurbished": {"refurbished", "翻新", "reconditioned"}}
        if condition == "unknown":
            unknown.append("condition")
        else:
            (matched if condition in known[filters["condition"]] else failed).append("condition")
    for key in ("city", "province"):
        if key in filters:
            location = offer.get("location")
            if not location:
                unknown.append(key)
            else:
                (matched if filters[key].casefold() in location.casefold() else failed).append(key)
    if filters.get("free_shipping"):
        value = offer.get("domestic_free_shipping")
        (matched if value is True else failed if value is False else unknown).append("free_shipping")
    return {"status": "excluded" if failed else "unknown" if unknown else "matched", "matched": matched,
            "failed": failed, "unknown": unknown, "scope": "returned_observed_fields_only"}
