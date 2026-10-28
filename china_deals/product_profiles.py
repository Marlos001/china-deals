"""Bounded, offline relevance profiles; seller wording is not authentication.

Only title and independent selected observations establish identity or listing
role. These profiles intentionally do not interpret descriptions, infer hardware
specs, or assess transaction/price scope. The caller owns transaction warnings.
"""

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal


def _text(value):
    value = re.sub(r"[‐‑‒–—−]", "-", unicodedata.normalize("NFKC", str(value or "")).casefold())
    value = re.sub(r"\b(sony)(?=wh[ -]*1000)", r"\1 ", value)
    value = re.sub(r"\b(rtx|ryzen)(?=\d)", r"\1 ", value)
    value = re.sub(r"\b((?:nintendo\s*)?switch)(?=oled\b|lite\b)", r"\1 ", value)
    return re.sub(r"\b(steam\s*deck)(?=oled\b|lcd\b)", r"\1 ", value)


def _has(pattern, text):
    return re.search(pattern, text, re.I) is not None


# ASCII token boundaries deliberately permit adjacent Chinese words, while
# preventing 5070 from matching 15070 or XM6 from matching XM60/ XM6XL.
_LEFT, _RIGHT = r"(?<![a-z0-9])", r"(?![a-z0-9])"
_CPU = _LEFT + r"([579]\d{3})(?:[ -]*(x3d|xt|x|g|f))?" + _RIGHT
_GPU = _LEFT + r"([2345]0[56789]0)\s*(ti\s*super|ti|super)?" + _RIGHT
_SONY = _LEFT + r"(wh|wf)[ -]*1000[ -]*xm(\d{1,2})" + _RIGHT
_DECK = _LEFT + r"steam\s*deck" + _RIGHT
_MINI = _LEFT + r"mini\s*([2345])(?:\s*(pro|se))?" + _RIGHT
_SWITCH = _LEFT + r"(?:nintendo\s*)?switch(?=\s|[2]|[^a-z0-9]|$)"


@dataclass(frozen=True)
class _Profile:
    identity: str
    chinese_prefix: str
    accessories: tuple


_COMMON = (
    ("case", r"保护壳|保护套|收纳包|便携包|\b(?:case|casing|cover|sarung|tas|pouch|sleeve|hardcase|softcase)\b"),
    ("packaging", r"空盒|包装盒|\bempty\s+box\b|\bdus\s+kosong\b|\bbox\s+only\b"),
    ("screen_protector", r"钢化膜|贴膜|\bscreen\s*(?:protector|guard)\b|\btempered\s*glass\b"),
)
_PROFILES = {
    "steam-deck": _Profile(_DECK, "维尔福", (
        ("dock", r"扩展坞|底座|\bdock(?:ing)?\b"),
        ("charger", r"充电器|电源适配器|\b(?:charger|adaptor|adapter)\b"),
        ("parts", r"摇杆|替换屏|更换电池|\b(?:replacement|pengganti)\s+(?:screen|battery|joystick)\b"),
    )),
    "sony-wh": _Profile(_LEFT + r"(?:sony\s+wh" + _RIGHT + r"|wh[ -]*1000(?:[ -]*xm\d{1,2})?" + _RIGHT + r")",
                        "索尼", (
        ("cushions", r"耳垫|耳罩(?!式)|\bear\s*(?:pads?|cushions?)\b|\bearmuffs?\b|\b(?:bantalan|earpad)\b"),
        ("headband", r"头梁|\bheadband\b|\bbando\b"),
        ("parts", r"充电线|\b(?:charging\s*cable|replacement\s*driver)\b"),
    )),
    "amd-ryzen-cpu": _Profile(_LEFT + r"(?:amd\s+)?ryzen" + _RIGHT + r"|锐龙|"
                             + _LEFT + r"[579]\d{3}[ -]*(?:x3d|xt|x)" + _RIGHT, "锐龙", (
        ("cooler", r"散热器|散热风扇|\b(?:cooler|heatsink|pendingin)\b"),
        ("motherboard", r"主板|\b(?:motherboard|mainboard)\b"),
        ("parts", r"支架|扣具|\b(?:bracket|mounting\s*kit)\b"),
    )),
    "nvidia-rtx-gpu": _Profile(_LEFT + r"(?:nvidia\s+)?(?:geforce\s+)?rtx" + _RIGHT + r"|"
                              + _GPU, "英伟达", (
        ("cooler", r"散热器|水冷头|\b(?:cooler|heatsink|water\s*block|pendingin)\b"),
        ("parts", r"支架|风扇替换|\b(?:bracket|riser|replacement\s*fan)\b"),
    )),
    "dji-mini": _Profile(r"(?:" + _LEFT + r"dji\s*|大疆\s*)mini" + r"(?=\s|[2345]|[^a-z0-9]|$)", "大疆", (
        ("controller", r"遥控器|\b(?:controller|remote|remot)\b"),
        ("battery", r"电池|\b(?:battery|baterai)\b"),
        ("propellers", r"螺旋桨|桨叶|\b(?:propellers?|baling[ -]*baling)\b"),
        ("charger", r"充电器|充电管家|\b(?:charger|charging\s*hub)\b"),
    )),
    "nintendo-switch": _Profile(_SWITCH + r"|任天堂", "任天堂", (
        ("controller", r"手柄|\bjoy[ -]*cons?\b|\b(?:controller|gamepad|stik)\b"),
        ("game", r"游戏卡|卡带|\b(?:game\s*cartridge|game\s*card|cartridge|kaset|game\s+for)\b"),
        ("dock", r"底座|扩展坞|\bdock(?:ing)?\b"),
        ("charger", r"充电器|电源适配器|\b(?:charger|adaptor|adapter)\b"),
    )),
}


