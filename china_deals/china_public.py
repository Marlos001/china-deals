"""Conservative public metadata observations for Tmall, 1688 and Weidian.

This is a pure parser, not an acquisition client. It never establishes a selected
variant/single-unit price contract. Even a JSON-LD Offer remains a source claim
under source_detail; no offers or numeric price are exposed to normalization.
"""

import hashlib
import json
import re
from datetime import datetime
from html.parser import HTMLParser

from .marketplaces import (
    CURRENCIES,
    INTERNATIONAL_MARKETPLACES,
    MONEY_SCALES,
    PUBLIC_METADATA_MARKETPLACES,
    canonical_product_url,
    product_id,
)

_MAX_BODY = 2 * 1024 * 1024
_MAX_SCRIPTS = 64
_MAX_NODES = 4096
_META_KEYS = {"og:url", "og:type", "og:title", "og:description", "description",
              "product:price:amount", "product:price:currency", "og:price:amount", "og:price:currency"}
_PRODUCT_KEYS = ("name", "description", "url", "@id", "productID", "sku", "model",
                 "brand", "availability", "itemCondition", "price", "priceCurrency")
_OFFER_KEYS = ("@type", "@id", "url", "price", "priceCurrency", "lowPrice", "highPrice",
               "offerCount", "availability", "itemCondition", "eligibleQuantity", "priceSpecification")
_WEIDIAN_ID = "__rocker-render-inject__"
# The retained first-party carrier has this companion script URL. It is inert
# provenance, never fetched/executed or used in place of inline data-obj JSON.
# Deliberately pin the observed value: a different carrier needs new evidence.
_WEIDIAN_CARRIER_SRC = "//s.geilicdn.com/node/itemServerMixed/index/index.7da280e4305531c98caa.js"
_MAX_NATIVE_STATE = 256 * 1024
_WEIDIAN_ITEM_KEYS = ("item_id", "item_name", "itemShareDesc", "origin_price", "itemLowPrice",
                      "stock", "flag", "buyLimitInfo", "itemSellable", "isQuantify", "special_price_type")
_WEIDIAN_SKU_KEYS = ("attr_list", "sku", "skuCount", "skuShowName", "sku_attr")
_WEIDIAN_SKU_ROW_KEYS = ("id", "attr_ids", "title", "origin_price", "price", "stock", "isQuantify")
# Require quoted, whitespace-separated attributes rather than HTMLParser's
# error-recovering interpretation of malformed native identity carriers.
_NATIVE_TAG = re.compile(
    r'''<script(?:\s+[a-zA-Z_:][a-zA-Z0-9_.:-]*\s*=\s*(?:"[^"<]*"|'[^'<]*'))*\s*>''', re.I)
_IGNORED_CONTEXTS = {"template", "noscript", "textarea", "title", "xmp", "iframe",
                     "noembed", "noframes", "svg", "math", "select", "plaintext"}


