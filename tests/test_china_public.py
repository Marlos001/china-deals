"""Offline fail-closed contracts. Synthetic fixtures do not prove live pricing."""

import copy
import hashlib
import json
import unittest
from html import escape
from pathlib import Path

from china_deals.china_public import parse_product_page
from china_deals.marketplaces import item_url
from china_deals.models import normalize_offer

FIXTURE = json.loads((Path(__file__).parent / "fixtures/china-public-synthetic.json").read_text())
OBSERVED = FIXTURE["observed_at"]
WEIDIAN = json.loads((Path(__file__).parent / "fixtures/china-public-weidian-retained.json").read_text())


def script(value):
    return '<script type="application/ld+json">' + json.dumps(value).replace("<", "\\u003c") + '</script>'


def html(*values, head="", body=""):
    return '<html><head>' + head + ''.join(script(v) for v in values) + '</head><body>' + body + '</body></html>'


def meta(key, value):
    return f'<meta property="{key}" content="{escape(value, quote=True)}">'


class ChinaPublicTests(unittest.TestCase):
    def setUp(self):
        self.case = copy.deepcopy(FIXTURE["cases"][0])
        self.product = self.case["product"]
        self.url = self.case["url"]

    def parse(self, body=None, url=None, observed_at=OBSERVED):
        return parse_product_page(body if body is not None else html(self.product), "tmall", url or self.url, observed_at)

    def assert_unpriced(self, row, market="tmall"):
        self.assertIsNone(row["price"])
        self.assertNotIn("offers", row)
        self.assertNotIn("selected_variant", row)
        normalized = normalize_offer(market, row, observed_at=OBSERVED)
        self.assertIsNone(normalized["price"]["amount"])
        self.assertIsNone(normalized["offers"])
        self.assertEqual(normalized["availability"], "unknown")
        self.assertEqual(normalized["source_detail"], row["source_detail"])
        self.assertIsNone(normalize_offer(market, normalized, observed_at=OBSERVED)["price"]["amount"])

    def test_all_new_market_fixtures_bind_identity_without_pricing(self):
        for case in FIXTURE["cases"]:
            with self.subTest(market=case["marketplace"]):
                body = html(case["product"])
                row = parse_product_page(body, case["marketplace"], case["url"], OBSERVED)
                self.assert_unpriced(row, case["marketplace"])
                self.assertEqual(row["url"], case["url"])
                self.assertEqual(row["observed_at"], OBSERVED)
                self.assertEqual(row["title"], case["product"]["name"])
                self.assertEqual(row["source_detail"]["response_text_sha256"], hashlib.sha256(body.encode()).hexdigest())
                self.assertIn("not_transport_bytes", row["source_detail"]["hash_basis"])

    def test_request_routes_and_marketplaces_are_exact(self):
        urls = [self.url.replace("https:", "http:"), self.url.replace("detail.tmall.com", "detail.tmall.com.evil.test"),
                self.url + "&id=123456789001", self.url + "&itemID=999", self.url.replace("123456789001", "１２３"),
                self.url.replace("/item.htm", "/search"), self.url.replace("detail.tmall.com", "user@detail.tmall.com"),
                self.url.replace("detail.tmall.com", "detail.tmall.com:443"), self.url + "\\x"]
        for url in urls:
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.parse(url=url)
        for market in ("taobao", "jd", "blibli", "TMALL", None, []):
            with self.subTest(market=market), self.assertRaises(ValueError):
                parse_product_page(html(self.product), market, self.url, OBSERVED)
        self.assertEqual(self.parse(url=self.url + "&spm=tracking#details")["url"], self.url)

    def test_id_or_url_conflict_is_not_rescued_by_metadata(self):
        for change in ({"productID": "999"}, {"productID": True}, {"productID": {"value": "123456789001"}},
                       {"@id": item_url("tmall", "999")}, {"url": item_url("tmall", "999")}, {"@id": "#unbound"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                product = dict(self.product, **change)
                self.parse(html(product, head=meta("og:url", self.url) + meta("og:type", "product") + meta("og:title", "Unrelated")))

    def test_product_id_alone_and_offer_url_do_not_bind_product(self):
        self.product.pop("url")
        self.product["offers"]["url"] = self.url
        with self.assertRaises(ValueError):
            self.parse()

    def test_bound_id_fragment_and_graph_are_supported(self):
        self.product["@id"] = self.product.pop("url") + "#product"
        row = self.parse(html({"@graph": [{"@type": "Organization", "name": "Test"}, self.product]}))
        self.assert_unpriced(row)
        self.assertEqual(row["item_id"], "123456789001")

    def test_recommendations_and_unrelated_script_prices_never_contaminate(self):
        recommendation = dict(self.product, url=item_url("tmall", "999"), productID="999", name="Accessory", offers={"price": "1"})
        self.product["isRelatedTo"] = recommendation
        row = self.parse(html(recommendation, self.product, {"price": "0.01"}))
        self.assert_unpriced(row)
        self.assertEqual(row["source_detail"]["provenance"]["script_index"], 1)
        self.assertEqual(row["source_detail"]["offer_claims"][0]["price"], "2999.00")
        self.assertNotIn("Accessory", json.dumps(row))
        with self.assertRaises(ValueError):
            self.parse(html({"@type": "ItemList", "itemListElement": [self.product]}))

    def test_webpage_main_entity_requires_bound_page_and_product(self):
        row = self.parse(html({"@type": "WebPage", "url": self.url, "mainEntity": self.product}))
        self.assert_unpriced(row)
        with self.assertRaises(ValueError):
            self.parse(html({"@type": "WebPage", "url": item_url("tmall", "999"), "mainEntity": self.product}))

    def test_multiple_scripts_or_graphs_with_matching_products_are_ambiguous(self):
        for body in (html(self.product, self.product), html([self.product, self.product]),
                     html({"@graph": [self.product]}, self.product)):
            with self.subTest(body=body), self.assertRaises(ValueError):
                self.parse(body)

    def test_malformed_later_script_cannot_be_silently_discarded(self):
        valid = script(self.product)
        for bad in ('{"@type":', '{"@type":"Product","@type":"Offer"}', '{"price":NaN}', '{"price":1e999}'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.parse(valid + '<script type="application/ld+json">' + bad + '</script>')
        with self.assertRaises(ValueError):
            self.parse(valid + '<script type="application/ld+json">{')

    def test_metadata_only_requires_explicit_product_head_and_page_identity(self):
        head = meta("og:type", "product") + meta("og:title", "Steam Deck OLED 掌机")
        identity = f'<link rel="canonical" href="{self.url}">'
        row = self.parse(html(head=head + identity + meta("product:price:amount", "1")))
        self.assert_unpriced(row)
        self.assertEqual(row["source_detail"]["provenance"]["kind"], "head_product_metadata")
        for body in (html(head=head), html(head=identity + meta("og:title", "Title")), html(body=head + identity),
                     html(head='<template>' + head + identity + '</template>'), html(head='<title>Product</title>')):
            with self.subTest(body=body), self.assertRaises(ValueError):
                self.parse(body)

    def test_conflicting_primary_metadata_rejects_even_valid_jsonld(self):
        for head in (meta("og:url", item_url("tmall", "999")), f'<link rel="canonical" href="{item_url("tmall", "999")}">',
                     meta("og:title", "A") + meta("og:title", "B"), '<meta property="og:url" content="x" content="y">'):
            with self.subTest(head=head), self.assertRaises(ValueError):
                self.parse(html(self.product, head=head))

    def test_prices_currencies_variants_deposits_and_wholesale_never_rank(self):
        offers = [
            {"@type": "Offer", "price": "1", "priceCurrency": "USD", "url": self.url},
            {"@type": "AggregateOffer", "lowPrice": "1", "highPrice": "999", "priceCurrency": "CNY"},
            {"@type": "Offer", "price": "999", "priceCurrency": "CNY", "url": item_url("tmall", "999")},
            {"@type": "Offer", "price": "100", "priceCurrency": "CNY", "eligibleQuantity": {"minValue": 20}},
            {"@type": "Offer", "price": "10", "priceCurrency": "CNY", "priceSpecification": {"name": "定金 分期", "price": "10", "priceCurrency": "USD"}},
            [{"price": "1", "priceCurrency": "CNY"}, {"price": "2", "priceCurrency": "USD"}],
        ]
        for offer in offers:
            with self.subTest(offer=offer):
                self.product["offers"] = offer
                self.product["hasVariant"] = [{"sku": "selected", "price": "1"}]
                self.assert_unpriced(self.parse(html(self.product, head=meta("product:price:currency", "USD") + meta("product:price:amount", "0.01"))))

    def test_truncation_is_rejected_for_identity_but_disclosed_for_claims(self):
        self.product["url"] = self.url + "x" * 10000
        with self.assertRaises(ValueError):
            self.parse()
        self.product["url"] = self.url
        self.product["name"] = "x" * 1001
        with self.assertRaises(ValueError):
            self.parse()
        self.product["name"] = "Product"
        self.product["offers"] = [{"price": "9" * 1000}] * 9
        row = self.parse()
        self.assert_unpriced(row)
        self.assertIn("offers", row["source_detail"]["claims_truncated"])
        self.assertIn("offers[0].price", row["source_detail"]["claims_truncated"])
        self.assertLessEqual(len(json.dumps(row["source_detail"])), 32768)

    def test_incomplete_html_and_resource_limits_fail_closed(self):
        for body in (html(self.product)[:-7], html(self.product) + '<meta', '<html><head>' + script(self.product),
                     'x' * (2 * 1024 * 1024 + 1), '字' * (1024 * 1024), html(self.product) + '\ufffd',
                     script(self.product) + script({}) * 64, html({"@graph": [{}] * 4097}),
                     '<script type="application/ld+json">' + '[' * 1100 + ']' * 1100 + '</script>'):
            with self.subTest(size=len(body)), self.assertRaises(ValueError):
                self.parse(body)

    def test_challenge_pages_do_not_return_metadata(self):
        for gate in ('<div id="captcha">Verify human</div>', '<title>登录</title>', '<title>Access denied</title>'):
            with self.subTest(gate=gate), self.assertRaises(ValueError):
                self.parse(html(self.product, head=gate))

    def test_no_clock_fallback_or_invalid_timestamp(self):
        for timestamp in (None, "", "2026-10-27", "2026-10-27T12:00:00", "now", 123):
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError):
                self.parse(observed_at=timestamp)

    def test_optional_html_attributes_and_invalid_product_fields(self):
        self.assert_unpriced(self.parse(html(self.product, body='<script type>var ignored = 1;</script>')))
        for change in ({"name": None}, {"description": []}, {"description": "x" * 8001}, {"url": [self.url]}):
            with self.subTest(change=list(change)), self.assertRaises(ValueError):
                self.parse(html(dict(self.product, **change)))
        with self.assertRaises(ValueError):
            self.parse(html(self.product, head='<meta property="og:url">'))


class WeidianNativeStateTests(unittest.TestCase):
    def setUp(self):
        self.state = copy.deepcopy(WEIDIAN["state"])
        self.item = self.state["result"]["default_model"]["item_info"]
        self.url = WEIDIAN["provenance"]["source_url"]

    def carrier(self, state=None, raw=None, extra=""):
        value = raw if raw is not None else json.dumps(self.state if state is None else state)
        return ('<script id="__rocker-render-inject__" data-obj="'
                + escape(value, quote=True) + '"' + extra + '></script>')

    def parse(self, carrier=None, url=None):
        return parse_product_page(html(body=self.carrier() if carrier is None else carrier),
                                  "weidian", url or self.url, WEIDIAN["provenance"]["observed_at"])

    def assert_unpriced(self, row, availability):
        self.assertEqual(row["availability"], availability)
        self.assertIsNone(row["price"])
        self.assertNotIn("selected_variant", row)
        self.assertNotIn("offers", row)
        for _ in range(3):
            self.assertIsNone(row.get("selected_variant"))
            self.assertFalse(row.get("offers"))
            row = normalize_offer("weidian", row, observed_at=OBSERVED)
            self.assertIsNone(row["price"]["amount"])
            self.assertEqual(row["availability"], availability)

    def test_retained_shape_preserves_delisting_and_unpriced_source_claims(self):
        row = self.parse()
        self.assertEqual(row["title"], "BALENCIAGA SIZE:S-XL  ")
        self.assertEqual(row["item_id"], "7287460067")
        self.assert_unpriced(row, "delisted")
        detail = row["source_detail"]
        self.assertEqual(detail["provenance"]["kind"], "weidian_native_state")
        claims = detail["native_state_claims"]
        self.assertEqual(claims["item_info"]["stock"], 8000)
        self.assertEqual(claims["item_info"]["itemLowPrice"], 24000)
        self.assertEqual(claims["item_info"]["origin_price"], "240")
        self.assertFalse(claims["item_info"]["flag"]["is_valid_item"])
        self.assertTrue(claims["item_info"]["flag"]["is_status_off_shelve"])
        self.assertEqual(len(claims["sku_properties"]["sku"]), 8)
        self.assertEqual(claims["sku_properties"]["sku"]["124315086893"]["price"], "240.00")
        self.assertEqual(claims["sku_properties"]["sku"]["124315086893"]["stock"], 1000)
        self.assertEqual(detail["offer_claims"], [])

    def test_observed_companion_src_requires_inline_state_and_is_inert(self):
        src = WEIDIAN["carrier_attributes"]["src"]
        row = self.parse(self.carrier(extra=f' crossorigin="anonymous" src="{src}"'))
        self.assert_unpriced(row, "delisted")
        self.assertEqual(row["source_detail"]["provenance"]["inert_companion_src"], src)
        self.assert_unpriced(self.parse(self.carrier(extra=' crossorigin="anonymous"')), "delisted")
        for carrier in (f'<script id="__rocker-render-inject__" src="{src}"></script>',
                        self.carrier(extra=f' src="{src}" src="{src}"'),
                        self.carrier(extra=f' src="{src}?different"'),
                        self.carrier(extra=f' src="https:{src}"')):
            with self.subTest(carrier=carrier[:100]), self.assertRaises(ValueError):
                self.parse(carrier)

    def test_primary_path_cannot_be_replaced_by_matching_sibling_or_recommendation(self):
        real = copy.deepcopy(self.item)
        self.item["item_id"] = "999"
        self.state["result"]["sibling"] = {"item_info": real}
        self.item["recommendations"] = [real]
        with self.assertRaises(ValueError):
            self.parse()
        del self.state["result"]["default_model"]["item_info"]
        with self.assertRaises(ValueError):
            self.parse()

    def test_recommendations_do_not_supply_any_claims(self):
        self.state["result"]["recommendations"] = [{"item_id": "999", "price": "RECOMMENDED_PRICE"}]
        self.state["result"]["default_model"]["sku_properties"]["sku"]["124315086893"]["recommendations"] = [
            {"price": "RECOMMENDED_PRICE"}]
        row = self.parse()
        self.assertNotIn("RECOMMENDED_PRICE", json.dumps(row))
        self.assert_unpriced(row, "delisted")

    def test_exact_url_id_and_market_are_required(self):
        for bad in (None, True, 7287460067.0, ["7287460067"], "7287460067x", "７２８７４６００６７"):
            with self.subTest(item_id=bad), self.assertRaises(ValueError):
                self.item["item_id"] = bad
                self.parse()
        self.item["item_id"] = 7287460067
        self.assert_unpriced(self.parse(), "delisted")
        for url in (item_url("weidian", "999"), self.url + "&itemID=7287460067", self.url.replace("https:", "http:")):
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.parse(url=url)
        with self.assertRaises(ValueError):
            parse_product_page(html(body=self.carrier()), "tmall", item_url("tmall", "7287460067"), OBSERVED)

    def test_malformed_duplicate_overflow_and_excessive_json_rejected(self):
        raw = json.dumps(self.state)
        bad_values = [raw[:-1], raw + '{}', raw.replace('"stock": 8000', '"stock": 1e999'),
                      raw.replace('"stock": 8000', '"stock": NaN'),
                      raw.replace('"stock": 8000', '"stock": 8000, "stock": 0'),
                      raw.replace('"item_id": "7287460067"', '"item_id":"999","item_id":"7287460067"'),
                      '{"status":{},"status":{}}', '[' * 1100 + ']' * 1100,
                      json.dumps(dict(self.state, ignored=[{}] * 4097)),
                      json.dumps(dict(self.state, ignored="x" * (256 * 1024))),
                      json.dumps(dict(self.state, ignored=[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[0]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]))]
        for bad in bad_values:
            with self.subTest(length=len(bad)), self.assertRaises(ValueError):
                self.parse(self.carrier(raw=bad))

    def test_carrier_duplicates_external_src_and_malformed_attributes_rejected(self):
        carrier = self.carrier()
        bad_values = [carrier * 2, carrier + self.carrier(raw="{"),
                      self.carrier(extra=' src="https://example.test/state.js"'),
                      self.carrier(extra=' src=""'), self.carrier(extra=' src'),
                      self.carrier(extra=' id="other"'), self.carrier(extra=' DATA-OBJ="{}"'),
                      self.carrier(extra=' junk'), self.carrier(extra=' type="application/ld+json"'),
                      carrier.replace('id="__rocker-render-inject__"', 'id=__rocker-render-inject__'),
                      carrier.replace(' data-obj=', 'data-obj='), carrier.replace('></script>', '/>'),
                      carrier.replace('</script>', 'alert(1)</script>'),
                      '<script id="__rocker-render-inject__"></script>',
                      '<div id="__rocker-render-inject__" data-obj="{}"></div>']
        for bad in bad_values:
            with self.subTest(carrier=bad[:90]), self.assertRaises(ValueError):
                self.parse(bad)

    def test_ignored_and_unclosed_contexts_cannot_supply_state(self):
        for tag in ("template", "noscript", "textarea", "title", "xmp", "iframe", "noembed", "noframes",
                    "svg", "math", "select", "plaintext"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                self.parse(f'<{tag}>' + self.carrier() + f'</{tag}>')
        for body in (self.carrier(), html(head=self.carrier()), html(body=self.carrier())[:-7],
                     html(body=self.carrier().replace('</script>', '')), html(body=self.carrier()) + '<script',
                     html(body='<plaintext></plaintext>' + self.carrier()),
                     html(body='<!-- ' + self.carrier() + ' -->'),
                     html(body='<style>' + self.carrier() + '</style>'),
                     html(body='</body><body>' + self.carrier())):
            with self.subTest(body=body[:80]), self.assertRaises(ValueError):
                parse_product_page(body, "weidian", self.url, OBSERVED)

    def test_jsonld_and_metadata_checks_are_not_bypassed(self):
        product = {"@type": "Product", "url": self.url, "name": "Other", "productID": "7287460067"}
        for body in (html(product, body=self.carrier()),
                     html(head='<script type="application/ld+json">{</script>', body=self.carrier()),
                     html(head=meta("og:url", item_url("weidian", "999")), body=self.carrier())):
            with self.subTest(body=body[:100]), self.assertRaises(ValueError):
                parse_product_page(body, "weidian", self.url, OBSERVED)

    def test_stock_and_sku_prices_never_resurrect_availability(self):
        self.item["flag"] = {"is_status_off_shelve": True, "is_valid_item": True}
        self.item["buyLimitInfo"] = {}
        self.item["itemSellable"] = True
        self.assert_unpriced(self.parse(), "delisted")
        self.item["flag"] = {"is_valid_item": False}
        self.assert_unpriced(self.parse(), "unavailable")
        self.item["flag"] = {"is_valid_item": True}
        self.assert_unpriced(self.parse(), "unknown")
        self.item["buyLimitInfo"] = {"buyButtonText": "商品已下架"}
        self.assert_unpriced(self.parse(), "delisted")

    def test_invalid_critical_fields_and_status_fail_closed(self):
        baseline = copy.deepcopy(self.item)
        for change in ({"item_name": "x" * 1001}, {"item_name": []}, {"itemShareDesc": "x" * 8001},
                       {"flag": []}, {"flag": {"is_status_off_shelve": "false"}}, {"itemSellable": 1},
                       {"buyLimitInfo": {"buyButtonText": "x" * 513}}):
            with self.subTest(change=list(change)), self.assertRaises(ValueError):
                self.state["result"]["default_model"]["item_info"] = dict(baseline, **change)
                self.parse()
        self.state["result"]["default_model"]["item_info"] = baseline
        for status in ({"code": True}, {"code": 1}, {"code": "0"}, [], None):
            with self.subTest(status=status), self.assertRaises(ValueError):
                self.state["status"] = status
                self.parse()

    def test_invalid_sku_shapes_fail_closed(self):
        for value in ([], {"sku": []}, {"sku": {"123": []}}, {"attr_list": {}},
                      {"attr_list": [[]]}, {"attr_list": [{"attr_values": {}}]},
                      {"attr_list": [{"attr_values": [1]}]}):
            with self.subTest(sku=value), self.assertRaises(ValueError):
                self.state["result"]["default_model"]["sku_properties"] = value
                self.parse()

    def test_auxiliary_claim_limits_are_disclosed(self):
        self.item["origin_price"] = "9" * 1000
        sku = self.state["result"]["default_model"]["sku_properties"]["sku"]
        sku.update({str(i): {"price": "1"} for i in range(20)})
        row = self.parse()
        self.assert_unpriced(row, "delisted")
        self.assertIn("native.item_info.origin_price", row["source_detail"]["claims_truncated"])
        self.assertIn("native.sku_properties.sku", row["source_detail"]["claims_truncated"])
        self.assertLessEqual(len(json.dumps(row["source_detail"])), 32768)


if __name__ == "__main__":
    unittest.main()
