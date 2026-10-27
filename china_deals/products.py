"""Conservative title/selected-variant relevance, not product authentication.

Descriptions and catalog summaries cannot establish the product being sold.
Missing model, revision and configuration evidence remains uncertain.
"""

import re
import unicodedata


def _compact(text):
    return re.sub(r"[\W_]+", "", unicodedata.normalize("NFKC", text).casefold())


def _has(pattern, text):
    return re.search(pattern, unicodedata.normalize("NFKC", text), re.I) is not None


def intent_family(query):
    if not isinstance(query, str):
        raise ValueError("Query must be text")
    compact = _compact(query)
    if any(name in compact for name in ("iphone17promax", "苹果17promax", "apple17promax")):
        return "iphone-17-pro-max"
    if "airpodsmax" in compact:
        return "airpods-max"
    if "zephyrus" in compact or re.search(r"幻(?:14|15|16)|冰刃", query):
        return "rog-zephyrus"
    return None


def query_plan(query):
    """Suggest bounded queries without dropping the caller's explicit scope."""
    family = intent_family(query)
    if not query.strip() or len(query) > 500 or any(ord(c) < 32 for c in query):
        raise ValueError("Query must be 1..500 characters without controls")
    compact = _compact(query)
    broad_zephyrus = re.fullmatch(r"(?:all|todos|全部|所有)?(?:asus)?(?:rog)?zephyrus(?:all|todos|全部|所有)?", compact)
    if family == "iphone-17-pro-max" and compact in {
        "iphone17promax", "appleiphone17promax", "苹果iphone17promax", "苹果17promax", "apple17promax"
    }:
        chinese, blibli = ["苹果 iPhone 17 Pro Max 手机"], ["Apple iPhone 17 Pro Max"]
    elif family == "airpods-max" and compact in {"airpodsmax", "appleairpodsmax", "苹果airpodsmax"}:
        chinese, blibli = ["苹果 AirPods Max 头戴式耳机"], ["Apple AirPods Max headphones"]
    elif family == "rog-zephyrus" and broad_zephyrus:
        # Bounded families documented in docs/validation/rog-zephyrus-all.md.
        # 幻16 alone is not a unique G16 alias; retain the explicit Latin model.
        models = ("G14", "G15", "G16", "M16", "Duo", "S17")
        chinese = ["华硕 ROG Zephyrus 笔记本"] + [f"华硕 ROG Zephyrus {m} 笔记本" for m in models]
        blibli = ["ASUS ROG Zephyrus"] + [f"ASUS ROG Zephyrus {m}" for m in models]
    elif family:
        # Preserve every refinement, including unfamiliar ones. Adding a neutral
        # brand term must not turn a case/charger query into a whole-device query.
        chinese = [("华硕 " if family == "rog-zephyrus" else "苹果 ") + query]
        blibli = [query]
    else:
        chinese, blibli = [], [query]
    return {"query": query, "family": family, "marketplace_queries": {
        "taobao": list(chinese), "jd": list(chinese), "goofish": list(chinese), "blibli": blibli},
        "requires_agent_translation": family is None,
        "warnings": ["Suggested queries are bounded starting points, not exhaustive inventory or generation coverage.",
                     "Refined queries preserve original terms; additional translation may improve local recall.",
                     "Chinese-marketplace queries must include Chinese text. No search has been executed."]}


_BUNDLE = r"\b(?:with|includes?|including|bonus|free|gratis)\b|赠送|附赠|含赠品|包含|含|附带|配有"
_PRICE_RISK = (r"定金|订金|首付|月供|月付|每月|\bdeposit\b|uang\s+muka|"
               r"\binstall?ments?\b|\bmonthly\b|\bcicilan\b|per\s+(?:month|bulan)|/\s*(?:month|bulan|月)")
_NON_PRODUCT = (r"维修|修理|模型机|展示模型|高仿|精仿|山寨|复刻|"
                r"\b(?:repair|replica|counterfeit|dummy)\b|display\s+dummy")
