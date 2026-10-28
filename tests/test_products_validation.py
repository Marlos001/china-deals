"""Offline synthetic regressions; none of these fixtures authenticates a listing."""

import unittest

from china_deals.products import assess_product, intent_family, query_plan


class ProductValidationTests(unittest.TestCase):
    def assert_status(self, query, title, status, variant=""):
        offer = {"title": title, "variant": variant}
        original = dict(offer)
        result = assess_product(offer, query)
        self.assertEqual(result["status"], status, (offer, query, result))
        self.assertEqual(offer, original)
        self.assertEqual(result["family"], intent_family(query))
        self.assertTrue(result["reasons"])
        return result

    def test_selected_model_cannot_be_overridden_by_title(self):
        for query, title, wrong, right in (
            ("iPhone 17 Pro Max", "iPhone17ProMax", "iPhone16ProMax", "iPhone17ProMax 256GB"),
            ("AirPods Max", "Apple AirPods Max", "AirPodsPro2", "AirPods Max USB-C"),
            ("ROG Zephyrus G14", "ASUS ROG Zephyrus G14", "ZephyrusG16", "G14 32GB"),
        ):
            with self.subTest(query=query):
                result = self.assert_status(query, title, "mismatch", wrong)
                self.assertIn("selected_variant", " ".join(result["reasons"]))
                self.assert_status(query, title, "match", right)
                self.assert_status(query, title, "match", "black")
                self.assert_status(query, wrong + " " + title, "mismatch")

    def test_model_tokens_do_not_merge_with_capacity_or_year(self):
        self.assert_status("ROG Zephyrus G14", "ROG Zephyrus G14", "mismatch", "G16 32GB")
        self.assert_status("ROG Zephyrus G14", "ROG Zephyrus G14 2024", "match")
        self.assert_status("ROG Zephyrus G14", "ROG Zephyrus G14", "match", "G14 32GB")
        self.assert_status("ROG Zephyrus G16", "ROG Zephyrus G16 2025", "match")

    def test_abbreviated_selected_iphone_model_has_priority(self):
        for variant in ("16 Pro Max 256GB", "17 Pro 256GB", "16ProMax 256GB"):
            self.assert_status("iPhone 17 Pro Max", "iPhone 17 Pro Max", "mismatch", variant)
        self.assert_status("iPhone 17 Pro Max", "iPhone 17 Pro Max", "match", "17 Pro Max 256GB")
        self.assert_status("iPhone 17 Pro Max", "iPhone 17 Pro Max", "match", "256GB black")

    def test_bundle_trimming_does_not_erase_selected_accessory(self):
        for title in ("AirPods Max with Smart Case", "AirPods Max includes Smart Case",
                      "AirPods Max 含 Smart Case", "AirPods Max 附赠 Smart Case"):
            for variant in ("Smart Case only", "case only", "Smart Case 单卖"):
                with self.subTest(title=title, variant=variant):
                    self.assert_status("AirPods Max", title, "mismatch", variant)
            self.assert_status("AirPods Max", title, "match", "black")
        self.assert_status("AirPods Max", "AirPods Max with Smart Case only", "mismatch")
        self.assert_status("iPhone 17 Pro Max", "iPhone 17 Pro Max with case", "mismatch", "case only")

    def test_airpods_report_non_products(self):
        for title in ("AirPods Max 头梁 单卖", "AirPods Max 维修 不开机维修",
                      "AirPods Max repair service", "AirPods Max display dummy 模型机",
                      "AirPods Max 模型机", "AirPods Max 1:1 replica 高仿",
                      "AirPods Max 精仿", "AirPods Max 山寨", "AirPods Max 复刻",
                      "AirPods Max Smart Case", "AirPods Max ear cushions", "AirPods Max 耳罩",
                      "AirPods Max replacement headband"):
            with self.subTest(title=title):
                self.assert_status("AirPods Max", title, "mismatch")
                self.assert_status("AirPods Max", "AirPods Max 含 Smart Case", "mismatch", title)
        for title in ("Apple AirPods Max USB-C 头戴式耳罩式耳机", "Apple AirPods Max USB-C 含 Smart Case",
                      "AirPods Max A2096", "AirPods Max A3184", "AirPods Max A3454",
                      "AirPods Max with Smart Case", "AirPods Max 耳罩式耳机"):
            with self.subTest(title=title):
                self.assert_status("AirPods Max", title, "match")

    def test_price_scope_is_independent_of_relevance_and_numeric_price(self):
        qualifiers = ("monthly installment", "月付", "每月", "cicilan bulanan", "cicilan",
                      "月供", "per bulan", "/month", "首付", "deposit", "定金", "订金", "uang muka")
        for qualifier in qualifiers:
            for source in ("title", "variant"):
                offer = {"title": "AirPods Max", "variant": "", "price": "100"}
                offer[source] += " " + qualifier
                with self.subTest(qualifier=qualifier, source=source):
                    result = assess_product(offer, "AirPods Max")
                    self.assertEqual(result["status"], "match")
                    self.assertEqual(result["price_scope_warnings"], ["possible_deposit_or_installment_price"])
        for title in ("AirPods Max USB-C", "AirPods Max 12 month warranty", "AirPods Max full price"):
            self.assertEqual(assess_product({"title": title}, "AirPods Max")["price_scope_warnings"], [])

    def test_zephyrus_model_evidence_and_accessories(self):
        for title in ("Zephyrus G14 charger", "Charger ASUS ROG Zephyrus G14",
                      "华硕 ROG 幻14 充电器", "Zephyrus G14 adapter", "华硕 ROG 幻16 笔记本"):
            self.assert_status("ROG Zephyrus G14", title, "mismatch")
        for title in ("ASUS ROG Zephyrus", "ASUS GA402XV", "ASUS laptop", "G14 laptop"):
            self.assert_status("ROG Zephyrus G14", title, "uncertain")
        self.assert_status("ROG Zephyrus G14", "华硕 ROG 幻14 笔记本", "match")
        self.assert_status("ROG Zephyrus G16", "华硕 ROG 幻16 笔记本", "uncertain")
        self.assert_status("ROG Zephyrus M16", "华硕 ROG 幻16 笔记本", "uncertain")
        self.assert_status("ROG Zephyrus", "华硕 ROG 幻16 笔记本", "match")
        self.assert_status("ROG Zephyrus G14", "ROG Zephyrus G14 with charger", "match")
        self.assert_status("ROG Zephyrus G14", "ROG Zephyrus G14 with charger", "mismatch", "charger only")

    def test_exact_configuration_needs_evidence(self):
        for query, title, wrong, right in (
            ("iPhone 17 Pro Max 512GB", "iPhone 17 Pro Max", "256GB", "512GB"),
            ("AirPods Max USB-C", "AirPods Max", "Lightning", "USB-C"),
            ("AirPods Max A3184", "AirPods Max", "A2096", "A3184"),
        ):
            self.assert_status(query, title, "uncertain")
            self.assert_status(query, title, "mismatch", wrong)
            self.assert_status(query, title, "match", right)
            self.assert_status(query, title + " " + right, "mismatch", wrong)
        self.assert_status("AirPods Max USB-C", "AirPods Max A3454", "uncertain")
        self.assert_status("iPhone 17 Pro Max 512GB", "iPhone 17 Pro Max 256GB / 512GB", "uncertain")

    def test_revision_missing_is_unknown_and_literal_conflicts_are_excluded(self):
        self.assert_status("AirPods Max 2", "AirPods Max", "uncertain")
        self.assert_status("AirPods Max 2", "AirPods Max 1", "mismatch")
        self.assert_status("AirPods Max 2", "AirPods Max", "match", "AirPods Max 2")
        self.assert_status("AirPods Max 2", "AirPods Max A3454", "uncertain")
        self.assert_status("AirPods Max A3184", "AirPods Max A2096 / A3184", "uncertain")
        self.assert_status("AirPods Max A3184", "AirPods Max A2096 / A3184", "match", "A3184")

    def test_repair_history_and_explicit_negations_are_not_service_or_replica_offers(self):
        for title in ("AirPods Max no repairs", "AirPods Max not a replica", "AirPods Max 无维修",
                      "AirPods Max 非高仿", "AirPods Max 已维修", "AirPods Max 维修过"):
            self.assert_status("AirPods Max", title, "match")
        self.assert_status("AirPods Max", "AirPods Max no repairs, replica", "mismatch")

    def test_descriptions_and_source_summaries_do_not_prove_listing(self):
        result = assess_product({"title": "Headphones", "description": "AirPods Max A3184 USB-C",
                                 "source_summary": "Apple authenticates AirPods Max"}, "AirPods Max")
        self.assertEqual(result["status"], "uncertain")

    def test_query_plans_preserve_refinements_and_accessory_scope(self):
        queries = ("ROG Zephyrus G14", "ASUS ROG Zephyrus G14 32GB 1TB", "AirPods Max USB-C",
                   "AirPods Max A3184", "iPhone 17 Pro Max 512GB", "case for iPhone 17 Pro Max",
                   "AirPods Max Smart Case only", "Zephyrus G14 charger", "华硕 ROG 幻14 充电器")
        for query in queries:
            with self.subTest(query=query):
                plan = query_plan(query)
                self.assertEqual(plan["query"], query)
                for market, suggestions in plan["marketplace_queries"].items():
                    self.assertEqual(len(suggestions), 1)
                    self.assertIn(query, suggestions[0])
                    if market not in {"blibli", "alibaba", "aliexpress"}:
                        self.assertTrue(any("\u3400" <= c <= "\u9fff" for c in suggestions[0]))
                    if any(s in query for s in ("case", "Case", "charger", "充电器")):
                        self.assertNotIn("手机", suggestions[0])
                        self.assertNotIn("headphones", suggestions[0])
                        self.assertNotIn("笔记本", suggestions[0])

    def test_broad_query_plan_covers_documented_families_without_invented_hardware(self):
        for query in ("ASUS ROG Zephyrus", "all Zephyrus", "ROG Zephyrus all"):
            for suggestions in query_plan(query)["marketplace_queries"].values():
                combined = " ".join(suggestions)
                for model in ("G14", "G15", "G16", "M16", "Duo", "S17"):
                    self.assertIn(model, combined)
                self.assertNotIn("RTX", combined)
                self.assertNotIn("2026", combined)

    def test_accessory_intent_does_not_claim_whole_product(self):
        self.assert_status("AirPods Max Smart Case", "Smart Case for AirPods Max", "match")
        self.assert_status("case for iPhone 17 Pro Max", "iPhone 17 Pro Max case", "match")
        self.assert_status("Zephyrus G14 charger", "ROG Zephyrus G14 charger", "match")
        self.assert_status("AirPods Max Smart Case", "AirPods Max headphones", "uncertain")

    def test_public_input_validation(self):
        for query in (None, 123, "", "\nAirPods Max", "a" * 501):
            with self.subTest(query=query), self.assertRaises(ValueError):
                query_plan(query)


if __name__ == "__main__":
    unittest.main()
