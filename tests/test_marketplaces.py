"""Offline registry and identity regressions using synthetic product records."""

import copy
import json
import unittest

from china_deals import models
from china_deals.marketplaces import (
    ALIASES,
    CHINESE_MARKETPLACES,
    CURRENCIES,
    DISCOVERY_DOMAINS,
    FANSBUY_MARKETPLACES,
    HOSTS,
    ID_FIELDS,
    MARKETPLACES,
    PRODUCT_HOSTS,
    canonical_product_url,
    item_url,
    product_id,
)
from china_deals.models import marketplace_name, normalize_offer
from china_deals.ranking import rank_offers

URLS = {
    "tmall": "https://detail.tmall.com/item.htm?id=123",
    "1688": "https://detail.1688.com/offer/123.html",
    "weidian": "https://weidian.com/item.html?itemID=123",
}


class RegistryTests(unittest.TestCase):
    def test_seven_markets_and_shared_legacy_exports(self):
        self.assertEqual(set(MARKETPLACES), {"taobao", "tmall", "1688", "weidian", "jd", "goofish", "blibli"})
        for name in ("MARKETPLACES", "ALIASES", "CURRENCIES", "HOSTS"):
            self.assertIs(getattr(models, name), globals()[name])
        for mapping in (CURRENCIES, HOSTS, ID_FIELDS, PRODUCT_HOSTS, DISCOVERY_DOMAINS):
            self.assertEqual(set(mapping), set(MARKETPLACES))
        self.assertEqual(set(FANSBUY_MARKETPLACES), {"taobao", "tmall", "1688", "weidian", "jd"})
        self.assertEqual(set(CHINESE_MARKETPLACES), set(MARKETPLACES) - {"blibli"})
        self.assertEqual(CURRENCIES["blibli"], "IDR")
        self.assertTrue(all(CURRENCIES[market] == "CNY" for market in CHINESE_MARKETPLACES))

    def test_explicit_aliases_do_not_conflate_alibaba_and_1688(self):
        for alias, market in (("alibaba1688", "1688"), ("1688.com", "1688"),
                              ("TMALL.COM", "tmall"), ("weidian.com", "weidian"), ("xianyu", "goofish")):
            self.assertEqual(marketplace_name(alias), market)
        for value in ("alibaba.com", "alibaba", "www.alibaba.com", "tmall.com.evil.test"):
            with self.assertRaises(ValueError):
                marketplace_name(value)
        self.assertNotIn("alibaba.com", ALIASES)

    def test_id_field_contracts(self):
        self.assertEqual(ID_FIELDS["tmall"], ID_FIELDS["taobao"])
        self.assertEqual(ID_FIELDS["1688"], ("offerId", "offer_id", "item_id", "id"))
        self.assertEqual(ID_FIELDS["weidian"], ("itemID", "itemId", "item_id"))