_ACCESSORIES = {
    "iphone-17-pro-max": {
        "case": r"手机壳|保护壳|\b(?:case|casing|cover|housing)\b",
        "screen_protector": r"钢化膜|贴膜|screen\s*(?:protector|guard)|tempered\s*glass",
        "parts": r"屏幕总成|更换电池|replacement\s+(?:screen|battery)",
        "packaging": r"空盒|dus\s+kosong|empty\s+box",
    },
    "airpods-max": {
        "case": r"保护套|收纳包|\b(?:case|cover|casing|sarung|softcase|hardcase)\b",
        "cushions": r"耳垫|耳罩(?!式耳机)|ear\s*(?:pads?|cushions?)|earmuffs?|\bbantalan\b",
        "headband": r"头梁|replacement\s*headband|headband\s*(?:only|replacement)",
        "parts": r"充电线|charging\s*cable|headphone\s*stand|replacement\s*ear\s*cups?",
        "packaging": r"空盒|empty\s+box",
    },
    "rog-zephyrus": {
        "case": r"保护套|电脑包|laptop\s*(?:sleeve|bag)|\b(?:sleeve|case)\b",
        "charger": r"充电器|电源适配器|\b(?:charger|adapter)\b",
        "parts": r"键盘膜|贴纸|屏幕总成|散热风扇|(?:keyboard|battery|fan|motherboard|skin)\s+(?:for|untuk)|"
                 r"replacement\s+(?:keyboard|battery|fan|panel)",
        "packaging": r"空盒|empty\s+box",
    },
}


def _non_product(text):
    # Narrow literal negations/repair history are not an offer of a replica or
    # repair service. They are still unverified seller claims.
    text = re.sub(r"\b(?:no|not a|not)\s+(?:replica|counterfeit|dummy|repairs?)\b|"
                  r"非(?:高仿|精仿|山寨|复刻|模型机)|(?:无|没有|未经|已)维修|维修过",
                  "", text, flags=re.I)
    return _has(_NON_PRODUCT, text)


def _accessories(text, family):
    core = re.split(_BUNDLE, text, maxsplit=1, flags=re.I)[0]
    # A standalone selection takes priority even when the title advertises a bundle.
    # An explicit "only" in a bundle tail also cannot be erased by trimming.
    if _has(r"\bonly\b|单卖|单售|仅售", text):
        core = text
    return {kind for kind, pattern in _ACCESSORIES[family].items() if _has(pattern, core)}


def _models(text, family, allow_shorthand=False):
    compact = _compact(text)
    raw = re.sub(r"[‐‑‒–—−]", "-", unicodedata.normalize("NFKC", text).casefold())
    if family == "iphone-17-pro-max":
        matches = re.findall(r"(?:iphone|苹果|apple)[ -]*(\d{1,2})(?!\d)(?:[ -]*(pro[ -]*max|pro|plus|air|e))?", raw)
        if allow_shorthand:
            # A selected iPhone model commonly omits the repeated brand name.
            # Require an explicit suffix so 16GB/17-inch cannot become a phone.
            matches += re.findall(r"(?<![a-z0-9])(\d{1,2})(?!\d)[ -]*(pro[ -]*max|pro|plus|air)(?![a-z])", raw)
        return {number + _compact(suffix) for number, suffix in matches}
    if family == "airpods-max":
        return set(re.findall(r"airpods(max[12]?|pro[123]?|[1234])(?!\d)", compact))
    # Keep token separators: G16 32GB and G14 2024 are separate facts.
    raw = re.sub(r"zephyrus(?=[gmsd])", "zephyrus ", raw)
    models = {_compact(model) for model in re.findall(
        r"(?<![a-z0-9])(g14|g15|g16|m15|m16|s15|s17|duo(?:[ -]*(?:15|16))?)(?!\d)", raw)}
    for alias, model in (("幻14", "g14"), ("幻15", "g15"), ("幻16", "幻16")):
        if alias in compact:
            models.add(model)
    return models


def _constraints(text, family):
    """Only literal capacities/connectors/model identifiers; no hardware guesses."""
    compact = _compact(text)
    fields = {"capacity": set(re.findall(r"\d+(?:gb|tb)", compact)),
              "connector": {v for v in ("usbc", "lightning") if v in compact}}
    if family == "airpods-max":
        fields["model_identifier"] = set(re.findall(r"a(?:2096|3184|3454)(?!\d)", compact))
    return fields


