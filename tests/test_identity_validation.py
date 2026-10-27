"""Offline source identity and warning regressions; every listing is synthetic."""

import copy
import json
import unittest

from china_deals.models import normalize_offer
from china_deals.ranking import rank_offers

URLS = {
    "jd": "https://item.jd.com/{}.html",
    "taobao": "https://item.taobao.com/item.htm?id={}",
    "goofish": "https://www.goofish.com/item?id={}",
    "blibli": "https://www.blibli.com/p/synthetic/ps--{}",
}


class IdentityValidationTests(unittest.TestCase):
    def row(self, market="jd"):
        return {"marketplace": market, "title": "Synthetic product", "item_id": "123",
                "url": URLS[market].format("123"), "price": 200}

    def assert_unpriced_roundtrip(self, row):
        normalized = normalize_offer(row["marketplace"], row)
        self.assertIsNone(normalized["price"]["amount"])
        self.assertTrue(any("identity" in w.lower() or "conflict" in w.lower()
                            for w in normalized["warnings"]))
        for source in (row, normalized, normalize_offer(row["marketplace"], normalized)):
            ranked = rank_offers([json.loads(json.dumps(source))])
            self.assertFalse(ranked["groups"])
            self.assertIsNone(ranked["unranked"][0]["price"]["amount"])
            self.assertEqual(ranked["unranked"][0]["price"]["raw"], normalized["price"]["raw"])
        return normalized

    def test_jd_mobile_outer_conflict(self):
        row = dict(self.row(), url="https://item.m.jd.com/product/456.html")
        result = self.assert_unpriced_roundtrip(row)
        self.assertEqual(result["price"]["raw"], 200)

    def test_nested_offer_url_and_product_id_conflicts_all_markets(self):
        for market, template in URLS.items():
            for field, value in (("url", template.format("456")), ("productID", "456")):
                with self.subTest(market=market, field=field):
                    row = self.row(market)
                    del row["price"]
                    row["offers"] = {"@type": "Offer", "price": "200.00", field: value,
                                     "priceCurrency": "IDR" if market == "blibli" else "CNY"}
                    result = self.assert_unpriced_roundtrip(row)
                    self.assertEqual(result["price"]["raw"], {"structured_offer": row["offers"]})

    def test_all_outer_identity_aliases_are_checked_and_retained(self):
        for market, field in (("jd", "sku"), ("jd", "skuId"), ("taobao", "num_iid"),
                              ("goofish", "itemId"), ("blibli", "productSku")):
            with self.subTest(market=market, field=field):
                self.assert_unpriced_roundtrip(dict(self.row(market), **{field: "456"}))
        for market, template in URLS.items():
            for field, value in (("productID", "456"), ("productUrl", template.format("456")),
                                 ("link", template.format("456"))):
                with self.subTest(market=market, field=field):
                    self.assert_unpriced_roundtrip(dict(self.row(market), **{field: value}))

    def test_nested_identity_is_checked_even_with_outer_price(self):
        row = dict(self.row(), offers={"url": URLS["jd"].format("456"), "price": 300})
        result = self.assert_unpriced_roundtrip(row)
        self.assertEqual(result["price"]["raw"], 200)
        self.assertEqual(result["offers"], row["offers"])

    def test_all_offers_are_checked_including_lists_and_retained_structured_offer(self):
        for offers in ([{"url": URLS["jd"].format("123")}, {"productID": "456"}],
                       [{"productID": "456"}]):
            self.assert_unpriced_roundtrip(dict(self.row(), offers=offers))
        self.assert_unpriced_roundtrip(dict(self.row(), price={
            "structured_offer": {"price": 200, "productID": "456"}}))

    def test_exact_raw_wrapper_is_preserved(self):
        raw = {"structured_offer": {"price": "200.00", "productID": "456"},
               "priceDisplay": "200", "source_note": "Synthetic source evidence"}
        result = self.assert_unpriced_roundtrip(dict(self.row(), price=raw))
        self.assertEqual(result["price"]["raw"], raw)

    def test_matching_controls_and_roundtrip(self):
        for market, template in URLS.items():
            with self.subTest(market=market):
                row = self.row(market)
                del row["price"]
                row["offers"] = {"@type": "Offer", "productID": "123", "url": template.format("123"),
                                 "price": "200.00", "priceCurrency": "IDR" if market == "blibli" else "CNY"}
                original = copy.deepcopy(row)
                normalized = normalize_offer(market, row)
                for source in (row, normalized, normalize_offer(market, normalized)):
                    result = rank_offers([source])
                    self.assertEqual(result["groups"][normalized["price"]["currency"]][0]["price"]["amount"], "200.00")
                self.assertEqual(row, original)
        mobile = normalize_offer("jd", dict(self.row(), url="https://item.m.jd.com/product/123.html"))
        self.assertEqual(mobile["price"]["amount"], "200")

    def test_unknown_opaque_jd_url_never_becomes_numeric_sku(self):
        row = dict(self.row(), item_id=None, url="https://item.jd.com/product/6QDM9CaD9ZAa0SxjEPbKrg.html")
        for source in (row, normalize_offer("jd", row)):
            result = normalize_offer("jd", source)
            self.assertIsNone(result["item_id"])
            self.assertEqual(result["url"], row["url"])

    def test_unknown_query_ids_are_not_inferred_as_item_ids(self):
        for market in ("taobao", "goofish"):
            row = dict(self.row(market), item_id=None, url=URLS[market].format("opaque123"))
            self.assertIsNone(normalize_offer(market, row)["item_id"])

    def test_native_route_controls_derive_only_numeric_ids(self):
        for market, url in (("jd", "https://item.m.jd.com/product/123.html"),
                            ("taobao", "https://detail.tmall.com/item.htm?id=123")):
            row = dict(self.row(market), item_id=None, url=url)
            result = normalize_offer(market, row)
            self.assertEqual(result["item_id"], "123")
            self.assertEqual(result["price"]["amount"], "200")

    def test_unsafe_nested_urls_cannot_supply_a_price(self):
        for url in ("https://item.jd.com.evil.test/123.html", "http://item.jd.com/123.html",
                    "https://user@item.jd.com/123.html", "https://item.jd.com:443/123.html",
                    "https://item.jd.com\\@evil.test/123.html", "https://item.taobao.com/item.htm?id=123"):
            with self.subTest(url=url):
                self.assert_unpriced_roundtrip(dict(self.row(), offers={"url": url, "price": 200}))

    def test_duplicate_query_ids_are_all_validated(self):
        for market in ("taobao", "goofish"):
            self.assert_unpriced_roundtrip(dict(self.row(market), url=URLS[market].format("123") + "&id=456"))


