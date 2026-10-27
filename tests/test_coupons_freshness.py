import copy
import json
import unittest
from datetime import date, datetime, timezone

from china_deals.coupons import annotate_offers, assess_coupon_freshness, evaluate_coupons

AS_OF = "2026-10-27T12:00:00Z"


def campaign(**updates):
    row = {"id": "fresh", "marketplace": "blibli", "currency": "IDR",
           "discount": {"percent": "10"}, "cap": "75000", "confirmed": True,
           "eligibility": "confirmed", "source_url": "https://www.blibli.com/promosi/test",
           "source_mode": "coupon_page", "observed_at": "2026-10-27T11:30:00Z",
           "starts_at": "2026-10-27T00:00:00Z", "ends_at": "2026-10-28T00:00:00Z"}
    row.update(updates)
    return row


def offer(**updates):
    row = {"marketplace": "blibli", "item_id": "sku-1", "seller": "shop-1",
           "url": "https://www.blibli.com/p/synthetic/ps--sku-1",
           "price": {"amount": "50000000", "currency": "IDR", "list_price": "60000000"}}
    row.update(updates)
    return row


def evaluate(rules=None, item=None, **kwargs):
    return evaluate_coupons(offer() if item is None else item,
                            [campaign()] if rules is None else rules,
                            as_of=AS_OF, require_fresh=True, **kwargs)