def assess_product(offer, query):
    """Keep the public relevance contract; a match is a literal claim, not verification."""
    family = intent_family(query)
    result = {"family": family, "status": "uncertain", "listing_kind": "unknown", "reasons": [],
              "match_basis": "title_and_selected_variant", "price_scope_warnings": []}
    title, variant = (str(offer.get(key) or "") for key in ("title", "variant"))
    fields = [("title", title), ("selected_variant", variant)]
    if any(_has(_PRICE_RISK, value) for _, value in fields):
        result["price_scope_warnings"].append("possible_deposit_or_installment_price")
    if family is None:
        result["reasons"].append("unsupported_product_intent")
        return result

    def mismatch(kind, reason):
        result.update(status="mismatch", listing_kind=kind)
        result["reasons"].append(reason)
        return result

    requested_accessories = _accessories(query, family)
    for source, value in fields:
        if _non_product(value):
            return mismatch("accessory_or_non_product", f"{source}: explicit_non_product_or_replica_wording")
        accessories = _accessories(value, family)
        if accessories and (not requested_accessories or accessories.isdisjoint(requested_accessories)):
            return mismatch("accessory_or_non_product", f"{source}: accessory_parts_or_non_product_title")

    requested = _models(query, family)
    if family == "rog-zephyrus":
        for source, value in fields:
            if _has(r"\b(?:strix|tuf|flow)\b|枪神|魔霸|天选|幻(?:13|16)\s*翻转|\b(?:G614|G615|GV601|GZ30[12])\b", value):
                return mismatch("other_product", f"{source}: different_product_or_family")
    # Identity in a selected variant is independent of the advertised title.
    # Generic variant labels (colour/condition) can inherit title identity.
    observed_fields = [(source, _models(value, family, source == "selected_variant")) for source, value in fields]
    for source, observed in observed_fields:
        if requested and observed:
            compatible = set()
            for model in observed:
                if model in requested or (family == "airpods-max" and "max" in requested and model.startswith("max")):
                    compatible.add(model)
                elif family == "rog-zephyrus" and "duo" in requested and model.startswith("duo"):
                    compatible.add(model)
                elif family == "rog-zephyrus" and "幻16" in requested and model in {"g16", "m16"}:
                    compatible.add(model)
            # 幻16 is ambiguous between G16/M16, but excludes G14.
            ambiguous_alias = family == "rog-zephyrus" and "幻16" in observed and bool(requested & {"g16", "m16"})
            generic_max = family == "airpods-max" and "max" in observed and any(
                model.startswith("max") for model in requested)
            unresolved = ({"幻16"} if ambiguous_alias else set()) | ({"max"} if generic_max else set())
            if observed - compatible - unresolved:
                return mismatch("other_product", f"{source}: different_explicit_product_model")

    identity = any(_models(value, family, source == "selected_variant") for source, value in fields)
    if family == "rog-zephyrus":
        identity = any("zephyrus" in _compact(v) or _has(r"幻(?:14|15|16)|冰刃", v) for _, v in fields)
    if not identity:
        result["reasons"].append("requested_product_not_established_in_title_or_selected_variant")
        return result
    observed = _models(variant, family, True) or _models(title, family)
    if requested and (not observed or (family == "rog-zephyrus" and observed == {"幻16"} and "幻16" not in requested)):
        result["reasons"].append("requested_model_not_established")
        return result
    # A generic Max cannot establish Max 1/2; the conflict check above rejects
    # explicit differences, while absence of revision evidence stays unknown.
    if family == "airpods-max" and "max" in observed and requested - {"max"}:
        result["reasons"].append("requested_model_not_established")
        return result
    for key, wanted in _constraints(query, family).items():
        if not wanted:
            continue
        selected = _constraints(variant, family)[key]
        advertised = _constraints(title, family)[key]
        actual = selected or advertised
        if actual and actual.isdisjoint(wanted):
            return mismatch("other_product", f"different_explicit_{key}")
        if actual != wanted:
            result["reasons"].append(f"requested_{key}_not_established_for_selected_variant")
            return result
    if requested_accessories and not any(_accessories(value, family) & requested_accessories for _, value in fields):
        result["reasons"].append("requested_accessory_scope_not_established")
        return result
    result.update(status="match", listing_kind="accessory" if requested_accessories else "product")
    result["reasons"].append("requested_product_named")
    return result
