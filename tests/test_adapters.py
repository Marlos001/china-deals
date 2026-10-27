"""Boundary tests with synthetic responses; none claims a live marketplace hit."""

import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from china_deals import adapters


class SubprocessTests(unittest.TestCase):
    def test_literal_arguments_and_both_pipes(self):
        query = "--help; $(touch /tmp/should-never-exist) `id` 中文"
        code, output = adapters._run(
            [sys.executable, "-c", "import json,sys;sys.stderr.write('private cookie');print(json.dumps(sys.argv[1:]))", query], 3,
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output), [query])
        self.assertNotIn(b"private cookie", output)

    def test_timeout_kills_and_reaps_process(self):
        start = time.monotonic()
        processes = []
        original_popen = subprocess.Popen

        def capture(*args, **kwargs):
            process = original_popen(*args, **kwargs)
            processes.append(process)
            return process

        with patch.object(adapters.subprocess, "Popen", side_effect=capture):
            with self.assertRaises(adapters._Failure) as caught:
                adapters._run([sys.executable, "-c", "import time;time.sleep(30)"], 0.1)
        self.assertEqual(caught.exception.code, "timeout")
        self.assertLess(time.monotonic() - start, 3)
        self.assertIsNotNone(processes[0].returncode)

    def test_timeout_also_covers_process_with_closed_pipes(self):
        with self.assertRaises(adapters._Failure) as caught:
            adapters._run([sys.executable, "-c", "import os,time;os.close(1);os.close(2);time.sleep(30)"], 0.1)
        self.assertEqual(caught.exception.code, "timeout")

    def test_output_limit_includes_stderr(self):
        with patch.object(adapters, "MAX_OUTPUT_BYTES", 1024):
            with self.assertRaises(adapters._Failure) as caught:
                adapters._run([sys.executable, "-c", "import sys;sys.stdout.write('x'*600);sys.stdout.flush();sys.stderr.write('x'*600)"], 3)
        self.assertEqual(caught.exception.code, "output_limit")

    def test_missing_executable_is_structured(self):
        result = adapters.search_marketplace("jd", "keyboard", executable="/no/such/opencli")
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["error"]["code"], "executable_unavailable")

    @unittest.skipUnless(os.name == "posix", "POSIX executable fixture")
    def test_public_boundary_version_and_safe_argv(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "opencli"
            executable.write_text(
                f"#!{sys.executable}\n"
                "import json,sys\n"
                "if sys.argv[1:] == ['--version']: print('2.0.2')\n"
                "else: print(json.dumps({'ok':True,'data':[{'title':'raw','argv':sys.argv[1:]}]}))\n",
                encoding="utf-8",
            )
            executable.chmod(0o700)
            query = "--help; $(id) 中文"
            result = adapters.search_marketplace("goofish", query, executable=str(executable))
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["items"][0]["argv"], ["xianyu", "search", "--limit", "10", "--format", "json", "--", query])