class _Page(HTMLParser):
    def __init__(self, native_weidian=False):
        super().__init__(convert_charrefs=True)
        self.head = False
        self.head_seen = False
        self.html_open = False
        self.ignored = []
        self.script = None
        self.scripts = []
        self.metadata = {}
        self.canonicals = []
        self.native_weidian = native_weidian
        self.native_state = None
        self.native_pending = None
        self.body = False
        self.body_seen = False
        self.html_seen = False

    def handle_starttag(self, tag, attrs):
        if tag in (_IGNORED_CONTEXTS if self.native_weidian else {"template", "noscript"}):
            self.ignored.append(tag)
        if self.ignored:
            return
        # Duplicate attributes can change identity between HTML implementations.
        if tag in {"meta", "link", "script"} and len({k for k, _ in attrs}) != len(attrs):
            raise ValueError("Ambiguous HTML attributes")
        attrs = dict(attrs)
        if tag == "html":
            if self.native_weidian and self.html_seen:
                raise ValueError("Multiple Weidian documents")
            self.html_open = True
            self.html_seen = True
        elif tag == "head":
            if self.head_seen:
                raise ValueError("Multiple document heads")
            self.head = self.head_seen = True
        elif tag == "body":
            if self.native_weidian and (self.body_seen or not self.html_open):
                raise ValueError("Ambiguous Weidian document body")
            self.head = False
            self.body = True
            self.body_seen = True
        elif tag == "script":
            if self.native_weidian and attrs.get("id") == _WEIDIAN_ID:
                raw = self.get_starttag_text()
                if (not self.html_open or not self.body or self.head
                        or self.native_state is not None or self.native_pending is not None):
                    raise ValueError("Ambiguous or misplaced Weidian state carrier")
                if (len(raw.encode("utf-8")) > 2 * _MAX_NATIVE_STATE
                        or any(ord(c) < 32 and c not in "\t\n\r" for c in raw)
                        or not _NATIVE_TAG.fullmatch(raw)):
                    raise ValueError("Malformed or oversized Weidian carrier attributes")
                if "src" in attrs and attrs["src"] != _WEIDIAN_CARRIER_SRC:
                    raise ValueError("Unrecognized external Weidian state carrier")
                if attrs.get("type", "") not in {"", "text/javascript", "application/javascript"}:
                    raise ValueError("Unexpected Weidian carrier type")
                if not isinstance(attrs.get("data-obj"), str) or not attrs["data-obj"]:
                    raise ValueError("Missing inline Weidian state")
                self.native_pending = attrs
            self.script = ((attrs.get("type") or "").strip().lower(), [])
        elif tag == "meta" and self.head:
            key = (attrs.get("property") or attrs.get("name") or "").lower()
            if key in _META_KEYS:
                self.metadata.setdefault(key, []).append(attrs.get("content"))
        elif tag == "link" and self.head and "canonical" in (attrs.get("rel") or "").lower().split():
            self.canonicals.append(attrs.get("href"))

    def handle_data(self, data):
        if self.script is not None:
            self.script[1].append(data)

    def handle_startendtag(self, tag, attrs):
        if self.native_weidian and tag == "script" and dict(attrs).get("id") == _WEIDIAN_ID:
            raise ValueError("Self-closing Weidian state carrier")
        super().handle_startendtag(tag, attrs)

    def handle_endtag(self, tag):
        if self.ignored:
            # HTML plaintext consumes the remainder; an apparent closing tag
            # cannot make a later native carrier part of the real document.
            if tag == self.ignored[-1] and tag != "plaintext":
                self.ignored.pop()
            return
        if tag == "script" and self.script is not None:
            if self.native_pending is not None:
                if "".join(self.script[1]).strip():
                    raise ValueError("Unexpected content in Weidian state carrier")
                self.native_state = self.native_pending
                self.native_pending = None
            if self.script[0] == "application/ld+json":
                self.scripts.append("".join(self.script[1]))
                if len(self.scripts) > _MAX_SCRIPTS:
                    raise ValueError("Too many JSON-LD scripts")
            self.script = None
        elif tag == "head":
            self.head = False
        elif tag == "body":
            self.body = False
        elif tag == "html":
            self.html_open = False


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON-LD key")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError("Non-finite JSON-LD number")


def _bounded_tree(value):
    pending, count = [(value, 0)], 0
    while pending:
        node, depth = pending.pop()
        count += 1
        if count > _MAX_NODES or depth > 32:
            raise ValueError("JSON-LD structure exceeds limits")
        if isinstance(node, dict):
            pending.extend((v, depth + 1) for v in node.values())
        elif isinstance(node, list):
            pending.extend((v, depth + 1) for v in node)
        elif isinstance(node, float) and (node != node or abs(node) == float("inf")):
            raise ValueError("Non-finite JSON-LD number")


def _has_type(node, name):
    types = node.get("@type")
    return types == name or isinstance(types, list) and name in types


def _nodes(value):
    """Only document nodes/graphs, never nested recommendations or Offer items."""
    if isinstance(value, list):
        for node in value:
            yield from _nodes(node)
    elif isinstance(value, dict):
        yield value
        yield from _nodes(value.get("@graph"))


def _text(value, field, limit):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"Missing, invalid or oversized {field}")
    return value.strip()


def _claims(value, path, truncated, depth=0):
    """Bound auxiliary claims explicitly; never truncate identity for matching."""
    if depth > 4:
        truncated.append(path)
        return None
    if isinstance(value, str):
        if len(value) > 512:
            truncated.append(path)
        return value[:512]
    if isinstance(value, list):
        if len(value) > 8:
            truncated.append(path)
        return [_claims(v, f"{path}[{i}]", truncated, depth + 1) for i, v in enumerate(value[:8])]
    if isinstance(value, dict):
        if len(value) > 16 or any(len(k) > 128 for k in value):
            truncated.append(path)
        return {k[:128]: _claims(v, f"{path}.{k[:128]}", truncated, depth + 1)
                for k, v in list(value.items())[:16]}
    return value


