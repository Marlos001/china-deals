"""Literal laptop observations and conservative, currency-local price comparisons.

No model-code lookup, performance score, currency conversion, freight or discount
estimate is performed. Evidence offsets are Python string offsets, end exclusive.
"""

import copy
import math
import re
from decimal import Decimal

from .models import normalize_offer

FIELDS = (
    "cpu", "gpu", "gpu_variant", "vram_gb", "gpu_tgp_w", "ram_gb", "ssd_gb",
    "display_resolution", "display_refresh_hz", "display_technology", "display_size_inches",
    "model_code", "model_year", "condition", "product_family", "product_chassis",
)
# Model codes/years do not prove hardware. Every hardware dimension and an
# explicit family/chassis must be observed before candidates can share a group.
COMPARISON_FIELDS = tuple(f for f in FIELDS if f not in ("model_code", "model_year"))
_CAPACITY = r"(?<![\d_.])(\d+(?:\.\d+)?)\s*(GB|TB|G|T)(?![A-Za-z])"
_RAM = r"RAM|(?:LP)?DDR[345](?:X)?|内存"
_SSD = r"SSD|NVMe|固态(?:硬盘)?"
_PRODUCT = r"(?:ASUS[®™]?|ROG|Zephyrus|[GM]1[456]|S17|Duo\s*16|笔记本|laptop|notebook)"
_IDENTITY_FIELDS = ("product_family", "product_chassis", "model_code", "model_year")
_DISPLAY_LABEL = r"(?:[234](?:\.\d)?K|QHD\+?|WQXGA|FHD\+?|UHD)"
_PIXELS = r"\d{3,4}\s*[x×]\s*\d{3,4}"


def _matches(pattern, text):
    return re.finditer(pattern, text, re.I)


def _finish(observations):
    result = {field: None for field in FIELDS}
    result["evidence"] = observations
    result["conflicts"] = {}
    for field, records in observations.items():
        values = list(dict.fromkeys(record["value"] for record in records))
        if len(values) == 1:
            result[field] = values[0]
        elif values:
            result["conflicts"][field] = values
    result["unknown_fields"] = [field for field in FIELDS if result[field] is None]
    return result