# Explicit product lines only: bare brands, colors and packaging are not
# competing identities. Do not reuse numeric family shortcuts here: Radeon
# model numbers, for example, can resemble Ryzen or GeForce model numbers.
_EXPLICIT_IDENTITIES = {
    "steam-deck": _DECK,
    "sony-wh": _PROFILES["sony-wh"].identity,
    "amd-ryzen-cpu": _LEFT + r"(?:amd\s+)?ryzen" + _RIGHT + r"|锐龙",
    "nvidia-rtx-gpu": _LEFT + r"(?:nvidia\s+)?(?:geforce\s+)?rtx" + _RIGHT,
    "dji-mini": _PROFILES["dji-mini"].identity,
    "nintendo-switch": _LEFT + r"nintendo\s*switch" + _RIGHT + r"|任天堂|"
                       + _SWITCH + r"\s*(?:2|oled|lite|original|v[12])" + _RIGHT,
    "sony-wf": _LEFT + r"wf[ -]*1000(?:[ -]*xm\d{1,2})?" + _RIGHT,
    "apple-airpods": _LEFT + r"air\s*pods(?:\s*(?:max|pro))?" + _RIGHT,
    "amd-radeon-gpu": _LEFT + r"radeon" + _RIGHT + r"|"
                      + _LEFT + r"rx\s*[5679]\d{3}(?:\s*(?:xtx|xt|gre))?" + _RIGHT,
    "intel-cpu": _LEFT + r"(?:intel\s+)?core\s*(?:i[3579]|ultra\s*[3579])" + _RIGHT
                 + r"|" + _LEFT + r"intel\s+(?:core|celeron|pentium|xeon)" + _RIGHT,
    "intel-arc-gpu": _LEFT + r"(?:intel\s+)?arc\s*[ab]\d{3}" + _RIGHT,
    "dji-other": _LEFT + r"dji\s*(?:mavic|air|avata|neo|flip)" + _RIGHT
                 + r"|大疆\s*(?:mavic|air|avata|neo|flip)" + _RIGHT,
    "apple-iphone": _LEFT + r"iphone\s*\d{1,2}" + _RIGHT,
    "rog-zephyrus": _LEFT + r"(?:rog\s+)?zephyrus\s*g\d{2}" + _RIGHT,
}