class SourceWarningTests(unittest.TestCase):
    def test_unranked_discovery_warnings_survive_json_import(self):
        row = dict(IdentityValidationTests().row(), source_mode="search_index",
                   warnings=["Guest detail was unavailable; synthetic challenge."])
        expected = row["warnings"][:]
        for _ in range(3):
            row = rank_offers([json.loads(json.dumps(row))])["unranked"][0]
            self.assertEqual(row["source_warnings"], expected)
            self.assertIsNone(row["price"]["amount"])

    def test_source_warnings_survive_normalization_and_ranking_without_growth(self):
        row = IdentityValidationTests().row()
        row["warnings"] = ["Guest detail was unavailable.", "Synthetic challenge."]
        expected = row["warnings"][:]
        for _ in range(3):
            row = normalize_offer("jd", row)
            self.assertEqual(row["source_warnings"], expected)
            row = rank_offers([row])["groups"]["CNY"][0]
            self.assertEqual(row["source_warnings"], expected)

    def test_explicit_source_warnings_take_precedence_even_when_empty_or_invalid(self):
        for value, expected in (([], []), (["Hydration failed."], ["Hydration failed."]), (None, [])):
            row = dict(IdentityValidationTests().row(), source_warnings=value, warnings=["Do not copy"])
            self.assertEqual(normalize_offer("jd", row)["source_warnings"], expected)

    def test_source_warning_bounds_and_string_filter(self):
        row = dict(IdentityValidationTests().row(), warnings=[None, 1, {}, True] + ["x" * 600] * 25)
        result = normalize_offer("jd", row)
        self.assertEqual(result["source_warnings"], ["x" * 500] * 20)
        for value in ("not a list", {}, 123):
            self.assertEqual(normalize_offer("jd", dict(row, warnings=value))["source_warnings"], [])


if __name__ == "__main__":
    unittest.main()