def extract_hardware(text: str) -> dict:
    """Extract explicitly stated facts; alternatives/conflicts have null values.

    Flat fields are accompanied by ``evidence[field]`` lists containing value,
    start, end and excerpt for *every* supporting source span. ``conflicts``
    retains competing values. Unlabelled capacities are deliberately unknown.
    GPU scope is laptop only with explicit mobile/product context; a desktop
    qualifier overrides that context. Marketing years and screen size do not
    establish RAM, GPU, model year, or any other unstated specification.
    """
    if not isinstance(text, str):
        raise ValueError("Hardware text must be a string")
    obs = {field: [] for field in FIELDS}
    gpu_capacities = []

    def negation_start(start):
        prefix_start = max(0, start - 64)
        match = re.search(
            r"(?:(?<![A-Za-z])(?:no|not|without)|不是|并非|非|无|没有)\s*"
            r"(?:(?:display|screen|resolution|refresh(?:\s+rate)?|size|VRAM|TGP)\s*[:=]?\s*)?$",
            text[prefix_start:start], re.I,
        )
        return prefix_start + match.start() if match else None

    def add(field, value, start, end):
        negative = negation_start(start)
        if negative is not None:
            value, start = None, negative
        record = {"value": value, "start": start, "end": end, "excerpt": text[start:end]}
        if record not in obs[field]:
            obs[field].append(record)

    def negated(start):
        return negation_start(start) is not None

    def unresolved_alternative(field, start, end, unit=""):
        # Keep a literal ambiguity span when an alternative omits the field
        # prefix or unit. Never silently select the fully written operand.
        number = rf"\d+(?:\.\d+)?(?:\s*(?:{unit}))?" if unit else r"\d+[A-Za-z]{0,3}"
        separator = r"(?:/|or|或|-)" if unit else r"(?:/|or|或)"
        before = re.search(rf"{number}\s*{separator}\s*$", text[max(0, start - 24):start], re.I)
        after = re.match(rf"\s*{separator}\s*{number}", text[end:], re.I)
        if before:
            add(field, None, max(0, start - 24) + before.start(), end)
        if after:
            add(field, None, start, end + after.end())

    cpu_patterns = (
        r"(?<![A-Za-z0-9])(?:Intel[®™]?\s+)?(?:Core[®™]?\s+)?i[3579][ -]\d{4,5}[A-Z]{0,3}(?![A-Za-z0-9])",
        r"(?<![A-Za-z0-9])(?:Intel[®™]?\s+)?(?:Core[®™]?\s+)?Ultra\s*[579][ -]+(?:Processor\s+)?\d{3}[A-Z]{1,3}(?![A-Za-z0-9])",
        r"(?<![A-Za-z0-9])(?:AMD[®™]?\s+)?Ryzen[®™]?\s*(?:AI\s*)?[3579]\s+(?:HX\s*)?\d{3,4}[A-Z]{0,3}(?![A-Za-z0-9])",
        r"(?<![A-Za-z0-9])R[3579]-\d{4}[A-Z]{1,3}(?![A-Za-z0-9])",
    )
    for pattern in cpu_patterns:
        for match in _matches(pattern, text):
            if negated(match.start()):
                continue
            value = re.sub(r"[®™]", "", match.group().upper())
            value = re.sub(r"PROCESSOR\s+", "", value)
            value = re.sub(r"^(?:INTEL\s+)?(?:CORE\s+)?", "", value)
            value = re.sub(r"^AMD\s+", "", value)
            value = re.sub(r"I([3579])[ -]+", r"i\1-", value)
            value = re.sub(r"ULTRA\s*([579])[ -]+", r"Core Ultra \1 ", value)
            value = re.sub(r"RYZEN\s*", "Ryzen ", value)
            value = re.sub(r"^R([3579])-", r"Ryzen \1 ", value)
            add("cpu", value, *match.span())
            unresolved_alternative("cpu", *match.span())

    gpu_pattern = r"(?<![A-Za-z0-9])(?:(?:NVIDIA[®™]?\s+)?(?:GeForce[®™]?\s+)?)((?:RTX|GTX)[®™]?\s*\d{3,4}(?:\s*(?:Ti|SUPER))?|(?:AMD[®™]?\s+)?(?:Radeon[®™]?\s+)?RX\s*\d{4}[A-Z]{0,3})(?![A-Za-z0-9])"
    for match in _matches(gpu_pattern, text):
        if negated(match.start()):
            continue
        value = re.sub(r"\s+", " ", re.sub(r"[®™]", "", match[1].upper()))
        value = re.sub(r"^AMD\s+", "", value)
        value = re.sub(r"^(?:RADEON\s+)?RX\s*", "RADEON RX ", value)
        value = re.sub(r"(RTX|GTX)\s*(\d)", r"\1 \2", value)
        value = re.sub(r"(\d)(TI|SUPER)", r"\1 \2", value)
        add("gpu", value, *match.span())
        offset = match.end()
        while value.startswith(("RTX ", "GTX ")):
            shorthand = re.match(r"\s*(?:/|or|或)\s*(\d{3,4}(?:\s*(?:Ti|SUPER))?)\b", text[offset:], re.I)
            if not shorthand:
                break
            alternative = value.split()[0] + " " + re.sub(r"\s+", " ", shorthand[1].upper())
            alternative = re.sub(r"(\d)(TI|SUPER)", r"\1 \2", alternative)
            offset += shorthand.end()
            add("gpu", alternative, match.start(), offset)
        # Scope is evidence-bound, never inferred from a GPU generation number.
        end = text.find("\n", match.end())
        end = len(text) if end < 0 else end
        start = text.rfind("\n", 0, match.start()) + 1
        clause = text[start:end]
        desktop = re.search(r"\bdesktop\b|台式|台机|桌面", clause, re.I)
        mobile = re.search(r"\blaptop\b|\bnotebook\b|\bmobile\b|Zephyrus|笔记本", clause, re.I)
        qualifier = desktop or mobile
        if qualifier:
            add("gpu_variant", "desktop" if desktop else "laptop", start + qualifier.start(),
                start + qualifier.end())
        # A capacity adjacent to a GPU can establish VRAM unless a memory
        # label also claims it. Ambiguous capacities do not become VRAM.
        vram = re.match(r"\s*(?:(?:Laptop|Mobile|desktop)\s*(?:GPU)?\s*)?[,(-]?\s*(\d+)\s*GB\b", text[match.end():], re.I)
        if vram:
            gpu_capacities.append((match.end(), match.end() + vram.end()))
        if vram and not re.match(rf"\s*(?:{_RAM}|{_SSD})\b", text[match.end() + vram.end():], re.I):
            add("vram_gb", int(vram[1]), match.start(), match.end() + vram.end())
            unresolved_alternative("vram_gb", match.start(), match.end() + vram.end(), "GB|G")

    for match in _matches(r"(?<![A-Za-z])(?:VRAM|显存)\s*[:=]?\s*(\d+)\s*(?:GB|G)(?![A-Za-z])|(?<![A-Za-z0-9])(\d+)\s*(?:GB|G)\s*(?:VRAM|显存)", text):
        add("vram_gb", int(match[1] or match[2]), *match.span())
        unresolved_alternative("vram_gb", *match.span(), "GB|G")
    for match in _matches(r"(?<![A-Za-z])(?:TGP|GPU\s*(?:power|功耗))\s*[:=]?\s*(\d+)\s*W(?![A-Za-z])|(?<![A-Za-z0-9])(\d+)\s*W\s*TGP(?![A-Za-z])", text):
        add("gpu_tgp_w", int(match[1] or match[2]), *match.span())
        unresolved_alternative("gpu_tgp_w", *match.span(), "W")

    # Labelled runs support alternatives such as RAM 16GB/32GB. Never guess
    # that 16-inch, G16, GU605, VRAM, or an unlabelled 16GB+1TB is system RAM.
    separator = r"(?:/|or|或|、|-)"
    shared_unit = rf"(?<![\d_.])(?:\d+(?:\.\d+)?\s*{separator}\s*)+{_CAPACITY}"
    runs = list(_matches(rf"(?:{shared_unit}|{_CAPACITY})(?:\s*{separator}\s*{_CAPACITY})*", text))
    labels = list(_matches(rf"(?<![A-Za-z])(?:{_RAM}|{_SSD})(?![A-Za-z])", text))
    assigned = {run.start() for run in runs for record in obs["vram_gb"]
                if record["start"] <= run.start() and run.end() <= record["end"]}
    associations = []
    for label in reversed(labels):
        if negated(label.start()):
            continue
        field = "ram_gb" if re.fullmatch(_RAM, label.group(), re.I) else "ssd_gb"
        left = next((run for run in runs if run.end() <= label.start()
                     and not text[run.end():label.start()].strip() and run.start() not in assigned), None)
        right = next((run for run in runs if run.start() >= label.end()
                      and re.fullmatch(r"\s*[:=]?\s*", text[label.end():run.start()])
                      and run.start() not in assigned), None)
        selected = right or left
        if selected:
            assigned.add(selected.start())
            associations.append((field, label, selected))
    # Preserve a second adjacent, unclaimed size as a competing observation.
    # A size also touching a GPU name is ambiguous VRAM, not extra system RAM.
    for label in labels:
        if negated(label.start()):
            continue
        field = "ram_gb" if re.fullmatch(_RAM, label.group(), re.I) else "ssd_gb"
        for run in runs:
            if run.start() in assigned or any(start <= run.start() and run.end() <= end
                                               for start, end in gpu_capacities):
                continue
            if (run.end() <= label.start() and not text[run.end():label.start()].strip()
                    or run.start() >= label.end()
                    and re.fullmatch(r"\s*[:=]?\s*", text[label.end():run.start()])):
                assigned.add(run.start())
                associations.append((field, label, run))
    for field, label, run in associations:
        capacities = list(_matches(_CAPACITY, run.group()))
        unit = capacities[-1][2] if capacities else None
        for capacity in _matches(r"(?<![\w.])(\d+(?:\.\d+)?)\s*(GB|TB|G|T)?", run.group()):
            size = float(capacity[1]) * (1024 if (capacity[2] or unit).upper().startswith("T") else 1)
            if math.isfinite(size) and size > 0:
                add(field, int(size) if size.is_integer() else size,
                    min(label.start(), run.start()), max(label.end(), run.end()))

    # Only a literal parenthetical equivalence binds a marketing label to
    # pixels. A bare K label never implies dimensions from a lookup table.
    aliases = list(_matches(
        rf"(?<![A-Za-z0-9]){_DISPLAY_LABEL}\s*[(（]\s*({_PIXELS})"
        rf"(?:\s*[,，]\s*{_DISPLAY_LABEL})*\s*[)）]", text,
    ))
    for match in aliases:
        add("display_resolution", re.sub(r"\s+", "", match[1]).replace("×", "x").lower(), *match.span())
    for match in _matches(rf"(?<![A-Za-z0-9])(\d{{3,4}})\s*[x×]\s*(\d{{3,4}})(?!\d)|(?<![A-Za-z0-9])({_DISPLAY_LABEL})(?![A-Za-z0-9])", text):
        if any(alias.start() <= match.start() and match.end() <= alias.end() for alias in aliases):
            continue
        value = f"{match[1]}x{match[2]}" if match[1] else match[3].upper()
        add("display_resolution", value, *match.span())
    for match in _matches(r"(?<![A-Za-z0-9_.])(\d{2,3})\s*Hz(?![A-Za-z])", text):
        add("display_refresh_hz", int(match[1]), *match.span())
        unresolved_alternative("display_refresh_hz", *match.span(), "Hz")
    for match in _matches(r"\bOLED\b|\bIPS\b|\bmini[ -]?LED\b", text):
        if not negated(match.start()):
            add("display_technology", re.sub(r"[ -]", "", match.group().upper()), *match.span())
    for match in _matches(r'(?<![A-Za-z0-9_.])(\d{1,2}(?:\.\d+)?)\s*(?:-?inch(?:es)?\b|["″]|英寸)', text):
        add("display_size_inches", float(match[1]), *match.span())
        unresolved_alternative("display_size_inches", *match.span(), "inch|inches|英寸")

    # Explicit family/chassis names partition comparisons. Chinese discovery
    # names and codes alone are not mapped to an unstated English family.
    for match in _matches(
        r"(?<![A-Za-z])(?P<family>Zephyrus|Strix|Flow|TUF)"
        r"(?:\s+(?:Gaming\s+)?(?P<chassis>Duo(?:\s*1[56])?|[GMSXZFA]1[345678]|[GMS]))?(?![A-Za-z0-9])",
        text,
    ):
        family = match['family'].upper()
        add("product_family", family, *match.span())
        if match['chassis']:
            add("product_chassis", re.sub(r"\s+", " ", match['chassis'].upper()), *match.span())

    # GM501GS is a bounded legacy literal, not a license to infer hardware or
    # accept every GM-prefixed string as a verified chassis grammar.
    for match in _matches(r"(?:(?<![A-Za-z0-9])|(?<=幻14)|(?<=幻15)|(?<=幻16))(?:G[AUWX]\d{3}[A-Z]{0,4}(?:-[A-Z0-9]+)?|GM501(?:GS)?)(?![A-Za-z0-9])", text):
        context = text[max(0, match.start() - 60):match.end() + 60]
        if re.search(_PRODUCT, context, re.I):
            add("model_code", match.group().upper(), *match.span())
    # Years must be adjacent to product identity, not timestamps or copyright.
    for match in _matches(rf"(?:{_PRODUCT})(?:\s+(?:{_PRODUCT}))*\s*[( -]*(20(?:2\d|3\d))(?!\d)|\b(20(?:2\d|3\d))\s*[款 )-]*\s*(?:{_PRODUCT})", text):
        add("model_year", int(match[1] or match[2]), *match.span())
        unresolved_alternative("model_year", *match.span())

    condition_patterns = (
        ("refurbished", r"\brefurbished\b|翻新"),
        ("open_box", r"\bopen[ -]box\b|开箱"),
        ("used", r"\b(?:used|pre[ -]owned|second[ -]hand|bekas|like new)\b|二手|自用|闲置|95新|9成新"),
        ("for_parts", r"\bfor parts\b|\bbroken\b|故障|仅配件"),
        ("new", r"\b(?:brand new|factory sealed|BNIB|new|baru)\b|全新|未拆封"),
    )
    for value, pattern in condition_patterns:
        for match in _matches(pattern, text):
            if negated(match.start()):
                continue
            if value == "new" and (re.search(r"like\s*$", text[max(0, match.start()-5):match.start()], re.I)
                                   or re.match(r"\s+(?:model|generation|design|20\d\d)\b", text[match.end():], re.I)):
                continue
            add("condition", value, *match.span())
    for records in obs.values():
        records.sort(key=lambda record: record["start"])
    return _finish(obs)


