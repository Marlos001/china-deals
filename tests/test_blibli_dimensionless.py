"""Offline regressions for five retained primary pages and adversarial mutations."""

import copy
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from china_deals import guest
from china_deals.blibli_public import parse_product_state
from china_deals.models import normalize_offer

FIXTURE = Path(__file__).parent / "fixtures" / "blibli-dimensionless.sanitized.json"
CASES = json.loads(FIXTURE.read_text())["cases"]
RETAINED = Path(__file__).resolve().parents[1] / ".local/diverse-search/blibli"


def html(state):
    return ("<script>window.__PRODUCT_DETAIL_INITIAL_STATE__ = "
            + json.dumps(state).replace("<", "\\u003c") + ";</script>")


class BlibliDimensionlessTests(unittest.TestCase):
    def setUp(self):
        self.case = copy.deepcopy(CASES[2])  # Available dimensionless Ryzen.
        self.state = self.case["state"]
        self.summary = self.state["productDetail.product/summary"]
        self.selected = self.summary["options"][0]

    def parse(self, case=None):
        case = case or self.case
        return parse_product_state(html(case["state"]), case["requested_url"], case["observed_at"])

    def assert_case(self, case, row):
        summary = case["state"]["productDetail.product/summary"]
        selected = next(option for option in summary["options"] if option["selected"])
        self.assertEqual(row["price"], case["expected_price"])
        self.assertEqual(row["availability"], "source_claimed_available" if selected["available"] else "unavailable")
        self.assertEqual(row["observed_at"], case["observed_at"])
        self.assertEqual(row["variant_evidence"]["itemSku"], summary["itemSku"])
        self.assertEqual(row["variant_evidence"]["attributes"],
                         {a["name"]: a["value"] for a in selected["attributes"]})
        detail = row["source_detail"]
        self.assertEqual(detail["selected_option"], selected)
        self.assertEqual(detail["stock_claim"], summary["stock"])
        self.assertEqual(detail["price_claims"], summary.get("price"))
        self.assertEqual(detail["price_field_present"], "price" in summary)
        self.assertEqual(detail["fulfillment_claims"], summary["fulfillmentTypes"])
        self.assertEqual(detail["summary_claims"], {k: summary[k] for k in
                         ("campaignInfo", "installment", "preOrder", "tags", "type") if k in summary})
        self.assertEqual(detail["merchant_claims"]["businessOperational"],
                         summary["merchant"]["businessOperational"])
        self.assertEqual(row["location"], summary["merchant"]["location"])
        self.assertEqual(detail["location_basis"], "merchant_location_claim")
        normalized = normalize_offer("blibli", row, row["observed_at"])
        expected = str(case["expected_price"]) if case["expected_price"] is not None else None
        self.assertEqual(normalized["price"]["amount"], expected)
        self.assertEqual(normalized["location"], row["location"])
        self.assertIsNone(normalized["domestic_free_shipping"])
        self.assertNotIn("shipping_destination", row)
        self.assertEqual(normalized["source_detail"]["location_basis"], "merchant_location_claim")

    def test_five_sanitized_primary_pages(self):
        for case in CASES:
            with self.subTest(product=case["name"]):
                self.assert_case(case, self.parse(case))

    @unittest.skipUnless((RETAINED / "network.json").is_file(), "Private retained bodies are not distributed")
    def test_five_retained_bodies_match_both_receipts_and_fixture_hashes(self):
        network = {r["body_file"]: r for r in json.loads((RETAINED / "network.json").read_text())}
        analysis = {r["body_file"]: r for r in json.loads((RETAINED / "analysis.json").read_text())}
        for case in CASES:
            with self.subTest(product=case["name"]):
                receipt = network[case["body_file"]]
                raw = (RETAINED / case["body_file"]).read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                self.assertEqual(digest, case["sha256"])
                self.assertEqual(digest, receipt["sha256"])
                self.assertEqual(digest, analysis[case["body_file"]]["sha256"])
                self.assertEqual(receipt["url"], case["requested_url"])
                self.assert_case(case, parse_product_state(raw.decode(), receipt["url"], receipt["retained_at"]))

    def test_guest_integration_all_five_without_network(self):
        for case in CASES:
            with self.subTest(product=case["name"]), patch(
                    "china_deals.guest._fetch", return_value=(html(case["state"]), case["requested_url"])):
                result = guest.get_guest_item("blibli", case["requested_url"])
                self.assertEqual(result["status"], "ok")
                self.assertEqual(len(result["items"]), 1)
                self.assertEqual(result["items"][0]["price"], case["expected_price"])

    def test_missing_price_with_available_identity_remains_unpriced(self):
        del self.summary["price"]
        row = self.parse()
        self.assertIsNone(row["price"])
        self.assertIsNone(row["original_price"])
        self.assertIsNone(row["discount_percent"])
        self.assertEqual(row["availability"], "source_claimed_available")
        self.assertFalse(row["source_detail"]["price_field_present"])
        self.assertIsNone(normalize_offer("blibli", row)["price"]["amount"])

    def test_empty_attributes_require_single_option(self):
        for available, selected in ((True, False), (False, False), (True, True)):
            sibling = {**self.selected, "id": self.selected["id"].replace("00004", "00005"),
                       "available": available, "selected": selected}
            self.summary["options"] = [self.selected, sibling]
            with self.subTest(available=available, selected=selected), self.assertRaises(ValueError):
                self.parse()

    def test_dimensionless_catalog_must_be_explicitly_empty(self):
        for catalog in (None, {}, "", [{"name": "Size", "values": []}],
                        [{"name": "Size", "values": [{"value": "Box"}]}]):
            self.summary["attributes"] = catalog
            with self.subTest(catalog=catalog), self.assertRaises(ValueError):
                self.parse()
        del self.summary["attributes"]
        with self.assertRaises(ValueError):
            self.parse()

    def test_mixed_or_missing_selected_dimensions_rejected(self):
        for attributes in (None, {}, "", [{"name": "Size", "value": "Box"}]):
            self.selected["attributes"] = attributes
            with self.subTest(attributes=attributes), self.assertRaises(ValueError):
                self.parse()
        del self.selected["attributes"]
        with self.assertRaises(ValueError):
            self.parse()

    def test_dimensionless_selection_conflicts_still_rejected(self):
        original = copy.deepcopy(self.selected)
        for change in ({"selected": False}, {"selected": 1}, {"available": "true"},
                       {"id": original["id"].replace("00004", "00005")},
                       {"itemSku": self.summary["itemSku"] + "9"}, {"productSku": "BAD-1-2"},
                       {"pickupPointCode": "PP-OTHER"},
                       {"url": self.summary["url"].replace("00004", "00005")},
                       {"price": {"offered": 1}}):
            self.selected.clear()
            self.selected.update(original, **change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.parse()

    def test_missing_price_does_not_relax_currency_or_selected_price_binding(self):
        del self.summary["price"]
        for target in (self.summary, self.selected):
            for key in ("currency", "priceCurrency"):
                target[key] = "USD"
                with self.assertRaisesRegex(ValueError, "currency"):
                    self.parse()
                del target[key]
        for price in ({"offered": 1}, {}, None):
            self.selected["price"] = price
            with self.subTest(price=price), self.assertRaises(ValueError):
                self.parse()

    def test_explicit_invalid_price_objects_rejected_even_if_unavailable(self):
        for available in (True, False):
            self.selected["available"] = available
            for price in (None, [], 8905000, "8905000", True):
                self.summary["price"] = price
                with self.subTest(available=available, price=price), self.assertRaises(ValueError):
                    self.parse()

    def test_ambiguous_dimensionless_prices_not_promoted(self):
        for price in ({}, {"offered": "1-2"}, {"offered": True}, {"offered": -1},
                      {"offered": 10, "listed": 1}, {"offered": 10, "minPrice": 1},
                      {"offered": 10, "installment": 1}, {"listed": 100}):
            self.summary["price"] = price
            with self.subTest(price=price):
                self.assertIsNone(self.parse()["price"])

    def test_installment_and_closed_business_do_not_replace_full_price(self):
        row = self.parse()
        self.assertEqual(row["price"], 8905000)
        self.assertEqual(row["availability"], "source_claimed_available")
        self.assertEqual(row["source_detail"]["summary_claims"]["installment"]["startFrom"], 371042)
        self.assertNotIn("transaction_evidence", row)

    def test_optional_location_only_accepts_bounded_nonempty_text(self):
        for value in (None, 123, {}, [], " ", "<script>hidden()</script>", "x" * 1001):
            self.summary["merchant"]["location"] = value
            with self.subTest(value_type=type(value).__name__):
                row = self.parse()
                self.assertNotIn("location", row)
                self.assertNotIn("location_basis", row["source_detail"])

    def test_new_raw_claims_remain_bounded(self):
        for key in ("campaignInfo", "installment", "preOrder", "tags"):
            original = self.summary.get(key)
            self.summary[key] = {"oversized": "x" * 32768}
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "evidence exceeds bound"):
                self.parse()
            if original is None:
                del self.summary[key]
            else:
                self.summary[key] = original


if __name__ == "__main__":
    unittest.main()