def _weidian_item(state, identity, truncated):
    """Read only the observed primary path, never search sibling recommendations."""
    if len(state.encode("utf-8")) > _MAX_NATIVE_STATE or "\ufffd" in state:
        raise ValueError("Weidian state exceeds limits")
    try:
        payload = json.loads(state, object_pairs_hook=_unique, parse_constant=_invalid_constant)
        _bounded_tree(payload)
    except (ValueError, RecursionError):
        raise ValueError("Malformed, ambiguous or oversized Weidian state") from None
    if not isinstance(payload, dict):
        raise ValueError("Invalid Weidian state envelope")
    status = payload.get("status")
    if not isinstance(status, dict) or type(status.get("code")) is not int or status["code"] != 0:
        raise ValueError("Weidian state is not a successful item response")
    result = payload.get("result")
    model = result.get("default_model") if isinstance(result, dict) else None
    item = model.get("item_info") if isinstance(model, dict) else None
    if not isinstance(item, dict):
        raise ValueError("Missing primary Weidian item_info")
    if type(item.get("item_id")) not in {str, int} or str(item["item_id"]) != identity:
        raise ValueError("Weidian primary item ID conflicts with exact URL")
    _text(item.get("item_name"), "Weidian item name", 1000)
    # Preserve the literal native title, including source whitespace.
    title = item["item_name"]
    description = item.get("itemShareDesc", "")
    if not isinstance(description, str) or len(description) > 8000:
        raise ValueError("Invalid or oversized Weidian description")
    flags, limits = item.get("flag", {}), item.get("buyLimitInfo", {})
    if not isinstance(flags, dict) or not isinstance(limits, dict):
        raise ValueError("Invalid Weidian availability claims")
    for key in ("is_valid_item", "is_status_off_shelve", "is_status_deleted"):
        if key in flags and type(flags[key]) is not bool:
            raise ValueError("Invalid Weidian availability flag")
    if "itemSellable" in item and type(item["itemSellable"]) is not bool:
        raise ValueError("Invalid Weidian sellable flag")
    for key in ("buyButtonText", "limitBarText"):
        if key in limits and (not isinstance(limits[key], str) or len(limits[key]) > 512):
            raise ValueError("Invalid or oversized Weidian availability text")
    delisted = (flags.get("is_status_off_shelve") is True
                or flags.get("is_status_deleted") is True
                or any("商品已下架" in limits.get(k, "") for k in ("buyButtonText", "limitBarText")))
    unavailable = flags.get("is_valid_item") is False or item.get("itemSellable") is False
    availability = "delisted" if delisted else "unavailable" if unavailable else "unknown"
    sku = model.get("sku_properties", {})
    if not isinstance(sku, dict):
        raise ValueError("Invalid Weidian SKU claims")
    sku = {k: sku[k] for k in _WEIDIAN_SKU_KEYS if k in sku}
    if "sku" in sku:
        if not isinstance(sku["sku"], dict) or any(not isinstance(v, dict) for v in sku["sku"].values()):
            raise ValueError("Invalid Weidian SKU rows")
        sku["sku"] = {key: {k: value[k] for k in _WEIDIAN_SKU_ROW_KEYS if k in value}
                      for key, value in sku["sku"].items()}
    if "attr_list" in sku:
        attrs = sku["attr_list"]
        if (not isinstance(attrs, list) or any(not isinstance(a, dict) for a in attrs)
                or any(not isinstance(a.get("attr_values", []), list) for a in attrs)
                or any(not isinstance(v, dict) for a in attrs for v in a.get("attr_values", []))):
            raise ValueError("Invalid Weidian SKU attributes")
        sku["attr_list"] = [{"attr_title": a.get("attr_title"),
                             "attr_values": [{k: v[k] for k in ("attr_id", "attr_value") if k in v}
                                             for v in a.get("attr_values", [])]} for a in attrs]
    claims = {
        "item_info": {k: _claims(item[k], f"native.item_info.{k}", truncated)
                      for k in _WEIDIAN_ITEM_KEYS if k in item},
        "sku_properties": {k: _claims(sku[k], f"native.sku_properties.{k}", truncated)
                           for k in _WEIDIAN_SKU_KEYS if k in sku},
    }
    # Keep the controlling availability flags even when unrelated flags exceed
    # the auxiliary dictionary bound. Their literal values must remain auditable.
    if "flag" in item:
        claims["item_info"]["flag"] = {k: flags[k] for k in
                                      ("is_valid_item", "is_status_off_shelve", "is_status_deleted",
                                       "is_stock_limit", "is_sale_floor_item_conflict") if k in flags}
    return title, description, availability, claims