class OpenCliTests(unittest.TestCase):
    @staticmethod
    def wire(payload, code=0):
        return code, json.dumps(payload, ensure_ascii=False).encode()

    def search(self, payload, code=0, marketplace="jd"):
        with patch.object(adapters, "_version", return_value="2.0.2"), patch.object(adapters, "_run", return_value=self.wire(payload, code)):
            return adapters.search_marketplace(marketplace, "键盘")

    def test_preserves_raw_search_rows(self):
        rows = [{"sku": "123", "title": "键盘", "price": "¥199.99", "shop": "unverified shop"}]
        result = self.search({"ok": True, "data": rows})
        self.assertEqual(result["items"], rows)
        self.assertEqual(result["status"], "ok")
        self.assertIn("weak", " ".join(result["warnings"]))

    def test_empty_jd_is_not_verified_zero(self):
        result = self.search({"ok": True, "data": []})
        self.assertEqual(result["status"], "empty_unverified")
        self.assertEqual(result["items"], [])

    def test_error_taxonomy_and_no_private_message_echo(self):
        cases = [
            ("AUTH_REQUIRED", "requires login", "", "auth_required"),
            ("EMPTY_RESULT", "returned no data", "May need to log in", "empty_unverified"),
            ("EMPTY_RESULT", "returned no data", "blocked by verification or risk control", "blocked"),
            ("COMMAND_EXEC", "Xianyu verification page", "", "blocked"),
            ("BROWSER_CONNECT", "extension disconnected", "", "unavailable"),
            ("LOGIN_WALL", "HTML instead of JSON", "", "blocked"),
            ("SELECTOR", "missing element", "", "error"),
        ]
        for code, message, hint, expected in cases:
            with self.subTest(code=code, hint=hint):
                result = self.search({"ok": False, "error": {"code": code, "message": message + " cookie=PRIVATE", "hint": hint}}, 1)
                self.assertEqual(result["status"], expected)
                self.assertEqual(result["items"], [])
                self.assertNotIn("PRIVATE", json.dumps(result))

    def test_rejects_bad_wire_shapes_and_nonzero_success(self):
        for payload in ([], {"items": []}, {"ok": 1, "data": []}, {"ok": True}, {"ok": False, "error": "oops"}, {"ok": True, "data": {}}, {"ok": True, "data": [1]}):
            with self.subTest(payload=payload):
                self.assertEqual(self.search(payload)["status"], "error")
        self.assertEqual(self.search({"ok": True, "data": [{"title": "x"}]}, 1)["error"]["code"], "exit_status")

    def test_invalid_json_and_nonfinite_numbers(self):
        for output in (b"notice\n{\"ok\":true,\"data\":[]}", b"{truncated", b"{\"ok\":true,\"data\":[NaN]}", b"\xff"):
            with self.subTest(output=output), patch.object(adapters, "_version"), patch.object(adapters, "_run", return_value=(0, output)):
                self.assertEqual(adapters.search_marketplace("jd", "x")["error"]["code"], "invalid_json")

    def test_decimal_numbers_are_strings(self):
        self.assertEqual(adapters._loads(b'{"price":1.234567890123456789}')["price"], "1.234567890123456789")

    def test_detail_keeps_field_value_table_and_command_names(self):
        rows = [{"field": "商品名称", "value": "键盘"}, {"field": "价格", "value": "¥10"}]
        for marketplace, site, command in (("taobao", "taobao", "detail"), ("jd", "jd", "detail"), ("goofish", "xianyu", "item")):
            with self.subTest(marketplace=marketplace), patch.object(adapters, "_version"), patch.object(adapters, "_wire", return_value=rows) as run:
                result = adapters.get_item(marketplace, "123456")
                self.assertEqual(result["items"], rows)
                self.assertEqual(run.call_args.args[0], ["opencli", site, command, "123456", "--format", "json"])

    def test_jd_detail_login_or_incomplete_is_not_offer(self):
        cases = [
            ([{"field": "商品名称", "value": "京东登录"}, {"field": "链接", "value": "https://passport.jd.com/new/login.aspx"}], "auth_required"),
            ([{"field": "商品名称", "value": "安全验证"}], "blocked"),
            ([{"field": "商品名称", "value": "京东"}, {"field": "SKU", "value": "123"}], "empty_unverified"),
        ]
        for rows, expected in cases:
            with self.subTest(rows=rows), patch.object(adapters, "_version"), patch.object(adapters, "_wire", return_value=rows):
                self.assertEqual(adapters.get_item("jd", "123")["status"], expected)

    def test_upstream_limits_are_disclosed(self):
        with patch.object(adapters, "_version"), patch.object(adapters, "_wire", return_value=[]) as run:
            result = adapters.search_marketplace("jd", "x", limit=100)
        self.assertEqual(run.call_args.args[0][4], "30")
        self.assertTrue(any("capped" in warning for warning in result["warnings"]))

    def test_input_validation_before_side_effects(self):
        cases = [(("bilibili", "x"), {}), (("jd", ""), {}), (("jd", "x\0"), {}), (("jd", "x"), {"limit": True}), (("jd", "x"), {"limit": 0}), (("jd", "x"), {"timeout": float("nan")}), (("jd", "x"), {"timeout": -1}), (("jd", "x"), {"executable": ""}), (("jd", "x"), {"browser_fallback": 1})]
        with patch.object(adapters, "_run") as run:
            for args, kwargs in cases:
                with self.subTest(args=args, kwargs=kwargs), self.assertRaises(ValueError):
                    adapters.search_marketplace(*args, **kwargs)
            with self.assertRaises(ValueError):
                adapters.get_item("goofish", "123;id")
            run.assert_not_called()


