"""Strict, offline extraction of Blibli's public primary product state.

No JavaScript is evaluated. Unsupported or contradictory state raises ValueError;
an absent/ambiguous price or unavailable selection is returned without a price.
"""

import json
import re
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

_STATE = "__PRODUCT_DETAIL_INITIAL_STATE__"
_ASSIGNMENT = re.compile(
    r"(?<![\w$])(?:window\s*\.\s*)?" + _STATE + r"\s*=(?!=)"
    r"|window\s*\[\s*['\"]" + _STATE + r"['\"]\s*\]\s*=(?!=)"
)
_SKU = re.compile(r"[A-Z0-9]+-[0-9]+-[0-9]+")
_MAX_BODY = 2 * 1024 * 1024


class _Scripts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.scripts = []
        self.current = None
        self.executable = False

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            attrs = dict(attrs)
            self.current = []
            self.executable = "src" not in attrs and attrs.get("type", "").lower() in (
                "", "text/javascript", "application/javascript", "module"
            )

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.current is not None:
            self.scripts.append(("".join(self.current), self.executable))
            self.current = None


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "template", "iframe", "object"}:
            self.hidden.append(tag)
        if not self.hidden:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if self.hidden and tag == self.hidden[-1]:
            self.hidden.pop()
        if not self.hidden:
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def _text(value, limit=8000):
    if not isinstance(value, str):
        raise ValueError("Expected product text")
    if len(value) > 65536:
        raise ValueError("Oversized product text")
    parser = _Text()
    parser.feed(value)
    parser.close()
    result = " ".join("".join(parser.parts).split())
    if len(result) > limit:
        raise ValueError("Product text exceeds evidence bound")
    return result


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON property")
        result[key] = value
    return result


def _number(value):
    number = Decimal(value)
    if (not number.is_finite() or abs(number) > 10**15
            or number.as_tuple().exponent < -10 or len(number.as_tuple().digits) > 18):
        raise ValueError("JSON number exceeds bounds")
    if number == number.to_integral_value():
        return int(number)
    result = float(number)
    if Decimal(str(result)) != number:
        raise ValueError("JSON number loses decimal precision")
    return result


def _constant(value):
    raise ValueError("Non-JSON numeric constant")


def _decode(text):
    """Bound nesting before invoking the duplicate-key rejecting JSON decoder."""
    text = text.lstrip()
    if not text.startswith("{"):
        raise ValueError("Product state must be a JSON object")
    stack, quoted, escaped = [], False, False
    for index, char in enumerate(text):
        if quoted:
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
            if len(stack) > 64:
                raise ValueError("Product state nesting exceeds bound")
        elif char in "}]":
            if not stack or stack.pop() != {"}": "{", "]": "["}[char]:
                raise ValueError("Unbalanced product state")
            if not stack:
                suffix = text[index + 1:].lstrip()
                if suffix and not suffix.startswith(";"):
                    raise ValueError("Product state is not a literal assignment")
                return json.loads(text[:index + 1], object_pairs_hook=_object,
                                  parse_int=_number, parse_float=_number, parse_constant=_constant)
    raise ValueError("Incomplete product state")


def _route(value):
    if not isinstance(value, str) or len(value) > 2048 or re.search(r"[\s\\%]", value):
        raise ValueError("Invalid Blibli product URL")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or parsed.netloc != "www.blibli.com"
            or parsed.fragment):
        raise ValueError("Not a native Blibli product URL")
    match = re.fullmatch(r"/p/[^/]+/(ps|is)--([A-Z0-9-]+)/?", parsed.path)
    if not match:
        raise ValueError("Invalid Blibli product route")
    query = parse_qs(parsed.query, keep_blank_values=True)
    if any(len(values) != 1 for values in query.values()):
        raise ValueError("Ambiguous product URL query")
    pickup_query = urlencode({"pickupPointCode": query["pickupPointCode"][0]}) if "pickupPointCode" in query else ""
    return match[1], match[2], urlunsplit((parsed.scheme, parsed.netloc, parsed.path, pickup_query, "")), query


