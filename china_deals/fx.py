"""Public ECB reference-rate snapshots; all cross-rates share the same source date."""

from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from .models import decimal_value

ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


def parse_ecb(raw):
    if len(raw) > 262144 or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("Invalid or oversized ECB XML")
    try:
        root = ElementTree.fromstring(raw)
        dated = [node for node in root.iter() if "time" in node.attrib]
        if len(dated) != 1:
            raise ValueError
        rate_date = date.fromisoformat(dated[0].attrib["time"])
        values = {}
        for node in dated[0].iter():
            currency = node.attrib.get("currency")
            if currency:
                if currency in values:
                    raise ValueError
                values[currency] = decimal_value(node.attrib.get("rate"), "FX rate", positive=True)
        if not {"BRL", "CNY", "IDR", "USD"} <= set(values):
            raise ValueError
    except (ElementTree.ParseError, KeyError, ValueError):
        raise ValueError("ECB response omitted an unambiguous dated BRL/CNY/IDR/USD rate set") from None
    return {
        "source": ECB_URL, "rate_date": rate_date.isoformat(), "base": "BRL",
        "brl_per_unit": {c: format(values["BRL"] / values[c], ".12f") for c in ("CNY", "IDR", "USD")},
        "warnings": ["ECB reference rates are estimates, not Fansbuy payment rates, card rates or customs PTAX.",
                     "Rates exclude conversion spread, payment fees and any IOF; compare provider charges separately."],
    }


def fetch_rates(timeout=15):
    with urlopen(Request(ECB_URL, headers={"User-Agent": "china-deals/0.2"}), timeout=timeout) as response:
        if urlsplit(response.url).hostname != "www.ecb.europa.eu":
            raise ValueError("ECB request redirected outside its source host")
        raw = response.read(262145)
    result = parse_ecb(raw)
    result["retrieved_at"] = datetime.now(timezone.utc).isoformat()
    return result


def validate_snapshot(snapshot):
    if not isinstance(snapshot, dict) or snapshot.get("base") != "BRL":
        raise ValueError("FX snapshot needs base BRL")
    date.fromisoformat(snapshot.get("rate_date", ""))
    rates = snapshot.get("brl_per_unit")
    if not isinstance(rates, dict) or not {"CNY", "IDR", "USD"} <= set(rates):
        raise ValueError("FX snapshot needs CNY, IDR and USD in brl_per_unit")
    for value in rates.values():
        decimal_value(value, "FX rate", positive=True)
    return snapshot


def convert_brl(amount, currency, snapshot):
    validate_snapshot(snapshot)
    rate = Decimal(1) if currency == "BRL" else decimal_value(snapshot["brl_per_unit"].get(currency), "FX rate", positive=True)
    converted = decimal_value(amount) * rate
    return str(converted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def annotate_offers(offers, snapshot, config):
    validate_snapshot(snapshot)
    for item in offers:
        price = item.get("price", {})
        amount = price.get("amount")
        item["brl"] = {
            "product_cost": convert_brl(amount, price["currency"], snapshot) if amount is not None else None,
            "rate_date": snapshot["rate_date"], "source": snapshot.get("source"),
            "shipping_policy": config["marketplaces"][item["marketplace"]]["shipping"],
            "landed_total": None,
            "scope": "product_only; shipping and tax not added" if item["marketplace"] == "blibli" else "product_only; Fansbuy freight/tax require a parcel and eligible import procedure",
        }
    return offers