def _offer_hardware(offer):
    observations = {field: [] for field in FIELDS}
    sources = [(key, offer.get(key)) for key in ("title", "description", "variant", "condition")]
    hardware = offer.get("hardware")
    # Structured facts need literal supporting evidence as well as a verified
    # flag. Reparse that evidence so arbitrary caller values cannot fill gaps.
    if (isinstance(hardware, dict) and hardware.get("verified") is True
            and isinstance(hardware.get("evidence"), dict)):
        for field, records in hardware.get("evidence", {}).items():
            if field not in FIELDS or not isinstance(records, list):
                continue
            for index, record in enumerate(records):
                if isinstance(record, dict) and isinstance(record.get("excerpt"), str):
                    sources.append((f"hardware.evidence.{field}.{index}", record["excerpt"]))
    for source, text in sources:
        if not isinstance(text, str):
            continue
        parsed = extract_hardware(text)
        for field in FIELDS:
            observations[field].extend(dict(record, source=source) for record in parsed["evidence"][field])
    return _finish(observations)


def _requirements(require):
    if require is None:
        return {}
    allowed = {"min_ram_gb", "min_ssd_gb", "cpu", "gpu", "display_technology", "new_only"}
    if not isinstance(require, dict) or set(require) - allowed:
        raise ValueError("Unsupported hardware requirements")
    for key, value in require.items():
        if key.startswith("min_"):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value < float("inf"):
                raise ValueError(f"{key} must be a positive finite number")
        elif key == "new_only":
            if not isinstance(value, bool):
                raise ValueError("new_only must be boolean")
        elif not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be an exact nonempty string")
    return require