def explicit_identity_families(text):
    """Return a frozenset of literal recognized product-family IDs.

    This includes original/unsupported profile families. Bare brands, generic
    options and numeric model shortcuts do not establish an explicit family.
    The caller decides whether any returned family conflicts with its intent.
    """
    if not isinstance(text, str):
        raise ValueError("Identity text must be text")
    value = _text(text)
    return frozenset(name for name, pattern in _EXPLICIT_IDENTITIES.items()
                     if _has(pattern, value))


def identify_family(query):
    """Return one supported family; mixed-family and unknown intents return None."""
    if not isinstance(query, str):
        raise ValueError("Query must be text")
    value = _text(query)
    families = [family for family, profile in _PROFILES.items() if _has(profile.identity, value)]
    return families[0] if len(families) == 1 else None


def profile_queries(query):
    """Return (Chinese, Blibli) suggestions, retaining the entire original query.

    Unknown intents return two empty lists for the caller's fallback. Neutral
    brand prefixes never turn an accessory request into a whole-device request.
    """
    family = identify_family(query)
    if family is None:
        return [], []
    return [_PROFILES[family].chinese_prefix + " " + query], [query]


_BUNDLE = r"\b(?:with|includes?|including|bonus|free|gratis|bundled\s+with)\b|附赠|赠送|含赠品|包含|附带|配有|含"
_ONLY = r"\b(?:only|saja|aja)\b|单卖|单售|仅售|仅有"
_NON_PRODUCT = (r"维修|修理|模型机|展示模型|高仿|精仿|山寨|复刻|"
                r"\b(?:repairs?|replica|counterfeit|dummy|replika|tiruan|imitasi|servis|reparasi|"
                r"perbaikan|palsu|clone|fake)\b|\bjasa\s+service\b")


def _non_product(value):
    value = re.sub(r"\b(?:no|not a|not)\s+(?:replica|counterfeit|dummy|repairs?)\b|"
                   r"非(?:高仿|精仿|山寨|复刻|模型机)|(?:无|没有|未经|已)维修|维修过", "", value)
    return _has(_NON_PRODUCT, value)


def _bundle_core(value):
    """Keep compatibility wording; trim only an actual bundle delimiter."""
    if not _has(_ONLY, value):
        for match in re.finditer(_BUNDLE, value):
            if match.group() == "with" and _has(r"\bcompatible\s*$", value[:match.start()]):
                continue
            return value[:match.start()]
    return value


def _accessories(value, family):
    core = _bundle_core(value)
    kinds = set()
    for kind, pattern in _COMMON + _PROFILES[family].accessories:
        positive = re.sub(r"(?:\b(?:no|without|tanpa)\s+(?:a\s+)?|不含|无)(?:" + pattern + ")", "", core)
        if _has(pattern, positive):
            kinds.add(kind)
    if family == 'dji-mini':
        controller = _LEFT + r'rc[ -]*(?:n[123]|[23])' + _RIGHT
        if _has(controller, value) and (_has(_ONLY, value) or _has(controller + r'.{0,40}(?:\bfor\b|\buntuk\b|适用|兼容).{0,30}mini', value)):
            kinds.add('controller')
    return kinds


def _negates_requested(value, family, wanted_accessories):
    """Detect direct exclusions, without carrying negation across other items."""
    targets = [_PROFILES[family].identity]
    targets += {
        "amd-ryzen-cpu": [r"\b(?:cpu|processor)\b|处理器|处理芯片"],
        "nvidia-rtx-gpu": [r"\b(?:gpu|graphics\s+card|video\s+card)\b|显卡"],
        "steam-deck": [r"\b(?:console|handheld)\b|掌机"],
        "nintendo-switch": [r"\bconsole\b|游戏机|主机"],
        "dji-mini": [r"\bdrone\b|无人机"],
        "sony-wh": [r"\bheadphones?\b|耳机"],
    }.get(family, [])
    if wanted_accessories:
        targets = [pattern for kind, pattern in _COMMON + _PROFILES[family].accessories
                   if kind in wanted_accessories]
    prefix = r"(?:\b(?:no|not|without|excluding|tanpa|bukan)\s+(?:(?:a|an|the)\s+)?|不含|没有|无|非)\s*"
    return any(_has(prefix + r"(?:" + target + r")", value) for target in targets)


