"""Marketplace contracts and pure, conservative native product URL helpers.

Fansbuy's indexed Beginner Guide and procurement copy explicitly named the five entries
in FANSBUY_MARKETPLACES in evidence captured 2026-10-27. This is a dated named
support claim, not an exhaustive inventory, current checkout or freight proof.
Sources: https://fansbuy.com/beginnerGuide and https://m.fansbuy.com/user/promo.
Retained evidence: .local/fansbuy-expansion/root-discovery/official-index-findings.md.
No network access is performed by this module.
"""

import re
from urllib.parse import parse_qsl, urlsplit

MARKETPLACES = ("taobao", "jd", "goofish", "blibli", "tmall", "1688", "weidian")
ALIASES = {
    "xianyu": "goofish", "jd.com": "jd", "blibli.com": "blibli",
    "alibaba1688": "1688", "1688.com": "1688", "tmall.com": "tmall", "weidian.com": "weidian",
}
CURRENCIES = {market: "IDR" if market == "blibli" else "CNY" for market in MARKETPLACES}
HOSTS = {
    # Historical Taobao records may contain Tmall URLs. Keep this acceptance.
    "taobao": ("taobao.com", "tmall.com"),
    "jd": ("jd.com",),
    "goofish": ("goofish.com",),
    "blibli": ("blibli.com",),
    "tmall": ("tmall.com",),
    "1688": ("1688.com",),
    "weidian": ("weidian.com",),
}
ID_FIELDS = {
    "taobao": ("item_id", "itemId", "num_iid"),
    "jd": ("item_id", "sku", "skuId"),
    "goofish": ("item_id", "itemId"),
    "blibli": ("item_id", "productSku", "sku"),
    "tmall": ("item_id", "itemId", "num_iid"),
    "1688": ("offerId", "offer_id", "item_id", "id"),
    "weidian": ("itemID", "itemId", "item_id"),
}
PRODUCT_HOSTS = {
    "taobao": frozenset({"item.taobao.com", "detail.tmall.com"}),
    "jd": frozenset({"item.jd.com", "item.m.jd.com"}),
    "goofish": frozenset({"www.goofish.com", "goofish.com"}),
    "blibli": frozenset({"www.blibli.com"}),
    "tmall": frozenset({"detail.tmall.com"}),
    "1688": frozenset({"detail.1688.com"}),
    "weidian": frozenset({"weidian.com"}),
}
DISCOVERY_DOMAINS = {
    "taobao": "item.taobao.com", "jd": "item.jd.com", "goofish": "www.goofish.com",
    "blibli": "www.blibli.com/p/", "tmall": "detail.tmall.com", "1688": "detail.1688.com",
    "weidian": "weidian.com",
}
FANSBUY_MARKETPLACES = ("taobao", "tmall", "1688", "weidian", "jd")
CHINESE_MARKETPLACES = tuple(market for market in MARKETPLACES if market != "blibli")

_ITEM_URLS = {
    "taobao": "https://item.taobao.com/item.htm?id={}",
    "jd": "https://item.jd.com/{}.html",
    "goofish": "https://www.goofish.com/item?id={}",
    "tmall": "https://detail.tmall.com/item.htm?id={}",
    "1688": "https://detail.1688.com/offer/{}.html",
    "weidian": "https://weidian.com/item.html?itemID={}",
}
_QUERY_ID_KEYS = frozenset({"id", "itemid", "item_id", "num_iid", "offerid", "offer_id", "productid"})


def _market(value):
    return ALIASES.get(value.lower(), value.lower()) if isinstance(value, str) else None


def item_url(market, item_id):
    """Construct a known native URL from an ASCII numeric ID, else return None.

    Blibli requires a source product slug, so an ID alone cannot construct it.
    """
    template = _ITEM_URLS.get(_market(market))
    if (not template or isinstance(item_id, bool) or not isinstance(item_id, (str, int))
            or not re.fullmatch(r"[0-9]+", str(item_id))):
        return None
    return template.format(item_id)


def _product(market, value):
    """Return (canonical URL, ID) only for an unambiguous native route."""
    market = _market(market)
    if (market not in PRODUCT_HOSTS or not isinstance(value, str)
            or re.search(r"[\\\s\x00-\x1f\x7f]", value)):
        return None
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or parsed.hostname not in PRODUCT_HOSTS[market]
                or parsed.netloc != parsed.hostname or parsed.port is not None
                or parsed.username is not None or parsed.password is not None):
            return None
        query_ids = [(key, val) for key, val in parse_qsl(parsed.query, keep_blank_values=True)
                     if key.casefold() in _QUERY_ID_KEYS]
    except ValueError:
        return None
    if market in {"taobao", "tmall", "goofish", "weidian"}:
        path = {"taobao": "/item.htm", "tmall": "/item.htm", "goofish": "/item",
                "weidian": "/item.html"}[market]
        key = "itemID" if market == "weidian" else "id"
        if (parsed.path != path or len(query_ids) != 1 or query_ids[0][0] != key
                or not re.fullmatch(r"[0-9]+", query_ids[0][1])):
            return None
        identity = query_ids[0][1]
        # Preserve the native Tmall host on legacy Taobao records.
        canonical = (f"https://{parsed.hostname}/item.htm?id={identity}" if market == "taobao"
                     else item_url(market, identity))
        return canonical, identity
    # Path IDs cannot also carry query IDs: even matching values are ambiguous.
    if query_ids:
        return None
    if market == "blibli":
        match = re.fullmatch(r"/p/[^/]+/(?:ps|is)--([A-Za-z0-9-]+)/?", parsed.path)
        return ("https://www.blibli.com" + parsed.path.rstrip("/"), match[1]) if match else None
    pattern = (r"/offer/([0-9]+)\.html" if market == "1688" else
               r"/product/([0-9]+)\.html" if parsed.hostname == "item.m.jd.com" else r"/([0-9]+)\.html")
    match = re.fullmatch(pattern, parsed.path)
    return (item_url(market, match[1]), match[1]) if match else None


def canonical_product_url(market, url):
    """Drop tracking/fragments only after validating host, route and identity."""
    product = _product(market, url)
    return product[0] if product else None


def product_id(market, url):
    """Read a native route ID; opaque tokens and conflicting query IDs fail closed."""
    product = _product(market, url)
    return product[1] if product else None