def _amount(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    raw = str(value)
    if not re.fullmatch(r"(?:0|[1-9][0-9]{0,14})(?:\.[0-9]{1,2})?", raw):
        return None
    try:
        number = Decimal(raw)
    except InvalidOperation:
        return None
    if number <= 0:
        return None
    # Numeric values avoid interpreting a machine decimal as an IDR thousands separator.
    if number == number.to_integral_value():
        return int(number)
    result = float(number)
    return result if Decimal(str(result)) == number else None


def parse_product_state(body, requested_url, observed_at):
    """Return one raw normalize_offer-compatible row; raise ValueError on bad state.

    observed_at is retained exactly, without consulting a clock. Parent (ps) URLs
    may select an explicit child; item (is) URLs must identify that exact child.
    """
    if not isinstance(body, str) or len(body) > _MAX_BODY:
        raise ValueError("Product response exceeds 2 MiB or is not text")
    try:
        if len(body.encode("utf-8")) > _MAX_BODY:
            raise ValueError("Product response exceeds 2 MiB")
    except UnicodeError as exc:
        raise ValueError("Invalid product response encoding") from exc
    # Count throughout the response, including malformed/duplicate script blocks.
    if len(list(_ASSIGNMENT.finditer(body))) != 1:
        raise ValueError("Expected exactly one primary state assignment")
    parser = _Scripts()
    parser.feed(body)
    parser.close()
    matches = [(script, _ASSIGNMENT.search(script), executable)
               for script, executable in parser.scripts if _ASSIGNMENT.search(script)]
    if len(matches) != 1:
        raise ValueError("Primary state is not in a closed script")
    script, match, executable = matches[0]
    if not executable or script[:match.start()].strip():
        raise ValueError("Unsupported primary state assignment context")
    state = _decode(script[match.end():])
    summary = state.get("productDetail.product/summary")
    if not isinstance(summary, dict):
        raise ValueError("Missing primary product summary")
    product, item = summary.get("productSku"), summary.get("itemSku")
    if (not isinstance(product, str) or not _SKU.fullmatch(product)
            or not isinstance(item, str) or not re.fullmatch(re.escape(product) + r"-[0-9]+", item)):
        raise ValueError("Invalid parent/child SKU binding")
    kind, requested_id, url, requested_query = _route(requested_url)
    if requested_id != (product if kind == "ps" else item):
        raise ValueError("Requested SKU conflicts with primary product")
    native_kind, native_id, _, native_query = _route(summary.get("url"))
    if native_kind != "is" or native_id != item:
        raise ValueError("Native selected URL conflicts with item SKU")
    canonical = summary.get("seo", {}).get("canonicalUrl") if isinstance(summary.get("seo"), dict) else None
    if canonical is not None and _route(canonical)[:2] != ("ps", product):
        raise ValueError("Canonical URL conflicts with product SKU")
    options = summary.get("options")
    if not isinstance(options, list) or not 1 <= len(options) <= 200:
        raise ValueError("Missing or oversized product options")
    ids, selected = set(), []
    for option in options:
        if (not isinstance(option, dict) or type(option.get("selected")) is not bool
                or type(option.get("available")) is not bool):
            raise ValueError("Invalid option selection flags")
        option_id = option.get("id")
        if (not isinstance(option_id, str) or len(option_id) > 200 or option_id in ids
                or not re.fullmatch(r"is--" + re.escape(product) + r"-[0-9]+_PP-[A-Z0-9-]+", option_id)):
            raise ValueError("Duplicate or invalid option identity")
        ids.add(option_id)
        if option["selected"]:
            selected.append(option)
    if len(selected) != 1:
        raise ValueError("Expected exactly one selected option")
    selected = selected[0]
    pickup = summary.get("pickupPointCode")
    if not isinstance(pickup, str) or not re.fullmatch(r"PP-[A-Z0-9-]+", pickup):
        raise ValueError("Invalid selected pickup point")
    if (selected["id"] != f"is--{item}_{pickup}" or selected.get("pickupPointCode") != pickup
            or native_query.get("pickupPointCode") != [pickup]
            or requested_query.get("pickupPointCode", [pickup]) != [pickup]):
        raise ValueError("Selected option or pickup point conflicts with native item")
    for key, expected in (("itemSku", item), ("productSku", product)):
        if key in selected and selected[key] != expected:
            raise ValueError("Selected option SKU conflicts with summary")
    if "url" in selected:
        selected_kind, selected_id, _, selected_query = _route(selected['url'])
        if ((selected_kind, selected_id) != ('is', item)
                or selected_query.get('pickupPointCode', [pickup]) != [pickup]):
            raise ValueError("Selected option URL conflicts with summary or pickup point")
    attributes = selected.get("attributes")
    if not isinstance(attributes, list) or not 1 <= len(attributes) <= 20:
        raise ValueError("Missing selected variant attributes")
    variant = {}
    for attribute in attributes:
        if not isinstance(attribute, dict):
            raise ValueError("Invalid selected attribute")
        name, value = _text(attribute.get("name"), 200), _text(attribute.get("value"), 500)
        if not name or not value or name in variant:
            raise ValueError("Ambiguous selected variant")
        variant[name] = value
    catalog = summary.get("attributes")
    if catalog is not None:
        if not isinstance(catalog, list) or len(catalog) > 20:
            raise ValueError("Invalid product attribute catalog")
        choices = {}
        for attribute in catalog:
            if not isinstance(attribute, dict) or not isinstance(attribute.get("values"), list):
                raise ValueError("Invalid product attribute choices")
            name = _text(attribute.get("name"), 200)
            if name in choices or len(attribute["values"]) > 200:
                raise ValueError("Ambiguous product attribute choices")
            choices[name] = {_text(entry.get("value"), 500) for entry in attribute["values"]
                             if isinstance(entry, dict)}
        if any(name not in choices or value not in choices[name] for name, value in variant.items()):
            raise ValueError("Selected variant conflicts with product attributes")
    title = _text(summary.get("name"), 2000)
    if not title:
        raise ValueError("Missing product title")
    descriptions = [_text(summary[key]) for key in ("description", "shortDescription", "uniqueSellingPoint")
                    if summary.get(key)]
    description_state = state.get("productDetail.product/description")
    if description_state is not None:
        if not isinstance(description_state, dict):
            raise ValueError("Unsupported product description state")
        for key, expected in (("productSku", product), ("itemSku", item)):
            if key in description_state and description_state[key] != expected:
                raise ValueError("Description identity conflicts with summary")
        descriptions.extend(_text(description_state[key]) for key in ("description", "shortDescription")
                            if description_state.get(key))
    descriptions.append("; ".join(f"{key}: {value}" for key, value in variant.items()))
    description = "\n".join(dict.fromkeys(descriptions))
    if len(description) > 8000:
        raise ValueError("Product description exceeds evidence bound")
    price = summary.get("price")
    if not isinstance(price, dict):
        raise ValueError("Missing source price object")
    currencies = [obj[key] for obj in (summary, price, selected)
                  for key in ("currency", "priceCurrency") if key in obj]
    if any(not isinstance(value, str) or value.upper() != "IDR" for value in currencies):
        raise ValueError("Explicit currency conflicts with IDR adapter contract")
    if "price" in selected and selected["price"] != price:
        raise ValueError("Selected variant price conflicts with summary")
    amount = _amount(price.get("offered"))
    listed = _amount(price.get("listed"))
    warnings = ["Listed price and discount percentages are source claims, not historical savings."]
    # Unknown additional price fields may represent ranges, installments or other variants.
    known_price = {"offered", "listed", "listDiscount", "totalDiscount", "currency", "priceCurrency"}
    if (set(price) - known_price or ("listed" in price and listed is None)
            or (amount is not None and listed is not None and amount > listed)):
        amount = None
        warnings.append("Ambiguous or contradictory primary price; excluded from ranking.")
    stock = summary.get("stock")
    if type(stock) is not int or stock < 0:
        raise ValueError("Invalid primary stock")
    availability = "source_claimed_available" if stock > 0 and selected["available"] else "unavailable"
    if availability == "unavailable":
        amount = None
    merchant = summary.get("merchant", {})
    if not isinstance(merchant, dict):
        raise ValueError("Invalid merchant claims")
    merchant_claims = {key: merchant[key] for key in
                       ("name", "code", "official", "international", "location", "url", "status", "rating")
                       if key in merchant}
    detail = {"parser": "blibli_primary_product_state", "productSku": product, "itemSku": item,
              "native_url": summary["url"], "requested_url": requested_url,
              "selected_option": selected, "price_claims": price, "stock_claim": stock,
              "merchant_claims": merchant_claims, "fulfillment_claims": summary.get("fulfillmentTypes"),
              "currency_basis": "explicit_source_field" if currencies else "marketplace_adapter_contract"}
    server_time = state.get("productDetail.product/serverTime")
    if isinstance(server_time, dict) and isinstance(server_time.get("headers"), dict):
        server_date = server_time["headers"].get("date")
        if isinstance(server_date, str):
            detail["server_date_claim"] = server_date[:100]
    if len(json.dumps(detail, ensure_ascii=True)) > 32768:
        raise ValueError("Primary source evidence exceeds bound")
    row = {"item_id": requested_id, "url": url, "nativeURL": url, "title": title,
           "description": description, "seller": _text(merchant.get("name", ""), 1000),
           "price": amount, "availability": availability, "source_mode": "guest_product_page",
           "observed_at": observed_at, "source_warnings": warnings, "source_detail": detail,
           "variant_evidence": {"productSku": product, "itemSku": item, "attributes": variant,
                                "selected": True, "available": selected["available"]}}
    if currencies:
        row["currency"] = "IDR"
    variant_text = "; ".join(f"{key}: {value}" for key, value in variant.items())
    row["variant"] = f"{variant_text}; SKU {item}; pickup {pickup}"
    row["selected_variant"] = row["variant"]
    row["original_price"] = listed
    row["discount_percent"] = price.get("totalDiscount")
    fulfillment = summary.get("fulfillmentTypes")
    if isinstance(fulfillment, dict) and fulfillment.get("delivery") == "UNAVAILABLE":
        row["source_warnings"].append("Source marks delivery unavailable; pickup and procurement require confirmation.")
    return row
