"""Offline primary-state contract tests; fixture is a retained public projection."""

import copy
import json
import unittest
from pathlib import Path

from china_deals.blibli_public import parse_product_state
from china_deals.models import normalize_offer

FIXTURE = Path(__file__).parent / "fixtures" / "blibli-primary-state.sanitized.json"
PRODUCT = "HEO-70120-00970"
ITEM = PRODUCT + "-00001"
PRODUCT_URL = f"https://www.blibli.com/p/airpods-max-2024/ps--{PRODUCT}"
ITEM_URL = f"https://www.blibli.com/p/airpods-max-2024/is--{ITEM}"
OBSERVED = "2026-10-27T17:16:19.000+00:00"


def html(state):
    return ("<script>window.__PRODUCT_DETAIL_INITIAL_STATE__ = "
            + json.dumps(state).replace("<", "\\u003c") + ";</script>")


class BlibliPrimaryStateTests(unittest.TestCase):
    def setUp(self):
        self.state = json.loads(FIXTURE.read_text())
        self.summary = self.state["productDetail.product/summary"]
        self.selected = next(option for option in self.summary["options"] if option["selected"])

    def parse(self, url=PRODUCT_URL):
        return parse_product_state(html(self.state), url, OBSERVED)

    def test_retained_summary_normalizes_parent_and_preserves_source_claims(self):
        row = self.parse()
        result = normalize_offer("blibli", row, observed_at=row["observed_at"])
        self.assertEqual(result["item_id"], PRODUCT)
        self.assertEqual(result["url"], PRODUCT_URL)
        self.assertEqual(result["title"], "Airpods Max 2024")
        self.assertEqual(result["description"], "Warna: Midnight")
        self.assertEqual(result["seller"], "Hello Flagship Store")
        self.assertEqual(result["price"]["amount"], "8799000")
        self.assertEqual(result["price"]["currency_basis"], "marketplace_adapter_contract")
        self.assertEqual(row["observed_at"], OBSERVED)
        self.assertEqual(result["variant_evidence"]["itemSku"], ITEM)
        detail = result["source_detail"]
        self.assertEqual(detail["price_claims"], self.summary["price"])
        self.assertTrue(detail["merchant_claims"]["official"])
        self.assertEqual(detail["fulfillment_claims"]["delivery"], "UNAVAILABLE")
        self.assertEqual(detail["native_url"], self.summary["url"])
        self.assertLess(len(json.dumps(detail)), 32768)
        self.assertNotIn("productSku", row)
        self.assertNotIn("historical", detail)

    def test_item_route_keeps_child_identity_and_rankable_price(self):
        selected_url = ITEM_URL + "?pickupPointCode=PP-3460337"
        row = self.parse(selected_url)
        result = normalize_offer("blibli", row, observed_at=OBSERVED)
        self.assertEqual(result["item_id"], ITEM)
        self.assertEqual(result["url"], selected_url)
        self.assertEqual(result["price"]["amount"], "8799000")
        self.assertEqual({entry["value"] for entry in result["identity_evidence"]}, {ITEM, selected_url})

    def test_wrong_request_identity_or_non_native_route_fails(self):
        for url in (PRODUCT_URL + "9", ITEM_URL[:-1] + "2", PRODUCT_URL.replace("ps--", "is--"),
                    ITEM_URL.replace("is--", "ps--"), PRODUCT_URL.replace("www.blibli.com", "evil.test"),
                    PRODUCT_URL + "?pickupPointCode=PP-OTHER", PRODUCT_URL + "?a=1&a=2"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.parse(url)

    def test_conflicting_summary_identity_fails(self):
        for field, value in (("productSku", "OTHER-70120-00970"), ("itemSku", PRODUCT + "-00002"),
                             ("url", ITEM_URL[:-1] + "2")):
            original = self.summary[field]
            self.summary[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.parse()
            self.summary[field] = original
        self.summary["seo"]["canonicalUrl"] = ITEM_URL
        with self.assertRaises(ValueError):
            self.parse()

    def test_selection_must_be_unique_and_exact(self):
        original = copy.deepcopy(self.state)
        mutations = [
            lambda: self.selected.update(selected=False),
            lambda: self.summary["options"][0].update(selected=True),
            lambda: self.selected.update(selected=1),
            lambda: self.selected.update(available="true"),
            lambda: self.selected.update(id=f"is--{PRODUCT}-00002_PP-3460337"),
            lambda: self.selected.update(itemSku=PRODUCT + "-00002"),
            lambda: self.selected.update(productSku="OTHER-70120-00970"),
            lambda: self.selected.update(pickupPointCode="PP-OTHER"),
            lambda: self.selected.update(price={"offered": 1}),
            lambda: self.selected["attributes"][0].update(value="Not a listed color"),
            lambda: self.selected["attributes"].append(copy.deepcopy(self.selected["attributes"][0])),
            lambda: self.summary["options"].append(copy.deepcopy(self.selected)),
        ]
        for index, mutate in enumerate(mutations):
            self.state = copy.deepcopy(original)
            self.summary = self.state["productDetail.product/summary"]
            self.selected = next(option for option in self.summary["options"] if option["selected"])
            mutate()
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.parse()

    def test_unavailable_stock_or_option_suppresses_price(self):
        for stock, available in ((0, True), (1, False), (0, False)):
            self.summary["stock"] = stock
            self.selected["available"] = available
            row = self.parse()
            self.assertEqual(row["availability"], "unavailable")
            self.assertIsNone(row["price"])
            self.assertIsNone(normalize_offer("blibli", row)["price"]["amount"])
            self.assertEqual(row["source_detail"]["price_claims"]["offered"], 8799000)

    def test_ambiguous_range_or_contradictory_prices_are_unpriced(self):
        original = copy.deepcopy(self.summary["price"])
        for price in ({**original, "offered": "100-200"}, {**original, "offered": [100, 200]},
                      {**original, "minPrice": 1}, {**original, "offered": True},
                      {**original, "offered": "Rp 8.799.000"}, {**original, "listed": 1},
                      {**original, "offered": "1e9"}, {**original, "offered": -1},
                      {**original, "offered": "999999999999999.99"},
                      {**original, "offered": 0}, {**original, "offered": "999999999999999999999"}):
            self.summary["price"] = price
            with self.subTest(price=price):
                self.assertIsNone(self.parse()["price"])

    def test_decimal_machine_amount_is_not_thousands_separator(self):
        self.summary["price"] = {"offered": "8799000.25", "listed": "8999000.00"}
        result = normalize_offer("blibli", self.parse())
        self.assertEqual(result["price"]["amount"], "8799000.25")

    def test_explicit_currency_is_validated_at_each_boundary(self):
        for target in (self.summary, self.summary["price"], self.selected):
            for key in ("currency", "priceCurrency"):
                for invalid in ("USD", "CNY", None, 123, ""):
                    target[key] = invalid
                    with self.subTest(key=key, invalid=invalid), self.assertRaises(ValueError):
                        self.parse()
                target[key] = "IDR"
                self.assertEqual(normalize_offer("blibli", self.parse())["price"]["currency_basis"],
                                 "explicit_source_field")
                del target[key]

    def test_duplicate_properties_assignments_and_nonliteral_values_fail(self):
        body = html(self.state)
        bad = [body.replace('"stock": 1', '"stock": 1, "stock": 1'), body + body,
               body + '<script>window["__PRODUCT_DETAIL_INITIAL_STATE__"] = {};</script>',
               body.replace('"stock": 1', '"stock": NaN'),
               body.replace('"stock": 1', '"stock": Infinity'),
               body.replace('"stock": 1', '"stock": 1e999'),
               body.replace('"stock": 1', '"stock": 100000000000000000000000'),
               body.replace('"stock": 1', '"stock": (() => 1)()'),
               body.replace(";</script>", " || {};</script>"),
               body.replace(";</script>", ""),
               body.replace("<script>", "<script>// "),
               body.replace("<script>", '<script type="application/json">'),
               body.replace("<script>", '<script src="https://evil.test/x.js">'),
               body.replace("<script>", "<div>").replace("</script>", "</div>"),
               '<script>window.__PRODUCT_DETAIL_INITIAL_STATE__ = {"a":'
               + '[' * 65 + '0' + ']' * 65 + '};</script>']
        for index, value in enumerate(bad):
            with self.subTest(index=index), self.assertRaises(ValueError):
                parse_product_state(value, PRODUCT_URL, OBSERVED)

    def test_response_and_evidence_bounds(self):
        for body in (html(self.state) + " " * (2 * 1024 * 1024),
                     html(self.state) + "é" * (1024 * 1024), "", None):
            with self.assertRaises(ValueError):
                parse_product_state(body, PRODUCT_URL, OBSERVED)
        self.summary["merchant"]["rating"] = {"untrusted": "x" * 32768}
        with self.assertRaises(ValueError):
            self.parse()

    def test_product_description_safe_text_excludes_unrelated_state(self):
        self.summary["description"] = (
            '<p>USB-C &amp; audio</p><script>malicious()</script><style>secret</style>')
        self.state["productDetail.product/description"] = {
            "productSku": PRODUCT, "itemSku": ITEM,
            "description": "<div>Full product description<br>2024</div>",
            "recommendations": {"description": "unrelated recommendation"}}
        self.state["recommendations"] = {"description": "unrelated recommendation"}
        row = self.parse()
        self.assertIn("USB-C & audio", row["description"])
        self.assertIn("Full product description 2024", row["description"])
        self.assertIn("Midnight", row["description"])
        for excluded in ("malicious", "secret", "unrelated", "<div>"):
            self.assertNotIn(excluded, row["description"])
        self.state["productDetail.product/description"]["itemSku"] = PRODUCT + "-00002"
        with self.assertRaises(ValueError):
            self.parse()

    def test_invalid_stock_is_not_an_available_claim(self):
        for value in (True, -1, "1", None, 0.5):
            self.summary["stock"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.parse()


if __name__ == "__main__":
    unittest.main()
