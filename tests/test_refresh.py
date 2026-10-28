"""Offline refresh orchestration, quote comparability and durable receipt tests."""

import copy
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from china_deals import adapters, browser_guest, guest, refresh
from china_deals.ranking import rank_offers

NOW = "2026-10-27T12:00:00+00:00"
BEFORE = "2026-10-27T10:00:00+00:00"
URL = "https://item.jd.com/123.html"
MOBILE = "https://item.m.jd.com/product/123.html"


def quote(**changes):
    return {"marketplace": "jd", "item_id": "123", "url": URL, "title": "New product",
            "price": "100", "currency": "CNY", "source_mode": "guest_product_page",
            "observed_at": NOW, "variant": "32 GB / black", "condition": "new",
            "payment": "single full payment", **changes}


def receipt(row=None, **changes):
    return {"marketplace": "jd", "status": "ok", "items": [quote() if row is None else row],
            "error": None, "access": {"attempts": [{"url": MOBILE, "status": "ok",
                                                       "attempted_at": NOW, "network_attempted": True}]}, **changes}


class RefreshTests(unittest.TestCase):
    def run_refresh(self, source=None, response=None, **options):
        with patch.object(guest, "get_guest_item", return_value=receipt() if response is None else response) as getter:
            result = refresh.refresh_offers([quote(observed_at=BEFORE, price="120") if source is None else source],
                                            as_of=NOW, **options)
        return result, getter

    def test_default_always_fetches_even_recent_with_force_false(self):
        for force in (False, True):
            result, getter = self.run_refresh(force=force)
            getter.assert_called_once()
            args, kwargs = getter.call_args
            self.assertEqual(args, ("jd", URL))
            self.assertGreater(kwargs["timeout"], 0)
            self.assertLessEqual(kwargs["timeout"], 30)
            item = result["items"][0]
            self.assertEqual(item["refresh"]["status"], "refreshed")
            self.assertEqual(item["price"]["amount"], "100")
            self.assertEqual(item["previous_observation"]["price"]["amount"], "120")
            self.assertEqual(item["observed_at"], NOW)
            self.assertTrue(item["price_freshness"]["recent_observation"])
            self.assertEqual(item["price_delta"]["amount"], "-20")
            self.assertEqual(item["price_delta"]["percent"], "-16.67")
            self.assertFalse(item["price_delta"]["verified_historic_savings"])

    def test_new_detail_does_not_inherit_old_product_facts(self):
        old = quote(title="Old title", description="Old specs", hardware={"ram": "64GB"}, seller="Old shop")
        new = {"url": URL, "item_id": "123", "source_mode": "guest_product_page", "observed_at": NOW}
        result, _ = self.run_refresh(old, receipt(new))
        item = result["items"][0]
        for field in ("title", "hardware", "variant", "seller", "selected_variant", "payment"):
            self.assertIsNone(item[field], field)
        self.assertEqual(item["description"], "")
        self.assertEqual(item["condition"], "unknown")
        self.assertIsNone(item["price"]["amount"])
        self.assertEqual(item["refresh"]["status"], "unpriced")
        self.assertEqual(item["previous_observation"]["title"], "Old title")

    def test_failed_refresh_suppresses_previous_price_and_chain_does_not_grow(self):
        failure = receipt(status="blocked", error={"code": "challenge"}, items=[])
        result, _ = self.run_refresh(response=failure)
        item = result["items"][0]
        self.assertIsNone(item["price"]["amount"])
        self.assertIsNone(item["price"]["raw"])
        self.assertIsNone(item["observed_at"])
        self.assertIsNone(item["title"])
        self.assertEqual(item["previous_observation"]["price"]["amount"], "120")
        again, _ = self.run_refresh(item, failure)
        previous = again["items"][0]["previous_observation"]
        self.assertEqual(previous["price"]["amount"], "120")
        self.assertNotIn("previous_observation", previous)

    def test_masked_price_never_inherits_old_amount(self):
        result, _ = self.run_refresh(response=receipt(quote(price="1??99")))
        item = result["items"][0]
        self.assertIsNone(item["price"]["amount"])
        self.assertEqual(item["price"]["raw"], "1??99")
        self.assertEqual(item["refresh"]["status"], "unpriced")

    def test_cached_stale_future_missing_timestamp_and_unknown_modes(self):
        cases = [({"source_mode": "connector_product_open_cached"}, "cached_or_aggregated_source"),
                 ({"observed_at": "2026-10-20T12:00:00Z"}, "older_than_limit"),
                 ({"observed_at": "2026-10-28T12:00:00Z"}, "future_timestamp"),
                 ({"observed_at": None}, "unknown"), ({"source_mode": "unspecified"}, "unknown")]
        for changes, expected in cases:
            with self.subTest(changes=changes):
                result, _ = self.run_refresh(response=receipt(quote(**changes)))
                item = result["items"][0]
                self.assertIsNone(item["price"]["amount"])
                self.assertEqual(item["refresh"]["status"], "nonrecent_observation")
                self.assertEqual(item["price_freshness"]["status"], expected)
                self.assertEqual(item["observed_at"], changes.get("observed_at", NOW))

    def test_changed_variant_and_unknown_scope_refuse_deltas(self):
        cases = [({"variant": "16 GB / black"}, "different_selected_variant"),
                 ({"variant": ""}, "selected_variant_unknown"),
                 ({"condition": "used"}, "different_conditions_or_payment"),
                 ({"payment": "installments"}, "different_conditions_or_payment"),
                 ({"condition": "unknown"}, "conditions_or_payment_unknown"),
                 ({"payment": None}, "conditions_or_payment_unknown")]
        for changes, reason in cases:
            with self.subTest(changes=changes):
                result, _ = self.run_refresh(response=receipt(quote(**changes)))
                self.assertEqual(result["items"][0]["price_delta"]["reason"], reason)

    def test_material_configuration_must_match_for_delta(self):
        prior = quote(observed_at=BEFORE, variant="black", hardware={"ram_gb": 16})
        for changes, expected in [
            ({"hardware": {"ram_gb": 16}}, "comparable_observed_change"),
            ({"hardware": {"ram_gb": 32}}, "different_or_unknown_material_variant"),
            ({"hardware": None}, "different_or_unknown_material_variant"),
            ({"hardware": {"ram_gb": 16}, "variant_observations": ["black", "32 GB"]}, "material_variant_ambiguous"),
        ]:
            with self.subTest(changes=changes):
                result, _ = self.run_refresh(prior, receipt(quote(variant="black", **changes)))
                delta = result["items"][0]["price_delta"]
                self.assertEqual(delta["status"] if expected == "comparable_observed_change" else delta["reason"], expected)
        result, _ = self.run_refresh(quote(observed_at=BEFORE, variant="black"), receipt(quote(variant="black")))
        self.assertEqual(result["items"][0]["price_delta"]["reason"], "material_variant_ambiguous")

    def test_old_or_nonprimary_previous_and_same_time_do_not_compare(self):
        for prior, reason in [(quote(observed_at="2026-10-20T10:00:00Z"), "requires_recent_primary_observations"),
                              (quote(source_mode="search_index", observed_at=BEFORE), "requires_recent_primary_observations"),
                              (quote(), "observation_not_newer")]:
            result, _ = self.run_refresh(prior)
            self.assertEqual(result["items"][0]["price_delta"]["reason"], reason)

    def test_listing_attributes_with_unknown_selected_sku_are_not_selected_variant(self):
        for changes in ({"selected_sku_id": None}, {"detail": {"selected_sku_id": None}},
                        {"selected_variant": "Other selection"}):
            with self.subTest(changes=changes):
                result, _ = self.run_refresh(response=receipt(quote(**changes)))
                self.assertIsNone(result["items"][0]["selected_variant"])
                self.assertEqual(result["items"][0]["price_delta"]["reason"], "selected_variant_unknown")

    def test_discount_is_only_new_seller_claim(self):
        result, _ = self.run_refresh(quote(discount="50%"), receipt(quote(original_price="150", discount="33%")))
        claims = result["items"][0]["discount_claims"]
        self.assertEqual(claims["claims"], {"original_price": "150", "discount": "33%"})
        self.assertFalse(claims["verified_historic_savings"])

    def test_intent_preserved_and_relevance_reassessed(self):
        old = quote(intent_query="iPhone 17 Pro Max", relevance={"status": "match"},
                    ranking_exclusions=["manual_review_required"], exclusions=["accessories"])
        original = copy.deepcopy(old)
        result, _ = self.run_refresh(old, receipt(quote(title="iPhone 16 Pro Max")))
        item = result["items"][0]
        self.assertEqual(old, original)
        self.assertEqual(item["intent_query"], old["intent_query"])
        self.assertEqual(item["original_context"]["relevance"], {"status": "match"})
        self.assertEqual(item["original_context"]["exclusions"], ["accessories"])
        self.assertNotEqual(item["relevance"]["status"], "match")
        self.assertIn("manual_review_required", item["ranking_exclusions"])

    def test_invalid_targets_fail_before_any_network(self):
        bad = ["123", "https://item.jd.com.evil.test/123.html", "http://item.jd.com/123.html",
               "https://user:pass@item.jd.com/123.html", "https://item.jd.com:443/123.html",
               "https://item.jd.com/product/opaque.html", "https://search.jd.com/Search?keyword=test"]
        with patch.object(guest, "get_guest_item") as getter:
            for url in bad:
                with self.subTest(url=url), self.assertRaises(ValueError):
                    refresh.refresh_offers([quote(), quote(url=url)])
            with self.assertRaises(ValueError):
                refresh.refresh_offers([quote(item_id="999")])
            with self.assertRaises(ValueError):
                refresh.refresh_offers([{"marketplace": "taobao", "url": "https://item.taobao.com/item.htm?id=123&id="}])
            getter.assert_not_called()

    def test_input_limits_and_options(self):
        invalid = [{"timeout": 0}, {"timeout": 301}, {"timeout": float("inf")}, {"timeout": True},
                   {"backend": "auto"}, {"force": "yes"}, {"max_age_hours": 0}, {"max_age_hours": 8761},
                   {"as_of": "2026-10-27"}, {"store_path": ":memory:"}]
        with patch.object(guest, "get_guest_item") as getter:
            for options in invalid:
                with self.subTest(options=options), self.assertRaises(ValueError):
                    refresh.refresh_offers([quote()], **options)
            for payload in ([quote()] * 51, [quote(description="x" * refresh.MAX_RECORD_BYTES)], {}, [None]):
                with self.assertRaises(ValueError):
                    refresh.refresh_offers(payload)
            with self.assertRaises(ValueError):
                refresh.refresh_offers({"query_intent": "x" * refresh.MAX_RECORD_BYTES, "items": [quote()]})
            getter.assert_not_called()

    def test_envelope_shapes_and_fifty_item_bound(self):
        with patch.object(guest, "get_guest_item", return_value=receipt()) as getter:
            for payload in ({"offers": [quote()]}, {"items": [quote()]},
                            {"groups": {"CNY": [quote()]}, "unranked": []}):
                self.assertEqual(len(refresh.refresh_offers(payload, as_of=NOW)["items"]), 1)
            result = refresh.refresh_offers([quote()] * 50, as_of=NOW)
            self.assertEqual(len(result["items"]), 50)
            self.assertEqual(getter.call_count, 53)

    def test_wrong_identity_and_multirow_receipts_are_rejected(self):
        cases = [receipt(quote(item_id="999")), receipt(quote(url="https://item.jd.com/999.html")),
                 receipt(quote(sku="999")), receipt(items=[quote(), quote()]),
                 receipt(quote(marketplace="taobao")), receipt(quote(offers={"url": "https://item.jd.com/999.html"}))]
        for response in cases:
            with self.subTest(response=response):
                result, _ = self.run_refresh(response=response)
                self.assertIsNone(result["items"][0]["price"]["amount"])
                self.assertEqual(result["items"][0]["refresh"]["error"]["code"], "detail_identity_or_schema_unverified")

    def test_output_limit_preserves_access_receipt(self):
        result, _ = self.run_refresh(response=receipt(quote(description="x" * refresh.MAX_RECORD_BYTES)))
        item = result["items"][0]
        self.assertEqual(item["refresh"]["error"]["code"], "detail_output_limit")
        self.assertTrue(item["refresh"]["access"]["attempts"][0]["network_attempted"])
        self.assertIsNone(item["price"]["amount"])

    def test_raw_browser_capture_is_discarded_before_retained_receipt_limit(self):
        result, _ = self.run_refresh(response=receipt(quote(detail={"capture": {"mainHtml": "x" * 100000},
                                                                  "product": {"skuId": "123"}})))
        self.assertEqual(result["items"][0]["refresh"]["status"], "refreshed")
        self.assertNotIn("capture", result["items"][0]["source_detail"])
        self.assertEqual(result["items"][0]["source_detail"]["product"]["skuId"], "123")

    def test_gate_stops_same_actual_host_and_other_host_continues(self):
        blibli = {"marketplace": "blibli", "url": "https://www.blibli.com/p/example/ps--TEST-1"}
        gate = receipt(status="blocked", error={"code": "http_429"}, items=[])
        with patch.object(guest, "get_guest_item", side_effect=[gate, receipt(status="unavailable", items=[])]) as getter:
            result = refresh.refresh_offers([quote(), quote(item_id="124", url="https://item.jd.com/124.html"), blibli], as_of=NOW)
        self.assertEqual(getter.call_count, 2)
        skipped = result["items"][1]["refresh"]
        self.assertEqual(skipped["error"]["code"], "skipped_after_challenge")
        self.assertFalse(skipped["access"]["attempts"][0]["network_attempted"])

    def test_real_guard_with_mocked_fetch_never_retries_challenge(self):
        with patch.object(guest, "_fetch", side_effect=adapters._Failure("blocked", "challenge", "Stop")) as fetch:
            result = refresh.refresh_offers([quote(), quote()], as_of=NOW)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(result["items"][1]["refresh"]["error"]["code"], "skipped_after_challenge")

    def test_nested_session_keeps_gates_force_does_not_reset(self):
        with guest.access_session():
            guest._record_gate({"url": MOBILE}, adapters._Failure("blocked", "challenge", "Stop"))
            result, getter = self.run_refresh(force=True)
            getter.assert_not_called()
            self.assertEqual(result["items"][0]["refresh"]["error"]["code"], "skipped_after_challenge")

    def test_explicit_browser_has_no_http_fallback(self):
        with patch.object(browser_guest, "get_browser_guest_item", return_value=receipt(status="blocked", error={"code": "challenge"}, items=[])) as browser:
            with patch.object(guest, "get_guest_item") as http:
                result = refresh.refresh_offers([quote(), quote()], backend="browser", as_of=NOW)
        browser.assert_called_once()
        http.assert_not_called()
        self.assertEqual(result["items"][1]["refresh"]["error"]["code"], "skipped_after_challenge")

    def test_one_shared_deadline_and_late_response_not_fresh(self):
        ticks = iter([0.0, 0.0, 3.0, 3.0])
        with patch.object(refresh.time, "monotonic", side_effect=lambda: next(ticks)):
            with patch.object(guest, "get_guest_item", return_value=receipt()) as getter:
                result = refresh.refresh_offers([quote(), quote()], timeout=2, as_of=NOW)
        getter.assert_called_once()
        for item in result["items"]:
            self.assertEqual(item["refresh"]["error"]["code"], "timeout")
            self.assertIsNone(item["price"]["amount"])
        self.assertFalse(result["items"][1]["refresh"]["access"]["attempts"][0]["network_attempted"])

    def test_mocked_first_party_jd_parse_integration(self):
        body = '<script>window._itemInfo = ' + json.dumps({"product": {"skuId": "123", "skuName": "Current title"},
                                                          "priceFloor": {"price": "99", "skuId": "123"}}) + ';</script>'
        with patch.object(guest, "_fetch", return_value=(body, MOBILE)), patch.object(guest, "utc_now", return_value=NOW):
            result = refresh.refresh_offers([quote()], as_of=NOW)
        item = result["items"][0]
        self.assertEqual(item["price"]["amount"], "99")
        self.assertEqual(item["title"], "Current title")
        self.assertEqual(item["source_detail"]["product"]["skuId"], "123")
        self.assertIsNone(item["variant"])
        self.assertEqual(item["price_delta"]["reason"], "selected_variant_unknown")


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "observations.sqlite"

    def refresh(self, response=None, payload=None, **kwargs):
        with patch.object(guest, "get_guest_item", return_value=receipt() if response is None else response):
            return refresh.refresh_offers([{"marketplace": "jd", "url": URL}] if payload is None else payload,
                                          store_path=self.path, as_of=NOW, **kwargs)

    def test_repeat_store_dedup_even_if_assessment_time_changes(self):
        first = self.refresh()
        second = self.refresh()
        with patch.object(guest, "get_guest_item", return_value=receipt()):
            third = refresh.refresh_offers([quote()], store_path=self.path, as_of="2026-10-29T12:00:00Z")
        self.assertEqual(first["storage"]["inserted"], 1)
        self.assertEqual(second["storage"]["inserted"], 0)
        self.assertEqual(third["storage"]["inserted"], 0)
        self.assertEqual(first["items"][0]["observation_hash"], third["items"][0]["observation_hash"])
        self.assertEqual(len(refresh.history(self.path)), 1)

    def test_prior_store_quote_used_for_bare_watchlist(self):
        self.refresh(receipt(quote(price="150", observed_at=BEFORE)))
        result = self.refresh()
        self.assertEqual(result["items"][0]["price_delta"]["amount"], "-50")
        self.assertEqual(result["items"][0]["previous_observation"]["observed_at"], BEFORE)
        entries = refresh.history(self.path, marketplace="jd", item_id="123", limit=1)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["observation"]["price"]["amount"], "100")
        self.assertEqual(refresh.history(self.path, marketplace="goofish"), [])

    def test_conflicting_selection_survives_history_and_ranking(self):
        row = quote(title="iPhone 17 Pro Max", variant="iPhone 17 Pro Max",
                    variant_observations=["iPhone 16 Pro Max"])
        result = self.refresh(receipt(row), payload=[quote(intent_query="iPhone 17 Pro Max")])
        item = result["items"][0]
        observation = refresh.history(self.path)[0]["observation"]
        self.assertIn("iPhone 16 Pro Max", item["variant_observations"])
        self.assertEqual(observation["variant_observations"], item["variant_observations"])
        ranked = rank_offers([item], query="iPhone 17 Pro Max", as_of=NOW)
        self.assertFalse(ranked["groups"])
        self.assertEqual(len(ranked["unranked"]), 1)

    def test_history_read_is_bounded_and_does_not_create_missing_store(self):
        with self.assertRaises(FileNotFoundError):
            refresh.history(self.path)
        self.assertFalse(self.path.exists())
        for limit in (0, 51, True, 1.5, "2"):
            with self.assertRaises(ValueError):
                refresh.history(self.path, limit=limit)
        self.refresh()
        self.assertEqual(refresh.history(self.path, item_id="123' OR 1=1 --"), [])

    def test_storage_failure_keeps_network_receipts(self):
        self.path.write_text("Not SQLite")
        result = self.refresh()
        self.assertEqual(result["storage"]["status"], "error")
        self.assertEqual(result["items"][0]["price"]["amount"], "100")
        self.assertEqual(result["items"][0]["refresh"]["access"]["attempts"][0]["status"], "ok")

    def test_oversized_retained_row_is_rejected_by_bounded_history_read(self):
        self.refresh()
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("UPDATE refresh_observations SET payload = ?", ('"' + 'x' * (4 * refresh.MAX_RECORD_BYTES) + '"',))
            connection.commit()
        finally:
            connection.close()
        with self.assertRaises(ValueError):
            refresh.history(self.path)
        result = self.refresh()
        self.assertEqual(result["storage"]["status"], "error")
        self.assertEqual(result["items"][0]["refresh"]["status"], "refreshed")

    def test_missing_directory_write_failure_keeps_receipts(self):
        self.path = self.path / "missing" / "observations.sqlite"
        result = self.refresh()
        self.assertEqual(result["storage"]["errors"], [{"operation": "write", "code": "history_write_failed"}])
        self.assertEqual(result["items"][0]["refresh"]["status"], "refreshed")

    def test_no_cookies_raw_captures_or_gate_tokens_are_stored(self):
        row = quote(detail={"cookies": "SECRET_COOKIE", "raw_capture": "RAW_DOM", "product": {"skuId": "123"}})
        response = receipt(row)
        response["access"]["attempts"][0]["challenge_url"] = "https://passport.jd.com/verify?token=SECRET_TOKEN"
        response["access"]["cookies"] = "SESSION_COOKIE"
        result = self.refresh(response)
        raw = json.dumps(refresh.history(self.path)) + json.dumps(result)
        for secret in ("SECRET_COOKIE", "RAW_DOM", "SECRET_TOKEN", "SESSION_COOKIE"):
            self.assertNotIn(secret, raw)
        self.assertIn('"skuId": "123"', raw)

    def test_concurrent_writers_dedup_and_transactions_are_atomic(self):
        with patch.object(guest, "get_guest_item", return_value=receipt()):
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = list(pool.map(lambda _: refresh.refresh_offers([quote()], store_path=self.path, as_of=NOW), range(8)))
        self.assertEqual(sum(result["storage"]["inserted"] for result in results), 1)
        self.assertEqual(len(refresh.history(self.path)), 1)
        self.assertTrue(all(result["storage"]["status"] == "ok" for result in results))
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("""CREATE TRIGGER reject_second BEFORE INSERT ON refresh_observations
                                  WHEN NEW.item_id = '124' BEGIN SELECT RAISE(ABORT, 'test'); END""")
            connection.commit()
        finally:
            connection.close()
        second = quote(item_id="124", url="https://item.jd.com/124.html")
        with patch.object(guest, "get_guest_item", side_effect=[receipt(quote(price="80")), receipt(second)]):
            result = refresh.refresh_offers([quote(), second], store_path=self.path, as_of=NOW)
        self.assertEqual(result["storage"]["status"], "error")
        self.assertEqual(result["storage"]["inserted"], 0)
        self.assertEqual(len(refresh.history(self.path)), 1)
        self.assertEqual(len(result["items"]), 2)


if __name__ == "__main__":
    unittest.main()
