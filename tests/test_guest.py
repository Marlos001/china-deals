"""Synthetic, minimal schemas, not claims of live marketplace accessibility."""

import http.client
import io
import json
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from email.message import Message
from unittest.mock import Mock, patch

from china_deals import adapters, guest
from china_deals.models import normalize_offer

JD_ID = "100214660452"
JD_URL = f"https://item.jd.com/{JD_ID}.html"
JD_MOBILE = f"https://item.m.jd.com/product/{JD_ID}.html"
BLIBLI_URL = "https://www.blibli.com/p/synthetic/ps--SYN-00001-00001"


def index_html(href=JD_URL, title="Synthetic ROG &amp; laptop", snippet="Indexed ¥9,999, not current"):
    return (f'<h2><a class="result__a" href="{href}">{title}</a></h2>'
            f'<a class="result__snippet"><b>{snippet}</b></a>')


def jd_html(price="1??99", sku=JD_ID, floor_sku=None, trailing=False):
    # Minimal synthetic equivalent of the observed JSON wrapper and masked price.
    data = {"product": {"skuId": sku, "skuName": "Synthetic U9 285H 32G 1T RTX5060",
                        "color": "white", "recommendations": "must not enter description"},
            "priceFloor": {"price": price}}
    if floor_sku is not None:
        data["priceFloor"]["skuId"] = floor_sku
    text = json.dumps(data)
    if trailing:
        text = text[:-1] + ",}"
    return f"<script>window._itemInfo = ({text});</script>"