class BlibliTests(unittest.TestCase):
    @staticmethod
    def response(payload, content_type="application/json"):
        response = io.BytesIO(json.dumps(payload).encode())
        response.headers = {"Content-Type": content_type}
        return response

    def test_real_endpoint_contract_parsing_is_synthetic(self):
        product = {"id": "SYN-00001-00001", "name": "Synthetic fixture", "price": {"minPrice": "100000"}, "url": "/p/synthetic/ps--SYN-00001-00001"}
        with patch.object(adapters.urllib.request, "urlopen", return_value=self.response({"code": 200, "status": "OK", "data": {"products": [product]}})) as open_url:
            result = adapters.search_marketplace("blibli", "a & b", limit=3)
        self.assertEqual(result["items"], [product])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(open_url.call_args.args[0].full_url, "https://www.blibli.com/backend/search/products?searchTerm=a+%26+b&start=0&itemPerPage=3")
        self.assertTrue(any("IDR" in w for w in result["warnings"]))

    def test_http_failures_never_become_zero_results(self):
        for code, expected in ((401, "auth_required"), (403, "blocked"), (429, "blocked"), (503, "unavailable")):
            error = urllib.error.HTTPError("https://www.blibli.com", code, "private server message", {}, io.BytesIO())
            with self.subTest(code=code), patch.object(adapters.urllib.request, "urlopen", side_effect=error):
                result = adapters.search_marketplace("blibli", "x")
            self.assertEqual(result["status"], expected)
            self.assertEqual(result["error"]["code"], f"http_{code}")

    def test_html_and_missing_products_do_not_prove_empty(self):
        for payload, content_type, expected in (({}, "text/html", "blocked"), ({"code": 200, "data": {}}, "application/json", "error"), ({"code": 403}, "application/json", "blocked"), ({"code": 200, "data": {"products": []}}, "application/json", "empty_unverified")):
            with self.subTest(payload=payload), patch.object(adapters.urllib.request, "urlopen", return_value=self.response(payload, content_type)):
                self.assertEqual(adapters.search_marketplace("blibli", "x")["status"], expected)

    def test_network_and_output_limit(self):
        with patch.object(adapters.urllib.request, "urlopen", side_effect=urllib.error.URLError("PRIVATE")):
            result = adapters.search_marketplace("blibli", "x")
        self.assertEqual(result["status"], "unavailable")
        self.assertNotIn("PRIVATE", json.dumps(result))
        with patch.object(adapters, "MAX_OUTPUT_BYTES", 10), patch.object(adapters.urllib.request, "urlopen", return_value=self.response({"code": 200, "data": {"products": []}})):
            self.assertEqual(adapters.search_marketplace("blibli", "x")["error"]["code"], "output_limit")

    def test_browser_is_opt_in_and_direct_block_survives_missing_bridge(self):
        blocked = adapters._Failure("blocked", "http_403", "Blocked")
        with patch.object(adapters, "_blibli_http", side_effect=blocked), patch.object(adapters, "_blibli_browser", side_effect=adapters._Failure("unavailable", "BROWSER_CONNECT", "No bridge")) as browser:
            self.assertEqual(adapters.search_marketplace("blibli", "x")["status"], "blocked")
            browser.assert_not_called()
            result = adapters.search_marketplace("blibli", "x", browser_fallback=True)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("BROWSER_CONNECT" in warning for warning in result["warnings"]))

    def test_detail_rejects_non_native_urls_and_does_not_guess_sku_route(self):
        for url in ("SKU-00001-00001", "https://evil.test/p/x/ps--123", "https://www.blibli.com@evil.test/p/x/ps--123", "http://www.blibli.com/p/x/ps--123", "https://www.blibli.com/p/../ps--123", "https://www.blibli.com/p/%2E%2E/ps--123", "https://www.blibli.com/p/%2Fadmin/ps--123"):
            with self.subTest(url=url), patch.object(adapters, "_run") as run:
                result = adapters.get_item("blibli", url, browser_fallback=True)
                self.assertEqual(result["error"]["code"], "detail_url_required")
                run.assert_not_called()

    def test_browser_session_placement_cleanup_and_jsonld_identity_binding(self):
        url = "https://www.blibli.com/p/synthetic/ps--SYN-00001-00001"
        related = {"@type": "Product", "url": "https://www.blibli.com/p/other/ps--SYN-00001-00002", "name": "Other"}
        product = {"@type": "Product", "url": url, "name": "Synthetic fixture", "offers": {"price": "100000", "priceCurrency": "IDR"}}
        with patch.object(adapters, "_version"), patch.object(adapters, "_wire", side_effect=[{"targetId": "synthetic"}, {"state": "ok", "products": [related, product]}, None]) as wire:
            result = adapters.get_item("blibli", url, browser_fallback=True)
        self.assertEqual(result["items"], [product])
        calls = [c.args[0] for c in wire.call_args_list]
        self.assertEqual([c[:3] for c in calls], [["opencli", "browser", "--session"]] * 3)
        self.assertEqual(len({c[3] for c in calls}), 1)
        self.assertEqual([c[4] for c in calls], ["open", "eval", "close"])
        self.assertIn("application/ld+json", calls[1][5])

    def test_browser_challenge_is_not_bypassed_and_cleanup_failure_is_disclosed(self):
        blocked = adapters._Failure("blocked", "http_403", "Blocked")
        with patch.object(adapters, "_blibli_http", side_effect=blocked), patch.object(adapters, "_version"), patch.object(adapters, "_wire", side_effect=[{}, {"state": "blocked"}, adapters._Failure("unavailable", "timeout", "Timeout")]) as wire:
            result = adapters.search_marketplace("blibli", "x", browser_fallback=True)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(wire.call_count, 3)
        self.assertIn("verifikasi sedang", wire.call_args_list[1].args[0][5])
        self.assertTrue(any("close is best effort" in w for w in result["warnings"]))
        self.assertTrue(any("close failed (timeout)" in w for w in result["warnings"]))

    def test_variant_urls_are_supported_without_guessing(self):
        url = "https://www.blibli.com/p/synthetic/is--SYN-00001-00001-00001?utm_source=fixture"
        self.assertEqual(adapters._blibli_product_url(url), url.split("?")[0])


