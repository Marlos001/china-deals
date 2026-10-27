"""Offline boundary tests. Stubs are not evidence of live site accessibility."""

import builtins
import json
import sys
import time
import types
import unittest
from contextlib import contextmanager
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

from china_deals import browser_guest as bg

JD_URL = "https://item.jd.com/123456.html"
GOOFISH_URL = "https://www.goofish.com/item?id=985148706040"


class Page:
    def __init__(self, url, cards=None, text="", title="Results", html="", status=200):
        self.url, self.cards, self.text, self.title = url, cards or [], text, title
        self.html, self.status, self.closed = html, status, False

    def route(self, pattern, handler):
        self.guard = handler

    def goto(self, url, **kwargs):
        self.requested_url = url
        if self.url == "SEARCH":
            self.url = url
        return types.SimpleNamespace(status=self.status)

    def evaluate(self, script):
        if script == bg._STATE_JS:
            return {"title": self.title, "text": self.text, "verification": False}
        if script == bg._CARDS_JS:
            return self.cards
        from china_deals.goofish_public import CAPTURE_JS
        if script == CAPTURE_JS:
            return {"url": self.url, "title": self.title, "capturedAt": "2026-10-27T16:29:23Z", "mainHtml": self.html}
        raise AssertionError("Unexpected browser script")

    def wait_for_function(self, script, **kwargs):
        pass

    def content(self):
        return self.html

    def close(self):
        self.closed = True


class Context:
    def __init__(self, pages):
        self.pages, self.used, self.closed = list(pages), [], False

    def new_page(self):
        page = self.pages.pop(0)
        self.used.append(page)
        return page

    def close(self):
        self.closed = True


@contextmanager
def session(context):
    try:
        yield context
    finally:
        context.close()