class IndexTests(unittest.TestCase):
    def search(self, body, **kwargs):
        with patch.object(guest, "_fetch", return_value=(body, "https://html.duckduckgo.com/html/?q=synthetic")):
            return guest.search_guest("jd", "synthetic", **kwargs)

    def test_index_unwrap_html_text_and_never_rank_index_prices(self):
        target = JD_URL + "?tracking=x#sku"
        wrapped = "//duckduckgo.com/l/?" + urllib.parse.urlencode({"uddg": target, "rut": "x"})
        result = self.search(index_html(wrapped), filters={"min_price": 100, "sort": "price"})
        self.assertEqual(result["status"], "discovery_only")
        row = result["items"][0]
        self.assertEqual(row["url"], JD_URL)
        self.assertEqual(row["nativeURL"], JD_URL)
        self.assertEqual(row["title"], "Synthetic ROG & laptop")
        self.assertIn("9,999", row["snippet"])
        self.assertIsNone(row["price"])
        self.assertEqual(row["source_mode"], "search_index")
        self.assertEqual(row["coverage"], "discovery_only")
        self.assertIn("discovered_at", row)
        self.assertIn("index_source_url", row)
        self.assertIsNone(normalize_offer("jd", row)["price"]["amount"])
        self.assertEqual(result["native_filters"]["requested"], {"min_price": 100, "sort": "price"})
        self.assertEqual(result["native_filters"]["applied"], {})
        self.assertEqual(result["native_filters"]["residual"], result["native_filters"]["requested"])
        self.assertEqual(result["native_filters"]["status"], "not_applied")
        self.assertFalse(result["access"]["authenticated"])

    def test_query_escaping_page_one_dedup_and_limit(self):
        query = 'ROG & x=1 # / 汉字 site:evil.test'
        body = index_html() + index_html(JD_URL + "?x=1") + index_html("https://item.jd.com/2.html")
        with patch.object(guest, "_fetch", return_value=(body, "https://html.duckduckgo.com/html/")) as fetch:
            result = guest.search_guest("jd", query, limit=1)
        self.assertEqual(len(result["items"]), 1)
        url = urllib.parse.urlsplit(fetch.call_args.args[0])
        self.assertEqual(urllib.parse.parse_qs(url.query), {"q": ["site:item.jd.com " + query]})
        self.assertEqual(fetch.call_count, 1)

    def test_rejects_unrelated_hosts_and_non_product_routes(self):
        bad = ["https://item.jd.com.evil.test/1.html", "https://evil.test/1.html",
               "https://item.jd.com@evil.test/1.html", "https://item.jd.com:443/1.html",
               "https://item.jd.com/catalog/1.html", "https://search.jd.com/Search?keyword=x",
               "http://item.jd.com/1.html", "javascript:alert(1)",
               "https://item.jd.com/%31.html", "https://item.jd.com/1.html/extra",
               "https://item.jd.com\\@evil.test/1.html"]
        for url in bad:
            with self.subTest(url=url):
                result = self.search(index_html(url))
                self.assertEqual(result["items"], [])
                self.assertEqual(result["status"], "empty_unverified")

    def test_each_marketplace_uses_exact_product_routes(self):
        good = {"jd": "https://item.m.jd.com/product/123.html?x=1",
                "taobao": "https://item.taobao.com/item.htm?id=123&spm=x",
                "goofish": "https://www.goofish.com/item?id=123&categoryId=1",
                "blibli": BLIBLI_URL + "?tracking=x"}
        for marketplace, url in good.items():
            with self.subTest(marketplace=marketplace):
                self.assertIsNotNone(guest._product_url(marketplace, url))
        for url in ("https://www.goofish.com/search?id=123", "https://www.goofish.com/item?id=1&id=2"):
            self.assertIsNone(guest._product_url("goofish", url))
        self.assertIsNone(guest._product_url("taobao", "https://www.taobao.com/item.htm?id=123"))
        self.assertIsNone(guest._product_url("blibli", "https://www.blibli.com/p/%2E%2E/ps--123"))

    def test_empty_parse_and_challenge_are_distinct(self):
        for body, status, code in [('<div class="no-results">No results</div>', "empty_unverified", "index_no_results"),
                                   ("<html>Unknown changed page</html>", "unavailable", "index_parse_error"),
                                   ('<form id="challenge-form">Verify you are human</form>', "blocked", "challenge")]:
            with self.subTest(code=code):
                result = self.search(body)
                self.assertEqual((result["status"], result["error"]["code"]), (status, code))
                self.assertEqual(result["items"], [])

    def test_incidental_captcha_word_in_index_text_is_not_a_gate(self):
        result = self.search(index_html(snippet="Seller notes mention CAPTCHA software"))
        self.assertEqual(result["status"], "discovery_only")
        self.assertEqual(self.search('<title>CAPTCHA verification</title>')["status"], "blocked")

    def test_no_opencli_and_no_retry_on_denial(self):
        for code in (403, 429):
            with self.subTest(code=code), patch.object(guest, "_fetch", side_effect=adapters._Failure("blocked", f"http_{code}", "denied")) as fetch, patch.object(adapters, "_version") as version:
                result = guest.search_guest("jd", "ROG")
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(fetch.call_count, 1)
            version.assert_not_called()

    def test_blibli_reuses_endpoint_schema_then_separate_index_on_denial(self):
        product = {"name": "Synthetic", "price": {"priceDisplay": "Rp1.000"}, "url": BLIBLI_URL}
        payload = json.dumps({"code": 200, "data": {"products": [product]}})
        with patch.object(guest, "_fetch", return_value=(payload, "https://www.blibli.com/backend/search/products")) as fetch:
            result = guest.search_guest("blibli", "a & b", filters={"sort": "price"})
        self.assertEqual(result["items"], [product])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["native_filters"]["applied"], {})
        self.assertIn("searchTerm=a+%26+b&start=0&itemPerPage=10", fetch.call_args.args[0])
        denial = adapters._Failure("blocked", "http_403", "Denied")
        with patch.object(guest, "_fetch", side_effect=[denial, (index_html(BLIBLI_URL), "https://html.duckduckgo.com/html/")]) as fetch:
            result = guest.search_guest("blibli", "a")
        self.assertEqual(result["status"], "discovery_only")
        self.assertIsNone(result["items"][0]["price"])
        self.assertEqual(fetch.call_count, 2)
        self.assertEqual([a["status"] for a in result["access"]["attempts"]], ["blocked", "ok"])