def parse_product_page(body, marketplace, requested_url, observed_at):
    """Return one raw normalize_offer-compatible, unpriced row or raise ValueError.

    Identity must come from one exact native URL-bound Product, unique product
    Open Graph metadata with an exact canonical/og:url, or Weidian's primary
    inline item state with an item_id matching the acquisition-verified URL.
    Acquisition must separately verify final URL, access status and transport
    completeness. observed_at is a timezone-aware caller-supplied ISO timestamp.
    """
    if not isinstance(marketplace, str) or marketplace not in PUBLIC_METADATA_MARKETPLACES:
        raise ValueError("Unsupported public metadata marketplace")
    url = canonical_product_url(marketplace, requested_url)
    if not url:
        raise ValueError("An exact native product URL is required")
    identity = product_id(marketplace, url)

    def bound_url(value):
        if marketplace == "alibaba" and isinstance(value, str):
            # The retained native page declares a protocol-relative localized
            # OG/Offer URL, with a different slug but the same exact product ID.
            value = "https:" + value if value.startswith("//") else value
            return product_id(marketplace, value) == identity
        return canonical_product_url(marketplace, value) == url

    def numeric_identity(value):
        return type(value) in {str, int} and str(value) == identity
    try:
        if not isinstance(observed_at, str) or datetime.fromisoformat(observed_at.replace("Z", "+00:00")).tzinfo is None:
            raise ValueError
    except (ValueError, TypeError):
        raise ValueError("A timezone-aware observation timestamp is required") from None
    if not isinstance(body, str) or len(body) > _MAX_BODY:
        raise ValueError("HTML body exceeds limits or is not text")
    try:
        encoded = body.encode("utf-8")
    except UnicodeError:
        raise ValueError("Invalid HTML text encoding") from None
    if len(encoded) > _MAX_BODY or "\ufffd" in body:
        raise ValueError("HTML body exceeds limits or has decoding damage")

    # Reuse the acquisition guard without importing guest at module load time.
    from .guest import _Failure, _html
    try:
        _html(body)
    except _Failure:
        raise ValueError("Public page is an access challenge") from None
    except (AssertionError, RecursionError):
        raise ValueError("Malformed HTML document") from None
    if re.search(r"<title\b[^>]*>[^<]*(?:登录|登陆|验证|login|sign in|captcha)", body, re.I):
        raise ValueError("Public page is a login or verification surface")
    page = _Page(native_weidian=marketplace == "weidian")
    try:
        page.feed(body)
    except (AssertionError, RecursionError):
        raise ValueError("Malformed HTML document") from None
    if page.script is not None or page.rawdata.strip() or page.head or page.html_open or page.ignored or page.body:
        raise ValueError("Incomplete HTML document or script")
    page.close()
    metadata = {}
    for key, values in page.metadata.items():
        if any(not isinstance(v, str) for v in values) or len(set(values)) != 1:
            raise ValueError("Conflicting or invalid primary metadata")
        metadata[key] = values[0]
    page_urls = page.canonicals + ([metadata["og:url"]] if "og:url" in metadata else [])
    if any(not bound_url(value) for value in page_urls):
        raise ValueError("Page URL identity conflicts with request")

    products, matches = [], []
    for script_index, script in enumerate(page.scripts):
        try:
            payload = json.loads(script, object_pairs_hook=_unique, parse_constant=_invalid_constant)
            _bounded_tree(payload)
        except (ValueError, RecursionError):
            raise ValueError("Malformed, ambiguous or oversized JSON-LD") from None
        nodes = list(_nodes(payload))
        for node in list(nodes):
            if _has_type(node, "WebPage") and bound_url(node.get("url")):
                nodes.extend(_nodes(node.get("mainEntity")))
        for node in nodes:
            if not _has_type(node, "Product"):
                continue
            products.append(node)
            urls = [(k, node[k]) for k in ("url", "@id") if k in node]
            numeric_bound = marketplace == "alibaba" and bool(page_urls) and numeric_identity(node.get("@id"))
            if not any(bound_url(v) for _, v in urls) and not numeric_bound:
                continue
            if any(not bound_url(v) and not (marketplace == "alibaba" and k == "@id" and numeric_identity(v)) for k, v in urls):
                raise ValueError("Product URL identity conflict")
            if marketplace == "alibaba" and "sku" in node and not numeric_identity(node["sku"]):
                raise ValueError("Alibaba primary SKU conflicts with product ID")
            if "productID" in node and (type(node["productID"]) not in {str, int} or str(node["productID"]) != identity):
                raise ValueError("Product ID conflicts with exact URL")
            matches.append((script_index, node))
    if len(matches) > 1:
        raise ValueError("Multiple matching Product nodes; identity is ambiguous")

    truncated = []
    availability, native_claims = "unknown", None
    if page.native_state is not None:
        if matches:
            raise ValueError("Multiple primary product sources are ambiguous")
        title, description, availability, native_claims = _weidian_item(
            page.native_state["data-obj"], identity, truncated)
        product_claims, offer_claims = {}, []
        provenance = {"kind": "weidian_native_state", "script_id": _WEIDIAN_ID,
                      "state_path": "result.default_model.item_info"}
        if "src" in page.native_state:
            provenance["inert_companion_src"] = page.native_state["src"]
    elif matches:
        script_index, product = matches[0]
        title = _text(product.get("name"), "Product name", 1000)
        description = product.get("description", "")
        if not isinstance(description, str) or len(description) > 8000:
            raise ValueError("Invalid or oversized Product description")
        product_claims = {k: _claims(product[k], f"product.{k}", truncated) for k in _PRODUCT_KEYS if k in product}
        offers = product.get("offers", [])
        offers = offers if isinstance(offers, list) else [offers]
        if len(offers) > 8:
            truncated.append("offers")
        offer_claims = [{k: _claims(o[k], f"offers[{i}].{k}", truncated) for k in _OFFER_KEYS if k in o}
                        for i, o in enumerate(offers[:8]) if isinstance(o, dict)]
        provenance = {"kind": "jsonld_product", "script_index": script_index}
    else:
        if products or not page_urls or metadata.get("og:type", "").lower() not in {"product", "og:product"}:
            raise ValueError("No unique exact-URL-bound primary Product metadata")
        title = _text(metadata.get("og:title"), "product Open Graph title", 1000)
        description = metadata.get("og:description", metadata.get("description", ""))
        if len(description) > 8000:
            raise ValueError("Oversized metadata description")
        product_claims, offer_claims = {}, []
        provenance = {"kind": "head_product_metadata"}
    detail = {"parser": "china_public_metadata_v1", "identity_binding": {"url": url, "item_id": identity},
              "provenance": provenance, "response_text_sha256": hashlib.sha256(encoded).hexdigest(),
              "response_text_bytes": len(encoded), "product_claims": product_claims,
              "offer_claims": offer_claims,
              "page_metadata_claims": {k: _claims(v, f"metadata.{k}", truncated) for k, v in metadata.items()},
              "claims_truncated": truncated,
              "price_contract": "unverified_selected_variant_single_unit",
              "hash_basis": "caller_supplied_html_utf8_not_transport_bytes"}
    if native_claims is not None:
        detail["native_state_claims"] = native_claims
    if len(json.dumps(detail, ensure_ascii=True)) > 32768:
        raise ValueError("Source claims exceed retained evidence limit")
    currencies = {str(v).upper() for v in [product_claims.get("priceCurrency"),
                  *(o.get("priceCurrency") for o in offer_claims),
                  metadata.get("product:price:currency"), metadata.get("og:price:currency")] if v is not None}
    source_currency = next(iter(currencies)) if len(currencies) == 1 and currencies <= MONEY_SCALES.keys() and "offers" not in truncated else None
    return {"marketplace": marketplace, "item_id": identity, "url": url, "nativeURL": url,
            "title": title, "description": description, "price": None,
            "currency": source_currency if marketplace in INTERNATIONAL_MARKETPLACES else CURRENCIES[marketplace],
            "price_basis": "source_observation_unverified", "source_mode": "guest_product_page",
            "observed_at": observed_at, "availability": availability, "condition": "unknown",
            "source_detail": detail,
            "ranking_exclusions": ["selected_variant_single_unit_price_unverified"],
            "source_warnings": ["Public product metadata only; selected variant, single-unit price, stock and checkout are unverified.",
                                "Published Offer and page price/currency fields are source claims only, never comparable quotes."]}