class NativeURLTests(unittest.TestCase):
    def assert_rejected(self, market, url):
        self.assertIsNone(canonical_product_url(market, url), url)
        self.assertIsNone(product_id(market, url), url)

    def test_native_routes_tracking_and_construction(self):
        for market, url in URLS.items():
            with self.subTest(market=market):
                separator = "&" if "?" in url else "?"
                self.assertEqual(canonical_product_url(market, url + separator + "spm=synthetic#details"), url)
                self.assertEqual(product_id(market, url), "123")
                self.assertEqual(item_url(market, "123"), url)
                self.assertEqual(item_url(market, 123), url)
                self.assertEqual(canonical_product_url(market, canonical_product_url(market, url)), url)

    def test_duplicate_blank_and_variant_query_ids_rejected(self):
        for market in ("tmall", "weidian"):
            key = "id" if market == "tmall" else "itemID"
            for tail in (f"{key}=123", f"{key}=456", f"{key}=", key, "itemId=123",
                         "item_id=456", "ID=123", "productID=123"):
                with self.subTest(market=market, tail=tail):
                    self.assert_rejected(market, URLS[market] + "&" + tail)
            base = URLS[market].split("?")[0]
            for query in (f"{key}=&{key}=123", f"{key}=123&%{ord(key[0]):02x}{key[1:]}=123",
                          "itemId=123", f"{key}=123;{key}=456"):
                self.assert_rejected(market, base + "?" + query)
        for query in ("offerId=456", "offerId=123", "offer_id=", "item_id=123", "id=456", "ID=123"):
            self.assert_rejected("1688", URLS["1688"] + "?" + query)

    def test_only_ascii_route_ids_and_exact_routes(self):
        for market, url in URLS.items():
            for invalid in ("", "abc", "12-3", "-123", "+123", "12.3", "１２３", "١٢٣", "123/456", "%2f123"):
                with self.subTest(market=market, invalid=invalid):
                    self.assert_rejected(market, url.replace("123", invalid))
            for value in (True, False, None, {}, 12.3, "123 ", " 123", "１２３", "-123"):
                self.assertIsNone(item_url(market, value))
            for suffix in ("/extra", ";extra"):
                parts = url.split("?")
                malformed = parts[0] + suffix + ("?" + parts[1] if len(parts) > 1 else "")
                self.assert_rejected(market, malformed)
        self.assert_rejected("1688", "https://www.1688.com/offer/123.html")
        self.assert_rejected("weidian", "https://weidian.com/item.htm?itemID=123")
        self.assert_rejected("tmall", "https://detail.tmall.com/item.html?id=123")

    def test_foreign_hosts_credentials_ports_backslashes_and_controls(self):
        for market, url in URLS.items():
            host = url.split("/")[2]
            for replacement in (host + ".evil.test", "evil.test", "user@" + host,
                                "user:pass@" + host, "@" + host, host + ":443", host + ":",
                                host + ":bad", host + "\\@evil.test", host + "%2f.evil.test"):
                self.assert_rejected(market, url.replace(host, replacement))
            for invalid in (url.replace("https:", "http:"), " " + url, "\n" + url, url + "\t", None, 123):
                self.assert_rejected(market, invalid)
        self.assert_rejected("1688", "https://detail.alibaba.com/offer/123.html")

    def test_legacy_routes_and_taobao_tmall_acceptance(self):
        old = {
            "taobao": "https://item.taobao.com/item.htm?id=123",
            "jd": "https://item.jd.com/123.html",
            "goofish": "https://www.goofish.com/item?id=123",
            "blibli": "https://www.blibli.com/p/synthetic/ps--SKU-123",
        }
        for market, url in old.items():
            self.assertEqual(canonical_product_url(market, url), url)
            self.assertEqual(product_id(market, url), "SKU-123" if market == "blibli" else "123")
        self.assertIsNone(item_url("blibli", "123"))
        self.assertEqual(canonical_product_url("taobao", URLS["tmall"]), URLS["tmall"])
        self.assertEqual(canonical_product_url("jd", "https://item.m.jd.com/product/123.html"), old["jd"])
        self.assert_rejected("tmall", old["taobao"])
        row = normalize_offer("taobao", {"title": "Synthetic", "url": URLS["tmall"], "price": 200})
        self.assertEqual((row["marketplace"], row["item_id"], row["price"]["amount"]), ("taobao", "123", "200"))