class DetailTests(unittest.TestCase):
    def detail(self, body, item_id=JD_ID, final_url=JD_MOBILE):
        with patch.object(guest, "_fetch", return_value=(body, final_url)):
            return guest.get_guest_item("jd", item_id)

    def test_jd_masked_title_selected_fields_and_trailing_comma(self):
        result = self.detail(jd_html(trailing=True))
        self.assertEqual(result["status"], "ok")
        row = result["items"][0]
        self.assertIsNone(row["price"])
        self.assertEqual(row["currency"], "CNY")
        self.assertEqual(row["title"], "Synthetic U9 285H 32G 1T RTX5060")
        self.assertEqual(row["detail"]["priceFloor"]["price"], "1??99")
        self.assertNotIn("recommendations", row["detail"]["product"])
        self.assertNotIn("must not enter", row["description"])
        self.assertEqual(row["source_mode"], "guest_product_page")
        self.assertEqual(row["url"], JD_URL)
        self.assertIn("observed_at", row)

    def test_only_unambiguous_sku_bound_price(self):
        for value, expected in [("9999.00", "9999.00"), (9999, "9999"), ("1??99", None),
                                ("¥9999", None), ("9999-19999", None), ("9,999", None),
                                ("9999起", None), ("1**99", None), (True, None), (None, None),
                                ("NaN", None), ("0", None), ("1e4", None)]:
            with self.subTest(value=value):
                self.assertEqual(self.detail(jd_html(price=value))["items"][0]["price"], expected)
        self.assertIsNone(self.detail(jd_html(price="9999", floor_sku="999"))["items"][0]["price"])

    def test_jd_exact_sku_binding_and_url_binding(self):
        for sku in ("999", JD_ID + "0", None):
            result = self.detail(jd_html(sku=sku))
            self.assertEqual(result["status"], "unavailable")
            self.assertEqual(result["error"]["code"], "item_schema_unverified")
        result = self.detail(jd_html(), final_url="https://item.m.jd.com/product/999.html")
        self.assertEqual(result["error"]["code"], "item_url_mismatch")

    def test_jd_no_eval_or_ambiguous_assignments(self):
        for body in ("<script>window._itemInfo = evil();</script>",
                     '<script>window._itemInfo = {"product": getProduct()};</script>',
                     jd_html() + jd_html(price="9999"),
                     '<script>window._itemInfo = {"product":{},"product":{}};</script>'):
            with self.subTest(body=body[:70]):
                self.assertEqual(self.detail(body)["error"]["code"], "item_schema_unverified")
        decoded = guest._decode_assignment('{"text":"comma,} and \\\" brace }",}')
        self.assertEqual(decoded["text"], 'comma,} and " brace }')
        for text in ('{"a":NaN}', '{"a":Infinity}', '{"a":1,"a":2}', '{"a": /*comment*/ 1}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                guest._decode_assignment(text)

    def test_other_china_details_explicitly_unavailable_without_fetch(self):
        with patch.object(guest, "_fetch") as fetch:
            for marketplace in ("taobao", "goofish"):
                result = guest.get_guest_item(marketplace, "123")
                self.assertEqual(result["status"], "unavailable")
                self.assertIn("product_url", result)
        fetch.assert_not_called()

    def test_blibli_only_url_bound_product_offer_jsonld(self):
        product = {"@type": "Product", "name": "Synthetic", "url": BLIBLI_URL,
                   "offers": {"@type": "Offer", "price": "100000", "priceCurrency": "IDR"}}
        def detail(value):
            body = '<script type="application/ld+json">' + json.dumps(value) + '</script>'
            with patch.object(guest, "_fetch", return_value=(body, BLIBLI_URL)):
                return guest.get_guest_item("blibli", BLIBLI_URL)
        self.assertEqual(detail({"@graph": [product]})["items"][0]["price"], "100000")
        for changes in ({"url": BLIBLI_URL + "-other"}, {"offers": {"@type": "AggregateOffer", "lowPrice": 100}},
                        {"offers": {"@type": "Offer", "url": BLIBLI_URL + "-other", "price": "100", "priceCurrency": "IDR"}}):
            self.assertEqual(detail(product | changes)["status"], "unavailable")
        self.assertEqual(detail([product, product])["status"], "unavailable")
        wrong_currency = product | {"offers": {"@type": "Offer", "price": "100", "priceCurrency": "CNY"}}
        self.assertIsNone(detail(wrong_currency)["items"][0]["price"])


class TransportTests(unittest.TestCase):
    @staticmethod
    def response(body=b"hello", url=JD_MOBILE):
        response = io.BytesIO(body)
        response.headers = Message()
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        response.geturl = lambda: url
        return response

    def test_cookie_free_opener_bounded_response_and_no_global_urlopen(self):
        opener = Mock()
        opener.open.return_value = self.response()
        with patch.object(guest.urllib.request, "build_opener", return_value=opener) as build, patch.object(guest.urllib.request, "urlopen") as global_open:
            body, _ = guest._fetch(JD_MOBILE, {"item.m.jd.com"}, time.monotonic() + 30)
        self.assertEqual(body, "hello")
        request = opener.open.call_args.args[0]
        self.assertIsNone(request.get_header("Cookie"))
        self.assertIsNone(request.get_header("Authorization"))
        self.assertEqual(len(build.call_args.args), 1)
        self.assertIsInstance(build.call_args.args[0], guest._Redirects)
        global_open.assert_not_called()
        opener.open.return_value = self.response(b"x" * 17)
        with patch.object(guest, "MAX_RESPONSE_BYTES", 16), patch.object(guest.urllib.request, "build_opener", return_value=opener):
            with self.assertRaises(adapters._Failure) as failure:
                guest._fetch(JD_MOBILE, {"item.m.jd.com"}, time.monotonic() + 30)
        self.assertEqual(failure.exception.code, "output_limit")

    def test_http_and_network_failures_are_not_retried(self):
        for code, status in ((401, "auth_required"), (403, "blocked"), (429, "blocked"), (503, "unavailable")):
            error = urllib.error.HTTPError(JD_MOBILE, code, "private", {}, io.BytesIO())
            opener = Mock()
            opener.open.side_effect = error
            with self.subTest(code=code), patch.object(guest.urllib.request, "build_opener", return_value=opener):
                result = guest.get_guest_item("jd", JD_ID)
            self.assertEqual(result["status"], status)
            self.assertEqual(result["error"]["code"], f"http_{code}")
            self.assertEqual(opener.open.call_count, 1)
            self.assertNotIn("private", json.dumps(result))
        opener.open.side_effect = urllib.error.URLError("private")
        with patch.object(guest.urllib.request, "build_opener", return_value=opener):
            self.assertEqual(guest.get_guest_item("jd", JD_ID)["error"]["code"], "network_error")

    def test_transport_truncation_and_final_host_fail_closed(self):
        opener = Mock()
        response = self.response(url="https://evil.test/product")
        opener.open.return_value = response
        with patch.object(guest.urllib.request, "build_opener", return_value=opener):
            self.assertEqual(guest.get_guest_item("jd", JD_ID)["error"]["code"], "redirect_denied")
        response = self.response()
        response.read1 = Mock(side_effect=http.client.IncompleteRead(b"partial"))
        opener.open.return_value = response
        with patch.object(guest.urllib.request, "build_opener", return_value=opener):
            self.assertEqual(guest.get_guest_item("jd", JD_ID)["error"]["code"], "network_error")

    def test_mid_read_total_deadline_is_enforced(self):
        opener = Mock()
        opener.open.return_value = self.response()
        with patch.object(guest.urllib.request, "build_opener", return_value=opener), patch.object(guest.adapters, "_remaining", side_effect=[10, 9, adapters._Failure("unavailable", "timeout", "timed out")]):
            result = guest.get_guest_item("jd", JD_ID)
        self.assertEqual(result["error"]["code"], "timeout")

    def test_redirects_restrict_hosts_schemes_credentials_and_login(self):
        handler = guest._Redirects({"item.m.jd.com"}, time.monotonic() + 30)
        request = urllib.request.Request(JD_MOBILE)
        for url in ("https://evil.test/", "https://passport.jd.com/login", "http://item.m.jd.com/",
                    "https://item.m.jd.com:443/", "https://item.m.jd.com@evil.test/", "https://item.m.jd.com/login"):
            with self.subTest(url=url), self.assertRaises(adapters._Failure):
                handler.redirect_request(request, None, 302, "Found", {}, url)
        redirected = handler.redirect_request(request, None, 302, "Found", {}, JD_MOBILE + "?x=1")
        self.assertEqual(redirected.full_url, JD_MOBILE + "?x=1")
        self.assertLessEqual(request.timeout, 30)

    def test_deadline_and_validation(self):
        with self.assertRaises(adapters._Failure):
            guest._fetch(JD_MOBILE, {"item.m.jd.com"}, time.monotonic() - 1)
        for kwargs in ({"limit": 0}, {"limit": True}, {"timeout": 0}, {"timeout": float("nan")}, {"filters": []}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                guest.search_guest("jd", "x", **kwargs)
        for item_id in ("１２３", "1/2", "https://evil.test", "123?x=1"):
            with self.subTest(item_id=item_id), self.assertRaises(ValueError):
                guest.get_guest_item("jd", item_id)


if __name__ == "__main__":
    unittest.main()