_CAPACITY = _LEFT + r"(\d+(?:\.\d+)?)\s*(gb|tb)" + _RIGHT
_RAM_LABEL = _LEFT + r"(?:ram|memory|(?:lp)?ddr[345]x?)" + _RIGHT + r"|内存"
_STORAGE_LABEL = _LEFT + r"(?:ssd|storage|nvme|emmc)" + _RIGHT + r"|固态(?:硬盘)?|存储"


def _deck_capacities(value):
    """Bind adjacent typed capacity runs; unlabelled Deck sizes mean storage.

    Resolve labels with only one available neighbor first, so both RAM 16GB
    SSD 1TB and 16GB RAM 1TB SSD keep their literal axes. A remaining two-sided
    label uses the suffix convention (16GB RAM 1TB). No units/specs are inferred.
    """
    run_pattern = _CAPACITY + r"(?:\s*(?:/|or|或|、)\s*" + _CAPACITY + r")*"
    runs = list(re.finditer(run_pattern, value))
    labels = list(re.finditer(r"(?:" + _RAM_LABEL + "|" + _STORAGE_LABEL + ")", value))
    assignments = {}
    pending = list(labels)
    while pending:
        candidates = []
        for label in pending:
            adjacent = [index for index, run in enumerate(runs) if index not in assignments and (
                run.end() <= label.start() and not value[run.end():label.start()].strip()
                or run.start() >= label.end()
                and re.fullmatch(r"\s*[:=]?\s*", value[label.end():run.start()]))]
            if adjacent:
                candidates.append((label, adjacent))
        if not candidates:
            break
        label, adjacent = next((item for item in candidates if len(item[1]) == 1), candidates[0])
        assignments[adjacent[0]] = "ram_capacity" if _has(_RAM_LABEL, label.group()) else "capacity"
        pending.remove(label)
    facts = {"capacity": set(), "ram_capacity": set()}
    for index, run in enumerate(runs):
        for number, unit in re.findall(_CAPACITY, run.group()):
            facts[assignments.get(index, "capacity")].add(Decimal(number) * (1024 if unit == "tb" else 1))
    return facts


def _model_tuples(value, family, selected=False):
    """Keep a suffix attached to the model that actually advertised it."""
    if family == "amd-ryzen-cpu":
        return set(re.findall(_CPU, value))
    if family == "dji-mini":
        models = set(re.findall(_MINI, re.sub(r"\bdji(?=mini)", "dji ", value)))
        if selected:
            models.update(re.findall(_LEFT + r"([2345])\s*(pro|se)" + _RIGHT, value))
        return models
    return set()


