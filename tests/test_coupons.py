import copy
import json
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from china_deals.coupons import annotate_offers, evaluate_coupons

AS_OF = "2026-10-27T12:00:00Z"


def offer(**updates):
    result = {"marketplace": "blibli", "item_id": "sku-1", "seller": "shop-1",
              "url": "https://www.blibli.com/p/synthetic/ps--sku-1",
              "price": {"amount": "50000000", "currency": "IDR", "raw": "listing-discounted"}}
    result.update(updates)
    return result


def campaign(**updates):
    result = {"id": "synthetic", "marketplace": "blibli", "currency": "IDR",
              "discount": {"percent": "10"}, "cap": "75000", "confirmed": True,
              "eligibility": "confirmed", "source_url": "https://example.invalid/synthetic-coupon",
              "observed_at": "2026-10-27T11:00:00Z"}
    result.update(updates)
    return result


def evaluate(rules=None, item=None, context=None, as_of=AS_OF):
    return evaluate_coupons(offer() if item is None else item,
                            [campaign()] if rules is None else rules, context, as_of)


class CouponTests(unittest.TestCase):
    def test_product_restricted_coupon_requires_url_identity(self):
        rule = campaign(product_ids=['sku-1'])
        valid = evaluate([rule])
        self.assertEqual(valid['campaigns'][0]['status'], 'eligible')
        mismatch = evaluate([rule], offer(url='https://www.blibli.com/p/synthetic/ps--OTHER-456'))
        self.assertEqual(mismatch['campaigns'][0]['status'], 'ineligible')
        missing = evaluate([rule], offer(url=None))
        self.assertEqual(missing['campaigns'][0]['status'], 'potential')
        self.assertIn('product_url_identity', missing['campaigns'][0]['missing_facts'])

    def test_capped_percent_on_50_million_is_only_75_thousand(self):
        result = evaluate()
        best = result["best_eligible"][0]
        self.assertEqual(best["discount_amount"], "75000")
        self.assertEqual(best["amount_due"], "49925000")
        self.assertEqual(best["cashback"], "0")
        self.assertEqual(result["evidence_basis"], "caller_assertions")
        self.assertFalse(result["independently_verified"])
        self.assertFalse(result["used_cart_checkout"])
        json.dumps(result, allow_nan=False)

    def test_listing_discount_never_subtracted_again_and_inputs_preserved(self):
        item = offer(price={"amount": "900", "currency": "CNY", "list_price": "1000"},
                     marketplace="taobao", item_id="1")
        rule = campaign(currency="CNY", marketplace="taobao", discount={"amount": "50"})
        before = copy.deepcopy((item, rule))
        result = evaluate([rule], item)
        self.assertEqual(result["best_eligible"][0]["amount_due"], "850.00")
        self.assertEqual((item, rule), before)

    def test_unknown_payment_is_potential_and_wrong_payment_fails(self):
        rule = campaign(requires={"payment_method": "bank-a", "app": True})
        result = evaluate([rule], context={"app": True})
        self.assertIsNone(result["best_eligible"])
        self.assertEqual(result["best_potential"][0]["missing_facts"], ["requires.payment_method"])
        result = evaluate([rule], context={"app": True, "payment_method": "bank-b"})
        self.assertEqual(result["campaigns"][0]["status"], "ineligible")

    def test_buyer_bound_coupon_is_not_transferable_or_inferred(self):
        rule = campaign(currency="CNY", marketplace="taobao", requires={"buyer_account": "fansbuy"})
        item = offer(marketplace="taobao", price={"amount": "1000", "currency": "CNY"})
        self.assertEqual(evaluate([rule], item)["campaigns"][0]["status"], "potential")
        self.assertEqual(evaluate([rule], item, {"buyer_account": "personal"})["campaigns"][0]["status"],
                         "ineligible")
        self.assertEqual(evaluate([rule], item, {"buyer_account": "fansbuy"})["campaigns"][0]["status"],
                         "eligible")

    def test_account_holder_member_and_new_customer_require_exact_context(self):
        rule = campaign(requires={"account_holder": "alice", "member": True, "new_customer": False})
        self.assertEqual(evaluate([rule], context={"account_holder": "bob", "member": True,
                                                   "new_customer": False})["campaigns"][0]["status"],
                         "ineligible")
        self.assertEqual(evaluate([rule], context={"account_holder": "alice", "member": 1,
                                                   "new_customer": False})["campaigns"][0]["status"],
                         "ineligible")
        self.assertEqual(evaluate([rule], context={"account_holder": "alice", "member": True,
                                                   "new_customer": False})["campaigns"][0]["status"],
                         "eligible")

    def test_wrong_product_currency_and_seller_fail(self):
        for updates, reason in [({"product_ids": ["sku-2"]}, "product_ids"),
                                ({"currency": "CNY"}, "currency"),
                                ({"seller": "shop-2"}, "seller")]:
            with self.subTest(updates=updates):
                result = evaluate([campaign(**updates)])
                self.assertIn(reason, result["campaigns"][0]["reasons"])
                self.assertIsNone(result["best_eligible"])
                self.assertIsNone(result["best_potential"])

    def test_product_identity_needs_marketplace_and_does_not_cross_markets(self):
        rule = campaign(product_ids=["sku-1"], marketplace="taobao")
        result = evaluate([rule])["campaigns"][0]
        self.assertEqual(result["status"], "ineligible")
        self.assertIn({"name": "product_ids", "status": "unknown"}, result["constraints"])
        rule.pop("marketplace")
        with self.assertRaises(ValueError):
            evaluate([rule])

    def test_missing_product_and_seller_remain_unknown(self):
        result = evaluate([campaign(product_ids=["sku-1"], seller="shop-1")],
                          offer(item_id=None, seller=None))["campaigns"][0]
        self.assertEqual(result["status"], "potential")
        self.assertEqual(result["missing_facts"], ["product_ids", "seller"])

    def test_expired_and_future_are_ineligible(self):
        for dates, reason in [({"ends_at": "2026-10-26"}, "ends_at"),
                              ({"starts_at": "2026-10-28"}, "starts_at")]:
            result = evaluate([campaign(**dates)])["campaigns"][0]
            self.assertEqual(result["status"], "ineligible")
            self.assertIn(reason, result["reasons"])

    def test_timezone_boundaries_are_inclusive_and_date_end_includes_day(self):
        for dates in [{"starts_at": "2026-10-27T20:00:00+08:00"},
                      {"ends_at": "2026-10-27T20:00:00+08:00"},
                      {"ends_at": "2026-10-27"}]:
            self.assertEqual(evaluate([campaign(**dates)])["campaigns"][0]["status"], "eligible")
        self.assertEqual(evaluate(as_of=datetime(2026, 10, 27, 12, tzinfo=timezone.utc))["as_of"],
                         "2026-10-27T12:00:00+00:00")

    def test_cashback_does_not_lower_payable(self):
        result = evaluate([campaign(kind="cashback")])["best_eligible"][0]
        self.assertEqual(result["cashback"], "75000")
        self.assertEqual(result["amount_due"], "50000000")

    def test_stacking_never_sums_discounts_ties_retained_potential_separate(self):
        rules = [campaign(id="a"), campaign(id="b"),
                 campaign(id="unknown-larger", discount={"amount": "200000"}, cap="200000", confirmed=False)]
        result = evaluate(rules)
        self.assertEqual([r["id"] for r in result["best_eligible"]], ["a", "b"])
        self.assertEqual(result["best_eligible"][0]["amount_due"], "49925000")
        self.assertEqual(result["best_potential"][0]["id"], "unknown-larger")
        self.assertTrue(any("Stacking rules unverified" in warning for warning in result["warnings"]))

    def test_best_prefers_payable_then_cashback(self):
        rules = [campaign(id="cash", kind="cashback"),
                 campaign(id="instant", discount={"amount": "1"})]
        self.assertEqual(evaluate(rules)["best_eligible"][0]["id"], "instant")
        rules = [campaign(id="small", kind="cashback", cap="10"), campaign(id="large", kind="cashback")]
        self.assertEqual(evaluate(rules)["best_eligible"][0]["id"], "large")

    def test_discount_is_capped_to_price(self):
        for kind in ("instant", "cashback"):
            result = evaluate([campaign(discount={"amount": "999999999"}, kind=kind)],
                              offer(price={"amount": "100", "currency": "IDR"}))["best_eligible"][0]
            self.assertEqual(result["discount_amount"], "100")
            self.assertEqual(result["amount_due"], "0" if kind == "instant" else "100")

    def test_half_up_at_currency_scale_and_min_spend_before_rounding(self):
        for currency, amount, benefit, due in [("CNY", "10.05", "1.01", "9.04"),
                                                ("IDR", "105", "11", "94")]:
            result = evaluate([campaign(currency=currency, cap="1000")],
                              offer(price={"amount": amount, "currency": currency}))["best_eligible"][0]
            self.assertEqual((result["discount_amount"], result["amount_due"]), (benefit, due))
        result = evaluate([campaign(min_spend="50000000.1")])["campaigns"][0]
        self.assertEqual(result["status"], "ineligible")
        self.assertEqual(evaluate([campaign(min_spend="50000000")])["campaigns"][0]["status"], "eligible")

    def test_no_silent_universal_eligibility(self):
        rule = campaign()
        rule.pop("eligibility")
        result = evaluate([rule])["campaigns"][0]
        self.assertEqual(result["status"], "potential")
        self.assertIn("eligibility", result["missing_facts"])
        rule["requires"] = {"member": True}
        self.assertEqual(evaluate([rule], context={"member": True})["campaigns"][0]["status"], "eligible")

    def test_confirmation_provenance_and_observation_required(self):
        for field in ("confirmed", "source_url", "observed_at"):
            rule = campaign()
            rule.pop(field)
            result = evaluate([rule])["campaigns"][0]
            self.assertEqual(result["status"], "potential")
            self.assertIn(field, result["missing_facts"])
        for flag in ("unknown", "unconfirmed"):
            self.assertEqual(evaluate([campaign(eligibility=flag)])["campaigns"][0]["status"], "potential")
        self.assertEqual(evaluate([campaign(eligibility="ineligible")])["campaigns"][0]["status"], "ineligible")
        result = evaluate([campaign(observed_at="2026-10-28")])["campaigns"][0]
        self.assertIn("observed_at_not_future", result["missing_facts"])

    def test_missing_price_and_empty_rules(self):
        result = evaluate(item=offer(price={"amount": None, "currency": "IDR"}))
        self.assertIsNone(result["best_eligible"])
        self.assertIsNone(result["best_potential"])
        self.assertEqual(result["campaigns"][0]["status"], "potential")
        self.assertIsNone(result["campaigns"][0]["amount_due"])
        self.assertEqual(evaluate([])["campaigns"], [])

    def test_large_cashback_ties_do_not_depend_on_decimal_context(self):
        amount = "123456789012345678901234567890"
        lower = "123456789012345678901234567889"
        rules = [campaign(id="lower", kind="cashback", discount={"amount": lower}, cap=amount),
                 campaign(id="a", kind="cashback", discount={"amount": amount}, cap=amount),
                 campaign(id="b", kind="cashback", discount={"amount": amount + ".1"}, cap=amount)]
        result = evaluate(rules, offer(price={"amount": amount, "currency": "IDR"}))
        self.assertEqual([row["id"] for row in result["best_eligible"]], ["a", "b"])
        self.assertEqual(result["best_eligible"][0]["cashback"], amount)

    def test_nonfinite_negative_and_boolean_amounts_are_rejected(self):
        for value in (True, False, -1, "-0.01", "NaN", "sNaN", "Infinity", float("nan"),
                      float("inf"), Decimal("-Infinity"), None, {}, "1e1000"):
            for field in ("amount", "percent", "min_spend", "cap", "price"):
                with self.subTest(value=value, field=field):
                    rule, item = campaign(), offer()
                    if field == "price":
                        if value is None:
                            continue
                        item["price"]["amount"] = value
                    elif field in ("amount", "percent"):
                        rule["discount"] = {field: value}
                    else:
                        rule[field] = value
                    with self.assertRaises(ValueError):
                        evaluate([rule], item)

    def test_invalid_rules_dates_and_context(self):
        bad_rules = [{"discount": {"percent": 101}}, {"discount": {"amount": 1, "percent": 10}},
                     {"discount": {}}, {"discount": {"ammount": 1}}, {"kind": "other"},
                     {"requires": {"member": []}}, {"requires": {"member": None}},
                     {"confirmed": "true"}, {"min_spent": 100}, {"currency": "ZZZ"}, {"currency": []},
                     {"eligibility": True}, {"source_url": "javascript:bad"},
                     {"product_ids": []}, {"product_ids": [True]},
                     {"starts_at": "2026-10-29", "ends_at": "2026-10-28"}]
        for field in ("starts_at", "ends_at", "observed_at"):
            for value in ("bad", "2026-02-30", "2026-10-27T12:00:00", None):
                bad_rules.append({field: value})
        for fields in bad_rules:
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                evaluate([campaign(**fields)])
        for context in ([], {"member": []}, {"member": float("nan")}):
            with self.subTest(context=context), self.assertRaises(ValueError):
                evaluate(context=context)
        with self.assertRaises(ValueError):
            evaluate(as_of="2026-10-27T12:00:00")

    def test_annotation_only_adds_estimates_and_is_deterministic(self):
        offers = [offer(), offer(item_id="sku-2")]
        payload = {"campaigns": [campaign()], "as_of": AS_OF, "context": {"buyer_account": None}}
        before = copy.deepcopy((offers, payload))
        result = annotate_offers(offers, payload)
        self.assertEqual((offers, payload), before)
        self.assertEqual(result, annotate_offers(offers, payload))
        for original, annotated in zip(offers, result):
            self.assertEqual({k: v for k, v in annotated.items() if k != "coupon_estimates"}, original)
        result[0]["price"]["amount"] = "0"
        self.assertEqual(offers[0]["price"]["amount"], "50000000")
        with self.assertRaises(ValueError):
            annotate_offers([], {"campaigns": [campaign(discount={"percent": 101})]})

    def test_synthetic_example_is_json_and_does_not_claim_eligibility(self):
        path = Path(__file__).resolve().parents[1] / "examples" / "coupons.example.json"
        payload = json.loads(path.read_text())
        results = annotate_offers([offer()], payload)[0]["coupon_estimates"]
        self.assertIsNone(results["best_eligible"])
        self.assertTrue(all("synthetic" in row["id"] for row in results["campaigns"]))
        self.assertFalse(results["used_cart_checkout"])


if __name__ == "__main__":
    unittest.main()