class NewMarketIdentityTests(unittest.TestCase):
    def row(self, market):
        return {"marketplace": market, "title": "Synthetic product", "item_id": "123",
                "url": URLS[market], "price": 200}

    def assert_unpriced_roundtrips(self, market, row):
        original = copy.deepcopy(row)
        result = normalize_offer(market, row)
        raw = copy.deepcopy(result["price"]["raw"])
        evidence = copy.deepcopy(result["identity_evidence"])
        for _ in range(3):
            self.assertIsNone(result["price"]["amount"])
            self.assertTrue(any("identity" in warning or "conflict" in warning for warning in result["warnings"]))
            self.assertEqual(result["price"]["raw"], raw)
            # Re-import may also retain a constructed URL or normalized item_id.
            # Every original conflicting observation must still be present.
            for observation in evidence:
                self.assertIn(observation, result["identity_evidence"])
            ranked = rank_offers([json.loads(json.dumps(result))])
            self.assertFalse(ranked["groups"])
            result = normalize_offer(market, json.loads(json.dumps(ranked["unranked"][0])))
        self.assertIsNone(result["price"]["amount"])
        self.assertEqual(row, original)

    def test_native_urls_derive_ids_and_each_alias_constructs_urls(self):
        for market, url in URLS.items():
            native = normalize_offer(market, {"title": "Synthetic", "url": url, "price": 200})
            self.assertEqual(native["item_id"], "123")
            self.assertEqual(native["url_basis"], "source_url")
            for field in ID_FIELDS[market]:
                row = normalize_offer(market, {"title": "Synthetic", field: "123", "price": 200})
                self.assertEqual(row["url"], url)
                self.assertEqual(row["url_basis"], "constructed_from_source_item_id")
                self.assertEqual(row["price"]["currency"], "CNY")
                self.assertEqual(row["price"]["amount"], "200")
                self.assertTrue(any("still needs confirmation" in warning for warning in row["warnings"]))

    def test_every_alias_conflict_is_retained(self):
        for market in URLS:
            for field in ID_FIELDS[market]:
                self.assert_unpriced_roundtrips(market, dict(self.row(market), **{field: "456"}))

    def test_nested_offer_and_retained_price_identity_conflicts(self):
        for market, url in URLS.items():
            for conflict in ({"url": url.replace("123", "456")}, {"productID": "456"},
                             {ID_FIELDS[market][0]: "456"}):
                offer = {"@type": "Offer", "price": "200.00", "priceCurrency": "CNY", **conflict}
                row = self.row(market)
                row.pop("price")
                self.assert_unpriced_roundtrips(market, dict(row, offers=offer))
                self.assert_unpriced_roundtrips(market, dict(self.row(market), offers=[{"url": url}, offer]))
                self.assert_unpriced_roundtrips(market, dict(row, price={"structured_offer": offer, "note": "retain"}))

    def test_invalid_urls_and_ids_stay_unpriced(self):
        for market, url in URLS.items():
            bad_query = "?offerId=" if market == "1688" else "&" + ("itemID=" if market == "weidian" else "id=")
            for invalid in (url + bad_query, url.replace("123", "１２３"),
                            url.replace("https://", "https://user@")):
                self.assert_unpriced_roundtrips(market, dict(self.row(market), url=invalid))
                self.assert_unpriced_roundtrips(market, dict(self.row(market), offers={"url": invalid, "price": 200}))
            self.assert_unpriced_roundtrips(market, dict(self.row(market), item_id="１２３"))

    def test_matching_offer_currency_and_source_safety_survive_three_roundtrips(self):
        for market, url in URLS.items():
            row = self.row(market)
            row.pop("price")
            row["offers"] = {"@type": "Offer", "url": url, "productID": "123",
                             "price": "200.00", "priceCurrency": "CNY"}
            row["source_warnings"] = ["Synthetic fixture; no stock or checkout verification."]
            for _ in range(3):
                row = normalize_offer(market, json.loads(json.dumps(row)))
                self.assertEqual(row["price"]["amount"], "200.00")
                self.assertEqual(row["source_warnings"], ["Synthetic fixture; no stock or checkout verification."])
                self.assertEqual(row["seller_trust"], "unverified")
                self.assertEqual(row["availability"], "unknown")
            for patch in ({"currency": "IDR"}, {"source_mode": "search_index"}, {"availability": "sold"}):
                candidate = dict(self.row(market), **patch)
                for _ in range(3):
                    candidate = normalize_offer(market, json.loads(json.dumps(candidate)))
                    self.assertIsNone(candidate["price"]["amount"])


if __name__ == "__main__":
    unittest.main()