class CouponFreshnessTests(unittest.TestCase):
    def test_fresh_evidence_remains_a_caller_assertion(self):
        row = evaluate()["best_eligible"][0]
        self.assertTrue(row["freshness"]["fresh"])
        self.assertEqual(row["freshness"]["status"], "fresh")
        self.assertEqual(row["freshness"]["age_hours"], "0.5")
        self.assertFalse(row["independently_verified"])
        self.assertFalse(row["used_cart_checkout"])
        self.assertFalse(row["freshness"]["independently_verified"])
        json.dumps(row, allow_nan=False)

    def test_stale_source_is_potential_only_when_required(self):
        rule = campaign(observed_at="2026-10-27T10:59:59Z")
        legacy = evaluate_coupons(offer(), [rule], None, AS_OF)
        self.assertEqual(legacy["campaigns"][0]["status"], "eligible")
        result = evaluate([rule])
        self.assertIsNone(result["best_eligible"])
        row = result["best_potential"][0]
        self.assertEqual(row["freshness"]["status"], "stale")
        self.assertIn("freshness", row["missing_facts"])
        self.assertEqual(row["amount_due"], "49925000")
        self.assertEqual(result["listing_amount"], "50000000")
        self.assertIsNotNone(evaluate([rule], max_age_hours=2)["best_eligible"])

    def test_future_observation_cannot_be_fresh(self):
        row = evaluate([campaign(observed_at="2026-10-27T12:00:01Z")])["campaigns"][0]
        self.assertEqual(row["status"], "potential")
        self.assertEqual(row["freshness"]["status"], "future_timestamp")

    def test_window_failures_remain_ineligible(self):
        for dates, status, reason in [
            ({"ends_at": "2026-10-27T11:59:59Z"}, "expired", "ends_at"),
            ({"starts_at": "2026-10-27T12:00:01Z"}, "not_started", "starts_at"),
        ]:
            with self.subTest(status=status):
                result = evaluate([campaign(**dates)])
                row = result["campaigns"][0]
                self.assertEqual(row["status"], "ineligible")
                self.assertEqual(row["freshness"]["status"], status)
                self.assertIn(reason, row["reasons"])
                self.assertIsNone(result["best_eligible"])
                self.assertIsNone(result["best_potential"])

    def test_both_boundaries_required_and_observation_must_be_inside(self):
        for field in ("starts_at", "ends_at"):
            rule = campaign()
            del rule[field]
            with self.subTest(field=field):
                row = evaluate([rule])["campaigns"][0]
                self.assertEqual(row["status"], "potential")
                self.assertIn(f"{field}_missing_or_invalid", row["freshness"]["reasons"])
        row = evaluate([campaign(starts_at="2026-10-27T11:45:00Z")])["campaigns"][0]
        self.assertFalse(row["freshness"]["fresh"])
        self.assertIn("observed_at_outside_validity_window", row["freshness"]["reasons"])

    def test_age_and_window_boundaries_are_inclusive_and_timezone_aware(self):
        for observed in ("2026-10-27T18:00:00+07:00", "2026-10-27T12:00:00Z"):
            rule = campaign(observed_at=observed, starts_at="2026-10-27T11:00:00Z",
                            ends_at="2026-10-27T12:00:00Z")
            self.assertTrue(assess_coupon_freshness(rule, AS_OF)["fresh"])
        rule = campaign(starts_at="2026-10-27", ends_at="2026-10-27")
        self.assertTrue(assess_coupon_freshness(rule, AS_OF)["fresh"])

    def test_cache_index_user_anonymous_and_unknown_modes_never_fresh(self):
        for mode in ("cached", "search_index", "indexed_product_block", "connector_product_open_cached",
                     "user_observation", "anonymous", "anonymous_coupon_page", "unknown", "guest_search"):
            with self.subTest(mode=mode):
                row = evaluate([campaign(source_mode=mode)])["campaigns"][0]
                self.assertEqual(row["status"], "potential")
                self.assertIn("source_mode_unverified", row["freshness"]["reasons"])
        rule = campaign()
        del rule["source_mode"]
        self.assertFalse(assess_coupon_freshness(rule, AS_OF)["fresh"])

    def test_only_recognized_first_party_https_evidence(self):
        for url in ("http://www.blibli.com/p/test", "https://blibli.com.attacker.test/p/test",
                    "https://notblibli.com/p/test", "https://www.jd.com/p/test",
                    "https://user@www.blibli.com/p/test", "https://www.blibli.com:8443/p/test",
                    "https://www.blibli.com:bad/p/test", "https://example.invalid/p/test"):
            with self.subTest(url=url):
                result = assess_coupon_freshness(campaign(source_url=url), AS_OF)
                self.assertFalse(result["fresh"])
                self.assertIn("source_url_not_first_party_https", result["reasons"])
        for mode in ("product_page", "guest_product_page", "retailer_product_page", "coupon_page",
                     "guest_coupon_page", "checkout_page", "guest_checkout_page", "guest_api"):
            self.assertTrue(assess_coupon_freshness(campaign(source_mode=mode), AS_OF)["fresh"])
        for market, host in (("taobao", "item.taobao.com"), ("taobao", "detail.tmall.com"),
                             ("jd", "item.jd.com"), ("goofish", "www.goofish.com")):
            self.assertTrue(assess_coupon_freshness(
                campaign(marketplace=market, source_url=f"https://{host}/test"), AS_OF)["fresh"])

    def test_no_date_or_verification_timestamp_laundering(self):
        for value in ("2026-10-27", date(2026, 10, 27), "2026-10-27T11:30:00",
                      datetime(2026, 10, 27, 11, 30), None):
            with self.subTest(value=value):
                result = assess_coupon_freshness(campaign(observed_at=value), AS_OF)
                self.assertFalse(result["fresh"])
                self.assertIn("observed_at_missing_or_invalid", result["reasons"])
        # Even near UTC midnight, legacy date normalization cannot create evidence.
        row = evaluate_coupons(offer(), [campaign(observed_at="2026-10-27")],
                               as_of="2026-10-27T00:30:00Z", require_fresh=True)["campaigns"][0]
        self.assertEqual(row["status"], "potential")
        stale = campaign(observed_at="2026-10-27T09:00:00Z", verified_at=AS_OF)
        self.assertEqual(assess_coupon_freshness(stale, AS_OF)["status"], "stale")
        del stale["observed_at"]
        self.assertFalse(assess_coupon_freshness(stale, AS_OF)["fresh"])

    def test_optional_verification_must_be_aware_and_chronological(self):
        for value in ("2026-10-27", "2026-10-27T11:40:00", "2026-10-27T12:00:01Z",
                      "2026-10-27T11:29:59Z", None):
            with self.subTest(value=value):
                self.assertFalse(assess_coupon_freshness(campaign(verified_at=value), AS_OF)["fresh"])
        self.assertTrue(assess_coupon_freshness(campaign(verified_at=AS_OF), AS_OF)["fresh"])

    def test_fresh_banner_does_not_supply_confirmation_or_account_facts(self):
        for updates, fact in (({"confirmed": False}, "confirmed"),
                              ({"eligibility": "unknown"}, "eligibility"),
                              ({"requires": {"buyer_account": "fansbuy"}}, "requires.buyer_account"),
                              ({"requires": {"quota_available": True}}, "requires.quota_available")):
            with self.subTest(updates=updates):
                row = evaluate([campaign(**updates)])["campaigns"][0]
                self.assertTrue(row["freshness"]["fresh"])
                self.assertEqual(row["status"], "potential")
                self.assertIn(fact, row["missing_facts"])

    def test_all_existing_requirements_and_identity_checks_still_apply(self):
        required = {"buyer_account": "fansbuy", "payment_method": "bank-a", "quantity": 1,
                    "selected_sku_eligible": True, "quota_available": True}
        rule = campaign(requires=required, product_ids=["sku-1"], seller="shop-1")
        self.assertIsNotNone(evaluate([rule], context=required)["best_eligible"])
        for field in required:
            context = dict(required, **{field: None})
            row = evaluate([rule], context=context)["campaigns"][0]
            self.assertEqual(row["status"], "potential")
            self.assertIn(f"requires.{field}", row["missing_facts"])
            context[field] = False if required[field] is True else "wrong"
            self.assertEqual(evaluate([rule], context=context)["campaigns"][0]["status"], "ineligible")
        for item in (offer(seller="other"), offer(item_id="other"),
                     offer(url="https://www.blibli.com/p/synthetic/ps--other")):
            self.assertEqual(evaluate([rule], item, context=required)["campaigns"][0]["status"], "ineligible")

    def test_maximum_ties_retained_and_stale_larger_discount_separate(self):
        rules = [campaign(id="a"), campaign(id="b"),
                 campaign(id="stale-larger", discount={"amount": "100000"}, cap="100000",
                          observed_at="2026-10-27T10:00:00Z")]
        result = evaluate(rules)
        self.assertEqual([row["id"] for row in result["best_eligible"]], ["a", "b"])
        self.assertEqual([row["id"] for row in result["best_potential"]], ["stale-larger"])
        self.assertEqual(result["best_eligible"][0]["discount_amount"], "75000")

    def test_annotation_preserves_price_intent_exclusions_and_inputs(self):
        offers = [offer(intent={"product": "gpu", "quantity": 1},
                        exclusions=["wrong_variant"], excluded=True, rankable=False)]
        payload = {"campaigns": [campaign()], "as_of": "2026-10-27T10:00:00Z"}
        before = copy.deepcopy((offers, payload))
        annotated = annotate_offers(offers, payload, require_fresh=True, as_of=AS_OF)
        self.assertEqual((offers, payload), before)
        self.assertEqual({k: v for k, v in annotated[0].items() if k != "coupon_estimates"}, offers[0])
        self.assertEqual(annotated[0]["coupon_estimates"]["as_of"], "2026-10-27T12:00:00+00:00")
        annotated[0]["intent"]["quantity"] = 9
        self.assertEqual(offers[0]["intent"]["quantity"], 1)
        # Without an explicit override, existing payload.as_of remains authoritative.
        self.assertEqual(annotate_offers(offers, payload)[0]["coupon_estimates"]["as_of"],
                         "2026-10-27T10:00:00+00:00")

    def test_independent_guard_and_options_validate_without_offers(self):
        evidence = campaign()
        for key in ("currency", "discount", "cap", "confirmed", "eligibility"):
            del evidence[key]
        self.assertTrue(assess_coupon_freshness(evidence, datetime(2026, 10, 27, 12,
                                                                tzinfo=timezone.utc))["fresh"])
        for value in (0, -1, True, "NaN", "Infinity", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                annotate_offers([], {"campaigns": []}, max_age_hours=value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                assess_coupon_freshness(evidence, AS_OF, max_age_hours=value)
        with self.assertRaises(ValueError):
            annotate_offers([], {"campaigns": []}, require_fresh="true")


if __name__ == "__main__":
    unittest.main()