def _check_requirements(hardware, require):
    unknown, failed = [], []
    for key, expected in require.items():
        if key == "new_only" and not expected:
            continue
        field = {"min_ram_gb": "ram_gb", "min_ssd_gb": "ssd_gb", "new_only": "condition"}.get(key, key)
        value = hardware[field]
        if value is None:
            unknown.append(key)
        elif key.startswith("min_"):
            if value < expected:
                failed.append(key)
        elif key == "new_only":
            if value != "new":
                failed.append(key)
        else:
            parsed = extract_hardware(expected)[field]
            target = parsed if parsed is not None else expected
            if str(value).casefold() != str(target).casefold():
                failed.append(key)
    return {"status": "fail" if failed else "unknown" if unknown else "pass", "unknown": unknown, "failed": failed}


def compare_laptops(offers: list[dict], require=None) -> dict:
    """Compare only complete observed configs at exact displayed local prices.

    Returns groups (currency/configuration/candidates/cheapest_candidate_ids),
    incomplete, unranked, filtered, requirement_unknown, and discoveries.
    Candidates retain original offer data plus candidate_id, source_url,
    hardware, requirement_check and reasons. There is no cross-config winner.
    A tie retains every cheapest ID. Unknown scope, VRAM, TGP or display facts
    keep candidates separate. Explicit family/chassis are required; observed
    model codes and years additionally partition groups, without implying SKU
    identity or filling any missing hardware. Multi-display binding is not
    represented by this single-display contract, so those offers stay incomplete.
    ``source_mode`` must explicitly be listing_content/product_detail (also
    listing/detail) for price comparison. Search indexes are discoveries only.
    """
    if not isinstance(offers, list) or any(not isinstance(offer, dict) for offer in offers):
        raise ValueError("Offers must be an array of objects")
    require = _requirements(require)
    result = {
        "schema_version": "1", "comparison_basis": "lowest_observed_displayed_price_per_explicit_product_identity_complete_config_and_currency",
        "groups": [], "incomplete": [], "unranked": [], "filtered": [], "requirement_unknown": [], "discoveries": [],
        "warnings": [
            "No universal best laptop: compare exact observed configurations and currencies separately.",
            "Unknown hardware is not equivalent hardware. GPU names alone do not establish performance or TGP.",
            "Groups share explicit family/chassis and observed identifiers, not verified same-model or selected-SKU identity.",
            "Prices are observations, not confirmed stock, checkout prices or discounts. Observation timestamps are retained.",
            "Freight, tax and forwarding are excluded; Blibli has no assumed China-origin Fansbuy freight route.",
        ],
    }
    groups = {}
    for index, offer in enumerate(offers):
        candidate = copy.deepcopy(offer)
        candidate["candidate_id"] = offer.get("candidate_id") or offer.get("id") or f"candidate-{index + 1}"
        candidate["source_url"] = offer.get("source_url") or offer.get("url")
        hardware = _offer_hardware(offer)
        candidate["hardware"] = hardware
        candidate["requirement_check"] = _check_requirements(hardware, require)
        candidate["reasons"] = []
        mode = offer.get("source_mode")
        if mode not in ("listing_content", "product_detail", "listing", "detail", "guest_product_page", "guest_api"):
            candidate["reasons"].append("search_index_discovery" if mode == "search_index" else "listing_content_unverified")
            result["discoveries"].append(candidate)
            continue
        if offer.get("ranking_exclusions"):
            candidate["reasons"].extend(offer["ranking_exclusions"])
            result["unranked"].append(candidate)
            continue
        # Role and transaction scope apply even to a plain imported array.
        # Reuse independent title/selected-variant checks; a description can be
        # a copied spec sheet, so it cannot override an accessory selection.
        from .products import assess_product
        scope = assess_product(offer, "ASUS ROG Zephyrus")
        if scope["listing_kind"] == "accessory_or_non_product" or scope["price_scope_warnings"]:
            candidate["reasons"].append("possible_deposit_accessory_or_parts")
            candidate["reasons"].extend(scope["price_scope_warnings"])
            candidate["ranking_exclusions"] = ["possible_deposit_accessory_or_parts", *scope["price_scope_warnings"]]
            if scope["price_scope_warnings"]:
                normalized_scope = normalize_offer(offer.get("marketplace"), offer, offer.get("observed_at"))
                candidate["price"] = dict(normalized_scope["price"], amount=None, basis="transaction_amount_unverified")
            result["unranked"].append(candidate)
            continue
        check = candidate["requirement_check"]["status"]
        if check != "pass":
            result["filtered" if check == "fail" else "requirement_unknown"].append(candidate)
            continue
        if hardware["gpu_variant"] == "desktop":
            candidate["reasons"].append("desktop_gpu_not_comparable_to_laptop_gpu")
            result["unranked"].append(candidate)
            continue
        missing = [field for field in COMPARISON_FIELDS if hardware[field] is None]
        product_text = "\n".join(offer[key] for key in ("title", "description", "variant")
                                 if isinstance(offer.get(key), str))
        multi_display = bool(re.search(
            r"\bDuo\b|\b(?:dual|second|secondary)[ -]?(?:screen|display)\b|双屏|副屏|第二屏",
            product_text, re.I,
        ))
        if missing or hardware["conflicts"] or multi_display:
            candidate["reasons"].extend(f"unknown_or_conflicting:{field}" for field in missing)
            if multi_display:
                candidate["reasons"].append("multi_display_binding_unresolved")
            if hardware["conflicts"]:
                candidate["reasons"].append("contradictory_or_alternative_configuration")
            result["incomplete"].append(candidate)
            continue
        # Reapply existing price/URL validation, retaining the original raw
        # price and refusing a normalized amount that disagrees with its raw.
        source = dict(offer, url=candidate["source_url"])
        price = offer.get("price")
        if isinstance(price, dict):
            source["price"] = price.get("raw")
            source["currency"] = price.get("source_currency") or price.get("currency")
            source["price_basis"] = price.get("basis", "displayed")
        try:
            normalized = normalize_offer(source.get("marketplace"), source, source.get("observed_at"))
        except ValueError:
            normalized = None
        from .guest import _item_id, _product_url
        product_url = _product_url(source.get("marketplace"), normalized["url"]) if normalized and normalized["url"] else None
        identity_bound = bool(product_url and (not normalized["item_id"] or _item_id(source["marketplace"], product_url) == normalized["item_id"]))
        if (not normalized or not identity_bound or not normalized["url"] or normalized["url_basis"] != "source_url"
                or normalized["price"]["amount"] is None
                or isinstance(price, dict) and str(price.get("amount")) != normalized["price"]["amount"]):
            candidate["reasons"].append("invalid_or_unverified_exact_price_or_url")
            result["unranked"].append(candidate)
            continue
        if any(signal in normalized["signals"] for signal in ("possible_deposit", "possible_accessory_or_parts")):
            candidate["reasons"].append("possible_deposit_accessory_or_parts")
            result["unranked"].append(candidate)
            continue
        candidate["source_url"] = normalized["url"]
        candidate["price"] = normalized["price"]
        config = {field: hardware[field] for field in COMPARISON_FIELDS}
        identity = {field: hardware[field] for field in _IDENTITY_FIELDS}
        key = (normalized["price"]["currency"], *identity.values(), *config.values())
        if key not in groups:
            groups[key] = {"currency": key[0], "configuration": config,
                           "product_identity": identity, "candidates": []}
        groups[key]["candidates"].append(candidate)
    for group in groups.values():
        group["candidates"].sort(key=lambda item: Decimal(item["price"]["amount"]))
        amount = Decimal(group["candidates"][0]["price"]["amount"])
        group["cheapest_candidate_ids"] = [item["candidate_id"] for item in group["candidates"]
                                            if Decimal(item["price"]["amount"]) == amount]
        result["groups"].append(group)
    return result