def _facts(value, family, selected=False):
    """Literal axes, never a catalog lookup or inferred configuration."""
    facts = {}

    def add(axis, values):
        facts[axis] = set(values)

    add("capacity", (Decimal(number) * (1024 if unit == "tb" else 1)
                     for number, unit in re.findall(_CAPACITY, value)))
    if family == "steam-deck":
        facts.update(_deck_capacities(value))
        add("revision", re.findall(_LEFT + r"(oled|lcd)" + _RIGHT, value))
    elif family == "sony-wh":
        models = re.findall(_SONY, value)
        add("series", (series for series, _ in models))
        add("model", (number for _, number in models))
        if selected:
            facts["model"].update(re.findall(_LEFT + r"xm(\d{1,2})" + _RIGHT, value))
    elif family == "amd-ryzen-cpu":
        models = _model_tuples(value, family, selected)
        add("model", (number for number, _ in models))
        add("revision", (suffix for _, suffix in models if suffix))
        packages = set()
        if _has(r'\bbox(?:ed)?\b|盒装', value):
            packages.add('boxed')
        if _has(r'\btray\b|散片|散装', value):
            packages.add('tray')
        add('package', packages)
        if selected:
            facts["revision"].update(re.findall(_LEFT + r"(x3d|xt|x|g|f)" + _RIGHT, value))
    elif family == "nvidia-rtx-gpu":
        # Insert only a separator after a known family prefix; never compact all
        # tokens, which would merge model numbers with capacities or years.
        models = re.findall(_GPU, re.sub(r"\brtx(?=\d)", "rtx ", value))
        add("model", (number + re.sub(r"\s+", "", suffix) for number, suffix in models))
        add("revision", (re.sub(r"\s+", "", suffix) or "base" for _, suffix in models))
        if selected and not models:
            facts["revision"].update(re.sub(r"\s+", "", suffix) for suffix in re.findall(
                _LEFT + r"(ti\s*super|ti|super)" + _RIGHT, value))
    elif family == "dji-mini":
        models = _model_tuples(value, family, selected)
        add("model", (number for number, _ in models))
        add("revision", (suffix for _, suffix in models if suffix))
        add('controller_model', (re.sub(r'[ -]+', '', model) for model in re.findall(_LEFT + r'(rc[ -]*(?:n[123]|[23]))' + _RIGHT, value)))
        bundle = set()
        if _has(r'\bfly\s*more\b|畅飞', value):
            bundle.add('fly_more_plus' if _has(r'\bplus\b|长续航', value) else 'fly_more')
        if _has(r'\bstandard\b|标准套装', value):
            bundle.add('standard')
        add('bundle', bundle)
        if selected:
            facts["revision"].update(re.findall(_LEFT + r"(pro|se)" + _RIGHT, value))
    elif family == "nintendo-switch":
        revisions = set()
        for revision, pattern in (
            ("2", r"switch\s*2" + _RIGHT),
            ("oled", _LEFT + r"oled" + _RIGHT),
            ("lite", _LEFT + r"lite" + _RIGHT),
            ("original", r"初代|续航版|switch\s*1" + _RIGHT + r"|"
             + _LEFT + r"(?:original|v[12]|first\s*gen)" + _RIGHT),
        ):
            if _has(pattern, value):
                revisions.add(revision)
        if selected and re.fullmatch(r"2(?:\s+(?:black|white|黑色|白色))?", value.strip()):
            revisions.add("2")
        add("revision", revisions)
    return facts


def _computer_role(value):
    if _has(r"笔记本|移动版|\b(?:laptop|notebook|mobile|laptop\s*gpu)\b", value):
        return "laptop"
    if _has(r"整机|台式主机|电脑主机|\b(?:complete\s*(?:pc|computer)|gaming\s*(?:pc|computer)|"
            r"desktop\s*(?:pc|computer)|pc\s*(?:rakitan|gaming)|prebuilt)\b", value):
        return "complete_pc"
    if _has(r"桌面版|独立显卡|显卡|\b(?:desktop|standalone|graphics\s*card|kartu\s*grafis)\b", value):
        return "component"
    return None