class BrowserSearchTests(unittest.TestCase):
    def search(self, pages, market="jd", query="幻16 Air", **kwargs):
        context = Context(pages)
        with patch.object(bg, "_browser_context", return_value=session(context)):
            result = bg.search_browser_guest(market, query, **kwargs)
        self.assertTrue(context.closed)
        self.assertTrue(all(p.closed for p in context.used))
        return result

    def test_native_cards_preserve_query_and_null_prices(self):
        page = Page("SEARCH", cards=[{"title": "幻16 Air", "href": JD_URL + "?tracking=1",
                                      "snippet": "Indexed ¥9,999; not a current offer"}])
        result = self.search([page], query="  幻16 Air  ", filters={"min_price": 20}, limit=100)
        self.assertEqual(result["query"], "  幻16 Air  ")
        self.assertEqual(parse_qs(urlsplit(page.requested_url).query)["q"], ["site:item.jd.com 幻16 Air"])
        self.assertEqual(result["status"], "discovery_only")
        row = result["items"][0]
        self.assertIsNone(row["price"])
        self.assertEqual(row["nativeURL"], JD_URL)
        self.assertEqual(row["source_mode"], "search_index")
        self.assertEqual(row["price_basis"], "indexed_text_only")
        self.assertIn("9,999", row["snippet"])
        self.assertEqual(result["native_filters"]["applied"], {})
        self.assertEqual(result["native_filters"]["residual"], {"min_price": 20})
        self.assertTrue(result["warnings"])

    def test_each_marketplace_uses_native_url_validator(self):
        urls = {"jd": JD_URL, "taobao": "https://item.taobao.com/item.htm?id=123456",
                "goofish": GOOFISH_URL, "blibli": "https://www.blibli.com/p/synthetic/ps--SYN-00001-00001"}
        for market, url in urls.items():
            with self.subTest(market=market):
                result = self.search([Page("SEARCH", [{"title": "Synthetic", "href": url}])], market=market)
                self.assertEqual(result["items"][0]["nativeURL"], url)

    def test_malformed_unrelated_and_duplicate_cards(self):
        cards = [{"title": "Synthetic", "href": value} for value in (
            "https://item.jd.com.attacker.test/123456.html", "https://item.jd.com/search",
            "http://item.jd.com/123456.html", "https://user@item.jd.com/123456.html",
            "https://www.google.com/goto?url=opaque", JD_URL, JD_URL + "?tracking=2")]
        cards[4]["href"] = "https://google.com.attacker.test/goto?url=opaque"
        result = self.search([Page("SEARCH", cards)])
        self.assertEqual(len(result["items"]), 1)

    def test_opaque_google_wrapper_ordinary_navigation_only(self):
        opaque = "https://www.google.com/goto?url=encrypted-not-decoded"
        target = Page(JD_URL)
        result = self.search([Page("SEARCH", [{"title": "Synthetic", "href": opaque}]), target])
        self.assertEqual(target.requested_url, opaque)
        self.assertEqual(result["items"][0]["nativeURL"], JD_URL)
        self.assertEqual(len(result["access"]["attempts"]), 2)

    def test_unresolved_wrapper_is_not_a_product(self):
        opaque = "https://www.google.com/goto?url=opaque"
        result = self.search([Page("SEARCH", [{"title": "Synthetic", "href": opaque}]), Page(opaque)])
        self.assertEqual(result["status"], "empty_unverified")
        self.assertEqual(result["items"], [])

    def test_challenge_stops_without_following_results(self):
        page = Page("SEARCH", [{"title": "Synthetic", "href": JD_URL}], text="Our systems have detected unusual traffic")
        result = self.search([page])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["error"]["code"], "challenge")
        self.assertEqual(len(result["access"]["attempts"]), 1)
        self.assertEqual(result["items"], [])

    def test_redirect_challenge_removes_partial_leads(self):
        cards = [{"title": "First", "href": JD_URL},
                 {"title": "Next", "href": "https://www.google.com/url?q=opaque"}]
        result = self.search([Page("SEARCH", cards), Page("https://www.google.com/sorry/index")])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["items"], [])

    def test_http_429_no_retry(self):
        result = self.search([Page("SEARCH", status=429)])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(len(result["access"]["attempts"]), 1)

    def test_empty_does_not_claim_native_inventory(self):
        result = self.search([Page("SEARCH", text="No results found")])
        self.assertEqual(result["status"], "empty_unverified")

    def test_argument_validation_before_browser(self):
        for kwargs in ({"limit": True}, {"limit": 0}, {"timeout": float("nan")}, {"filters": []}):
            with self.subTest(kwargs=kwargs), patch.object(bg, "_browser_context") as browser:
                with self.assertRaises(ValueError):
                    bg.search_browser_guest("jd", "幻16", **kwargs)
                browser.assert_not_called()


class NavigationTests(unittest.TestCase):
    def route(self, guard, url, navigation=True):
        frame = types.SimpleNamespace()
        frame.page = types.SimpleNamespace(main_frame=frame)
        request = types.SimpleNamespace(url=url, frame=frame, is_navigation_request=lambda: navigation)
        route = Mock(request=request)
        guard.handle(route)
        return route

    def test_one_hop_and_final_host_boundary(self):
        initial = "https://www.google.com/goto?url=opaque"
        guard = bg._Navigation("jd", initial)
        self.route(guard, initial).continue_.assert_called_once()
        self.route(guard, JD_URL).continue_.assert_called_once()
        self.route(guard, "https://item.jd.com/987654.html").abort.assert_called_once()
        self.assertEqual(guard.failure.code, "redirect_denied")

    def test_unrelated_destination_login_and_detail_identity(self):
        for target, code in (("https://attacker.test/", "redirect_denied"),
                             ("https://passport.jd.com/login", "challenge"),
                             ("https://item.jd.com/987654.html", "redirect_denied")):
            with self.subTest(target=target):
                guard = bg._Navigation("jd", JD_URL, JD_URL)
                self.route(guard, JD_URL)
                self.route(guard, target).abort.assert_called_once()
                self.assertEqual(guard.failure.code, code)

    def test_subresources_are_not_rewritten(self):
        guard = bg._Navigation("jd", JD_URL)
        self.route(guard, "https://static.example/image.jpg", navigation=False).continue_.assert_called_once()
        self.assertFalse(guard.started)

    def test_google_can_add_metadata_without_changing_query(self):
        initial = "https://www.google.com/search?q=site%3Aitem.jd.com+%E5%B9%BB16"
        guard = bg._Navigation("jd", initial)
        self.route(guard, initial)
        self.route(guard, initial + "&sei=synthetic").continue_.assert_called_once()
        self.assertIsNone(guard.failure)
        changed = bg._Navigation("jd", initial)
        self.route(changed, initial)
        self.route(changed, "https://www.google.com/search?q=unrelated").abort.assert_called_once()
        self.assertEqual(changed.failure.code, "redirect_denied")


