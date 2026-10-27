"""Per-market access and logistics preferences. No account or freight assumption is global."""

import copy
import json
import os
from pathlib import Path

from .models import MARKETPLACES

DEFAULT_CONFIG = {
    "schema_version": 1,
    "display_currency": "BRL",
    "marketplaces": {
        "taobao": {"access": "guest", "shipping": "fansbuy", "currency": "CNY"},
        "jd": {"access": "guest", "shipping": "fansbuy", "currency": "CNY"},
        "goofish": {"access": "guest", "shipping": "fansbuy", "currency": "CNY"},
        "blibli": {"access": "guest", "shipping": "excluded", "currency": "IDR"},
    },
}


def config_path():
    if os.environ.get("CHINA_DEALS_CONFIG"):
        return Path(os.environ["CHINA_DEALS_CONFIG"]).expanduser()
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "china-deals/config.json"


def load_config(path=None):
    result = copy.deepcopy(DEFAULT_CONFIG)
    target = Path(path).expanduser() if path else config_path()
    if not target.exists():
        if path:
            raise ValueError(f"Configuration file does not exist: {target}")
        return result
    raw = target.read_bytes()
    if len(raw) > 65536:
        raise ValueError("Configuration exceeds 64 KiB")
    supplied = json.loads(raw)
    if not isinstance(supplied, dict) or set(supplied) - {"schema_version", "display_currency", "marketplaces"}:
        raise ValueError("Configuration contains unknown fields")
    if supplied.get("schema_version", 1) != 1 or supplied.get("display_currency", "BRL") not in {"BRL", "native"}:
        raise ValueError("Configuration needs schema_version 1 and BRL or native display currency")
    markets = supplied.get("marketplaces", {})
    if not isinstance(markets, dict) or set(markets) - set(MARKETPLACES):
        raise ValueError("Unknown marketplace in configuration")
    for market, values in markets.items():
        if not isinstance(values, dict) or set(values) - {"access", "shipping", "currency"}:
            raise ValueError(f"Unknown setting for {market}")
        if values.get("access", "guest") not in {"guest", "native"}:
            raise ValueError("access must be guest or native")
        if values.get("shipping", result["marketplaces"][market]["shipping"]) not in {"fansbuy", "excluded", "manual"}:
            raise ValueError("shipping must be fansbuy, excluded or manual")
        if values.get("currency", result["marketplaces"][market]["currency"]) != result["marketplaces"][market]["currency"]:
            raise ValueError("Marketplace native currency cannot be changed by configuration")
        if values.get("shipping") == "fansbuy" and market == "blibli":
            raise ValueError("Blibli is Indonesia; a China-origin Fansbuy route cannot be assumed")
        result["marketplaces"][market].update(values)
    result["display_currency"] = supplied.get("display_currency", result["display_currency"])
    return result


def write_default_config(path=None):
    target = Path(path).expanduser() if path else config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x") as stream:
        json.dump(DEFAULT_CONFIG, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return {"path": str(target), "config": copy.deepcopy(DEFAULT_CONFIG)}
