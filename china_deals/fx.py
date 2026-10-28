"""Public ECB reference-rate snapshots; all cross-rates share the same source date."""

from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree import ElementTree

from .decimal_math import bounded_decimal, monetary_calculation
from .models import decimal_value

ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"


def _valid_ecb_url(url):
    try:
        parts = urlsplit(url)
        return (parts.scheme == "https" and parts.hostname == "www.ecb.europa.eu"
                and parts.port in (None, 443) and parts.username is None and parts.password is None)
    except ValueError:
        return False


class _ECBRedirects(HTTPRedirectHandler):
    def __init__(self):
        self.count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.count += 1
        if self.count > 5 or not _valid_ecb_url(newurl):
            if fp is not None:
                fp.close()
            raise ValueError("ECB redirect denied")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


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
        "brl_per_unit": {c: format(values["BRL"] / rate, ".12f") for c, rate in
                         {"EUR": Decimal(1), **values}.items()},
        "warnings": ["ECB reference rates are estimates, not Fansbuy payment rates, card rates or customs PTAX.",
                     "Rates exclude conversion spread, payment fees and any IOF; compare provider charges separately."],
    }


def fetch_rates(timeout=15):
    if not _valid_ecb_url(ECB_URL):
        raise ValueError("ECB source URL denied")
    opener = build_opener(_ECBRedirects())
    with opener.open(Request(ECB_URL, headers={"User-Agent": "china-deals/0.2"}), timeout=timeout) as response:
        if not _valid_ecb_url(response.url):
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


@monetary_calculation
def convert_brl(amount, currency, snapshot):
    """Convert within 18 integer and 12 meaningful fractional digits, rounding to cents."""
    validate_snapshot(snapshot)
    rate = Decimal(1) if currency == "BRL" else decimal_value(snapshot["brl_per_unit"].get(currency), "FX rate", positive=True)
    converted = bounded_decimal(decimal_value(amount), 'amount') * bounded_decimal(rate, 'FX rate')
    return str(converted.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def annotate_offers(offers, snapshot, config):
    validate_snapshot(snapshot)
    for item in offers:
        price = item.get("price", {})
        amount = price.get("amount")
        convertible = price.get("currency") == "BRL" or price.get("currency") in snapshot["brl_per_unit"]
        item["brl"] = {
            "product_cost": convert_brl(amount, price["currency"], snapshot) if amount is not None and convertible else None,
            "rate_date": snapshot["rate_date"], "source": snapshot.get("source"),
            "shipping_policy": config["marketplaces"][item["marketplace"]]["shipping"],
            "landed_total": None,
            "scope": "product_only; shipping and tax not added" if config["marketplaces"][item["marketplace"]]["shipping"] != "fansbuy" else "product_only; Fansbuy freight/tax require a parcel and eligible import procedure",
        }
        if amount is not None and not convertible:
            item.setdefault("warnings", []).append("FX snapshot omits the source currency; BRL cost remains unknown.")
        detail = item.get("source_detail")
        observation = (detail.get("price_observation") or detail.get("catalog_observation")) if isinstance(detail, dict) else None
        if isinstance(observation, dict) and observation.get("currency") == price.get("currency"):
            try:
                quoted = decimal_value(observation.get("amount"), "observed amount", positive=True)
                item["brl"]["source_observation_cost"] = convert_brl(quoted, price["currency"], snapshot)
                item["brl"]["source_observation_scope"] = "Unverified source observation only; variant, current stock, freight and taxes unresolved."
            except ValueError:
                pass
    return offers