class DetailTests(unittest.TestCase):
    def read(self, page, market, value):
        context = Context([page])
        with patch.object(bg, "_browser_context", return_value=session(context)):
            result = bg.get_browser_guest_item(market, value)
        self.assertTrue(context.closed)
        self.assertTrue(page.closed)
        return result

    def test_goofish_does_not_invent_primary_price_from_recommendations(self):
        page = Page(GOOFISH_URL, text="已下架 ¥7999 推荐 ¥1", html="<div>已下架 ¥7999 推荐 ¥1</div>")
        result = self.read(page, "goofish", "985148706040")
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["error"]["code"], "item_schema_unverified")
        self.assertEqual(result["items"], [])

    def test_goofish_illegal_access_is_blocked(self):
        result = self.read(Page(GOOFISH_URL, text="非法访问 请使用正常浏览器访问闲鱼"), "goofish", GOOFISH_URL)
        self.assertEqual(result["status"], "blocked")

    def test_jd_exact_sku_bound_schema_only(self):
        for sku, status in (("123456", "ok"), ("987654", "unavailable")):
            data = {"product": {"skuId": sku, "skuName": "Synthetic primary item"}, "priceFloor": {"price": "1??99"}}
            page = Page(JD_URL, html=f"<script>window._itemInfo = {json.dumps(data)};</script>")
            result = self.read(page, "jd", JD_URL)
            self.assertEqual(result["status"], status)
            if status == "ok":
                self.assertIsNone(result["items"][0]["price"])

    def test_detail_url_mismatch_rejected(self):
        result = self.read(Page("https://item.jd.com/987654.html"), "jd", JD_URL)
        self.assertEqual(result["error"]["code"], "item_url_mismatch")

    def test_untrusted_input_never_launches(self):
        with patch.object(bg, "_browser_context") as browser:
            result = bg.get_browser_guest_item("goofish", "https://www.goofish.com.attacker.test/item?id=1")
        self.assertEqual(result["error"]["code"], "detail_url_required")
        browser.assert_not_called()


class OptionalDependencyTests(unittest.TestCase):
    def test_missing_dependency_structured_unavailable(self):
        original = builtins.__import__

        def import_without_playwright(name, *args, **kwargs):
            if name.startswith("playwright"):
                raise ImportError("not installed")
            return original(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=import_without_playwright):
            result = bg.search_browser_guest("jd", "幻16")
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["error"]["code"], "dependency_missing")

    def test_incognito_context_and_cleanup_on_failure(self):
        class BrowserError(Exception):
            pass

        class BrowserTimeout(BrowserError):
            pass

        manager, playwright, browser, context = Mock(), Mock(), Mock(), Mock()
        manager.__enter__ = Mock(return_value=playwright)
        manager.__exit__ = Mock(return_value=False)
        playwright.chromium.launch.return_value = browser
        browser.new_context.return_value = context
        module = types.ModuleType("playwright.sync_api")
        module.Error, module.TimeoutError = BrowserError, BrowserTimeout
        module.sync_playwright = Mock(return_value=manager)
        with patch.dict(sys.modules, {"playwright.sync_api": module}):
            with self.assertRaises(bg._Failure):
                with bg._browser_context(None, time.monotonic() + 5):
                    raise bg._Failure("blocked", "challenge", "stop")
        browser.new_context.assert_called_once_with(accept_downloads=False)
        options = playwright.chromium.launch.call_args.kwargs
        self.assertEqual(options["executable_path"], "/usr/bin/chromium")
        self.assertTrue(options["chromium_sandbox"])
        self.assertNotIn("args", options)
        self.assertNotIn("storage_state", browser.new_context.call_args.kwargs)
        context.close.assert_called_once()
        browser.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