def assess_profile(offer, query, *, selected_observations=None):
    """Assess supported intent conservatively using title and selected variant.

    Generic options may inherit title identity. Explicit conflicting fields fail
    independently; a multi-model title needs an unambiguous compatible selection.
    ``selected_observations`` optionally replaces ``offer['variant']`` with a
    caller-preserved sequence of independent text observations. Role and family
    checks run separately on each observation; selected facts are then unioned
    per axis, so a generic color cannot veto a model selection. Never concatenate
    observations: a bundle delimiter in one must not hide another's accessory.
    The caller owns extracting/preserving structured evidence and price scope.
    A match says nothing about authenticity, performance, or purchasable price.
    """
    family = identify_family(query)
    result = {"family": family, "status": "uncertain", "listing_kind": "unknown", "reasons": [],
              "match_basis": "title_and_selected_variant", "price_scope_warnings": []}

    def finish(status, reason, kind="unknown"):
        result.update(status=status, listing_kind=kind)
        result["reasons"].append(reason)
        return result

    if family is None:
        return finish("uncertain", "unsupported_product_intent")
    query_text = _text(query)
    if selected_observations is None:
        selected_observations = [offer.get("variant")]
    else:
        if isinstance(selected_observations, str):
            raise ValueError("Selected observations must be a sequence of text values")
        selected_observations = list(selected_observations)
        if any(not isinstance(value, str) for value in selected_observations):
            raise ValueError("Selected observations must be a sequence of text values")
    fields = [("title", _text(offer.get("title")))] + [
        ("selected_variant", _text(value)) for value in selected_observations
    ]
    wanted_accessories = _accessories(query_text, family)
    observed_accessories = []
    for source, value in fields:
        if _negates_requested(value, family, wanted_accessories):
            return finish("mismatch", f"{source}: requested_product_explicitly_excluded", "other_product")
        explicit_families = explicit_identity_families(value)
        if explicit_families - {family}:
            return finish("mismatch", f"{source}: different_explicit_product_family", "other_product")
        if _non_product(value):
            return finish("mismatch", f"{source}: explicit_non_product_or_replica_wording", "accessory_or_non_product")
        accessories = _accessories(value, family)
        observed_accessories.append(accessories)
        if accessories and (not wanted_accessories or not accessories <= wanted_accessories):
            return finish("mismatch", f"{source}: different_accessory_or_product_role", "accessory_or_non_product")
        if family in {"nvidia-rtx-gpu", "amd-ryzen-cpu"}:
            wanted_role = _computer_role(query_text) or "component"
            observed_role = _computer_role(value)
            if observed_role and observed_role != wanted_role:
                return finish("mismatch", f"{source}: different_computer_or_component_role", "other_product")

    wanted = _facts(query_text, family)
    observations = [_facts(value, family, source == "selected_variant") for source, value in fields]
    title_facts = observations[0]
    selected_facts = {}
    for facts in observations[1:]:
        for axis, values in facts.items():
            selected_facts.setdefault(axis, set()).update(values)
    pending = []
    wanted_tuples = _model_tuples(query_text, family)
    if len(wanted_tuples) == 1 and all(suffix for _, suffix in wanted_tuples):
        for source, value in fields:
            actual_tuples = _model_tuples(value, family, source == "selected_variant")
            if not actual_tuples or actual_tuples & wanted_tuples:
                continue
            # A single partial model can be completed by a separate selected
            # revision field. Multiple advertised models cannot borrow suffixes
            # from each other; a partial matching alternative stays unresolved.
            if len(actual_tuples) == 1 and not next(iter(actual_tuples))[1]:
                continue
            if any((model, "") in actual_tuples for model, _ in wanted_tuples):
                pending.append(f"{source}: requested_model_revision_not_established")
            else:
                return finish("mismatch", f"{source}: different_explicit_model_revision", "other_product")
    if family in {"nvidia-rtx-gpu", "amd-ryzen-cpu"}:
        wanted_role = _computer_role(query_text)
        if wanted_role and not any(_computer_role(value) == wanted_role for _, value in fields):
            pending.append("requested_computer_or_component_role_not_established")
    for axis, required in wanted.items():
        if not required:
            continue
        if len(required) > 1:
            pending.append(f"ambiguous_requested_{axis}")
        for (source, _), observed in zip(fields, observations):
            actual = observed.get(axis, set())
            if actual and actual.isdisjoint(required):
                return finish("mismatch", f"{source}: different_explicit_{axis}", "other_product")
        actual = selected_facts.get(axis) or title_facts.get(axis, set())
        if actual != required:
            pending.append(f"requested_{axis}_not_established_for_selected_variant")

    # Selecting a partial model must not silently inherit a missing suffix from
    # the title (Mini 4 is not evidence of Mini 4 Pro; 9800 is not 9800X3D).
    if family in {"amd-ryzen-cpu", "dji-mini"} and selected_facts.get("model"):
        if wanted.get("revision") and not selected_facts.get("revision"):
            pending.append("selected_variant: requested_revision_not_established")
    identity = any(_has(_PROFILES[family].identity, value) for _, value in fields)
    # Sony WF is an explicit incompatible family even when WH is generic.
    if family == "sony-wh" and any("wf" in facts.get("series", set()) for facts in observations):
        return finish("mismatch", "different_explicit_headphone_series", "other_product")
    if not identity:
        pending.append("requested_product_not_established_in_title_or_selected_variant")
    if wanted_accessories and not wanted_accessories <= set().union(*observed_accessories):
        pending.append("requested_accessory_scope_not_established")
    if pending:
        result["reasons"].extend(pending)
        return result
    return finish("match", "requested_product_named", "accessory" if wanted_accessories else "product")