class DoctorTests(unittest.TestCase):
    def test_default_is_version_only(self):
        with patch.object(adapters, "_run", return_value=(0, b"2.0.2\n")) as run:
            result = adapters.doctor()
        self.assertEqual(result["status"], "ok")
        self.assertFalse(result["live_checked"])
        run.assert_called_once_with(["opencli", "--version"], 10)

    def test_version_mismatch_refuses_marketplace_execution(self):
        with patch.object(adapters, "_run", return_value=(0, b"2.0.3\n")) as run:
            result = adapters.search_marketplace("taobao", "x")
        self.assertEqual(result["error"]["code"], "version_mismatch")
        self.assertEqual(run.call_count, 1)

    def test_live_bridge_is_explicit_and_does_not_echo_profiles(self):
        report = {"daemonRunning": True, "extensionConnected": False, "profiles": ["PRIVATE"]}
        with patch.object(adapters, "_version", return_value="2.0.2"), patch.object(adapters, "_wire", return_value=report) as wire:
            result = adapters.doctor(live=True)
        self.assertTrue(result["live_checked"])
        self.assertEqual(result["status"], "unavailable")
        self.assertNotIn("PRIVATE", json.dumps(result))
        wire.assert_called_once_with(["opencli", "doctor"], 30)


if __name__ == "__main__":
    unittest.main()
