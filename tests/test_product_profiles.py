"""Offline literal relevance cases, not evidence of authenticity or live stock."""

import json
import unittest
from unittest.mock import patch

from china_deals.product_profiles import (
    assess_profile,
    explicit_identity_families,
    identify_family,
    profile_queries,
)


class ProductProfileTests(unittest.TestCase):
    def test_direct_requested_exclusions_do_not_cross_unrelated_exclusions(self):
        cases = [("RTX 5070", "RTX 5070 without GPU"),
                 ("RTX 5070", "RTX 5070 不含显卡"),
                 ("Ryzen 9800X3D", "Ryzen 9800X3D tanpa CPU"),
                 ("Steam Deck OLED", "not Steam Deck OLED"),
                 ("Nintendo Switch 2", "Nintendo Switch 2 没有游戏机")]
        for query, title in cases:
            with self.subTest(title=title):
                self.check(query, title, "mismatch")
        for query, title in [("RTX 5070", "RTX 5070 without cooler"),
                             ("Ryzen 9800X3D", "Ryzen 9800X3D tanpa motherboard"),
                             ("Steam Deck OLED", "Steam Deck OLED 不含充电器")]:
            with self.subTest(title=title):
                self.check(query, title)
        self.check("RTX 5070", "RTX 5070", "mismatch", variant="no graphics card")

    def check(self, query, title, status="match", variant="", **extra):
        offer = {"title": title, "variant": variant, **extra}
        original = dict(offer)
        result = assess_profile(offer, query)
        self.assertEqual(result["status"], status, (query, offer, result))
        self.assertEqual(result["family"], identify_family(query))
        self.assertEqual(result["match_basis"], "title_and_selected_variant")
        self.assertEqual(result["price_scope_warnings"], [])
        self.assertTrue(result["reasons"])
        self.assertEqual(offer, original)
        return result

    def test_family_and_verbatim_queries(self):
        for family, query in (
            ("steam-deck", "Steam Deck OLED 1TB limited edition dock only"),
            ("sony-wh", "Sony WH-1000XM6 ear pads silver 2025"),
            ("sony-wh", "SonyWH1000XM6"),
            ("amd-ryzen-cpu", "AMD Ryzen 7 9800X3D tray no cooler"),
            ("amd-ryzen-cpu", "锐龙9800X3D 散片"),
            ("nvidia-rtx-gpu", "RTX5070Ti 16GB white OC"),
            ("nvidia-rtx-gpu", "5070 Ti water block only"),
            ("dji-mini", "大疆Mini4Pro 带屏遥控器"),
            ("nintendo-switch", "Nintendo Switch 2 joycon only Japan edition"),
        ):
            with self.subTest(query=query):
                self.assertEqual(identify_family(query), family)
                chinese, blibli = profile_queries(query)
                self.assertEqual(blibli, [query])
                self.assertEqual(len(chinese), 1)
                self.assertTrue(chinese[0].endswith(query))
                self.assertTrue(any("\u3400" <= c <= "\u9fff" for c in chinese[0]))
        for query in ("desk lamp", "iPhone 17 Pro Max", "Sony WF-1000XM5", "RTX 15070 Ti",
                      "Steam Decker", "WH1000XM6XL", "DJI Miniature", "Ryzenologist"):
            with self.subTest(query=query):
                # RTX identifies a family but the invalid number must not establish a model.
                if query != "RTX 15070 Ti":
                    self.assertIsNone(identify_family(query))
                    self.assertEqual(profile_queries(query), ([], []))
        self.assertIsNone(identify_family("Steam Deck and Nintendo Switch 2"))
        with self.assertRaises(ValueError):
            identify_family(None)

    def test_reported_false_positives(self):
        self.check("Sony WH-1000XM6", "Replacement ear pads for Sony WH-1000XM6", "mismatch")
        self.check("Steam Deck OLED", "Steam Deck OLED docking station USB-C", "mismatch")
        self.check("RTX 5070 Ti", "MSI GeForce RTX 5070 12GB graphics card", "mismatch")

    def test_realistic_positive_listings(self):
        for query, title in (
            ("Steam Deck OLED 1TB", "Valve Steam Deck OLED 1 TB handheld console"),
            ("Sony WH-1000XM6", "索尼 WH-1000XM6 无线降噪耳机 黑色"),
            ("AMD Ryzen 9800X3D", "AMD Ryzen 7 9800X3D AM5 tray processor"),
            ("RTX 5070 Ti", "ZOTAC GAMING GeForce RTX 5070 Ti SOLID OC 16GB GDDR7"),
            ("DJI Mini 4 Pro", "大疆 Mini4Pro 无人机 畅飞套装"),
            ("Nintendo Switch 2", "任天堂 Nintendo Switch 2 console Japan edition"),
        ):
            with self.subTest(query=query):
                self.check(query, title)
                self.check(query, title, variant="Black / Hitam")

    def test_selected_model_independent_of_title(self):
        for query, bad, good in (
            ("Steam Deck OLED 512GB", "LCD 512GB", "OLED 512GB"),
            ("Sony WH-1000XM6", "XM5", "XM6"),
            ("AMD Ryzen 9800X3D", "7800X3D", "9800X3D"),
            ("RTX 5070 Ti", "5070", "5070 Ti"),
            ("DJI Mini 4 Pro", "3 Pro", "4 Pro"),
            ("Nintendo Switch 2", "OLED", "2"),
        ):
            with self.subTest(query=query):
                result = self.check(query, query, "mismatch", bad)
                self.assertIn("selected_variant", " ".join(result["reasons"]))
                self.check(query, query, variant=good)
                self.check(query, query, variant="white")

    def test_device_revisions_and_model_boundaries(self):
        for query, title, status in (
            ("Sony WH-1000XM6", "Sony WH-1000XM5 headphones", "mismatch"),
            ("Sony WH-1000XM6", "Sony WF-1000XM6 earbuds", "mismatch"),
            ("Sony WH-1000XM6", "Sony WH-1000XM60", "mismatch"),
            ("Sony WH-1000XM6", "Sony WH-1000XM6XL", "uncertain"),
            ("Sony WH-1000XM6", "Sony WH-1000 headphones", "uncertain"),
            ("AMD Ryzen 9800X3D", "AMD Ryzen 9800X", "mismatch"),
            ("AMD Ryzen 9800X3D", "AMD Ryzen 9800", "uncertain"),
            ("AMD Ryzen 9800X3D", "AMD Ryzen 19800X3D", "uncertain"),
            ("AMD Ryzen 9800X3D", "AMD Ryzen 9800X3DX", "uncertain"),
            ("RTX 5070 Ti", "GeForce RTX 5070 Ti SUPER", "mismatch"),
            ("RTX 5070", "RTX 5070 Super", "mismatch"),
            ("RTX 5070 Ti", "RTX 5070 Titanium", "mismatch"),
            ("RTX 5070 Ti", "RTX 15070 Ti", "uncertain"),
            ("DJI Mini 4 Pro", "DJI Mini 3 Pro", "mismatch"),
            ("DJI Mini 4 Pro", "DJI Mini 4", "uncertain"),
            ("DJI Mini 4 Pro", "DJI Mini 4 SE", "mismatch"),
            ("Nintendo Switch 2", "Nintendo Switch OLED", "mismatch"),
            ("Nintendo Switch 2", "Nintendo Switch original V1", "mismatch"),
            ("Nintendo Switch 2", "Nintendo Switch", "uncertain"),
            ("Nintendo Switch 2", "Nintendo Switch 20", "uncertain"),
            ("Steam Deck OLED", "Valve Steam Deck LCD", "mismatch"),
            ("Steam Deck OLED", "Valve Steam Deck", "uncertain"),
        ):
            with self.subTest(query=query, title=title):
                self.check(query, title, status)

    def test_explicit_capacity_only_and_independent_conflicts(self):
        query = "Steam Deck OLED 1TB"
        for title, variant, status in (
            ("Steam Deck OLED 1024GB", "", "match"),
            ("SteamDeckOLED 1.0 TB", "", "match"),
            ("Steam Deck OLED", "1TB white", "match"),
            ("Steam Deck OLED 512GB", "1TB", "mismatch"),
            ("Steam Deck OLED 1TB", "512GB", "mismatch"),
            ("Steam Deck OLED 512GB / 1TB", "", "uncertain"),
            ("Steam Deck OLED 512GB / 1TB", "1TB", "match"),
            ("Steam Deck OLED", "1024", "uncertain"),
            ("Steam Deck OLED", "1T", "uncertain"),
            ("Steam Deck OLED 1000GB", "", "mismatch"),
            ("Steam Deck OLED 1TB", "1TB / 512GB", "uncertain"),
        ):
            with self.subTest(title=title, variant=variant):
                self.check(query, title, status, variant)
        self.check("RTX 5070 Ti 16GB", "RTX 5070 Ti 16 GB GDDR7", variant="white")
        self.check("Sony WH-1000XM6", "Sony WH-1000XM6 2025")

    def test_ambiguous_models_need_unambiguous_selection(self):
        for query, title, selected in (
            ("Sony WH-1000XM6", "Sony WH-1000XM5 / WH-1000XM6", "XM6"),
            ("AMD Ryzen 9800X3D", "AMD Ryzen 7800X3D / 9800X3D", "9800X3D"),
            ("RTX 5070 Ti", "RTX 5070 / RTX 5070 Ti", "5070 Ti"),
            ("DJI Mini 4 Pro", "DJI Mini 3 Pro / Mini 4 Pro", "4 Pro"),
            ("Nintendo Switch 2", "Nintendo Switch OLED / Switch 2", "2"),
        ):
            with self.subTest(query=query):
                self.check(query, title, "uncertain")
                self.check(query, title, variant=selected)
                self.check(query, query, "uncertain", title)
        self.check("DJI Mini 4 Pro", "DJI Mini 4 Pro", "uncertain", "Mini 4")
        self.check("AMD Ryzen 9800X3D", "AMD Ryzen 9800X3D", "uncertain", "9800")
        self.check("AMD Ryzen 9800X3D", "AMD Ryzen 9800X3D", "mismatch", "X")
        self.check("RTX 5070 Ti", "RTX 5070 Ti", "mismatch", "Super")
        self.check("Nintendo Switch 2", "Nintendo Switch 2", "mismatch", "Switch 1")

    def test_accessory_language_and_intent(self):
        for query, accessory in (
            ("Steam Deck OLED", "dock"), ("Steam Deck OLED", "扩展坞"),
            ("Steam Deck OLED", "sarung"), ("Steam Deck OLED", "charger"),
            ("Sony WH-1000XM6", "bantalan"), ("Sony WH-1000XM6", "耳垫"),
            ("Sony WH-1000XM6", "ear cushions"),
            ("AMD Ryzen 9800X3D", "散热器"), ("AMD Ryzen 9800X3D", "cooler"),
            ("RTX 5070 Ti", "water block"), ("RTX 5070 Ti", "支架"),
            ("DJI Mini 4 Pro", "controller"), ("DJI Mini 4 Pro", "遥控器"),
            ("DJI Mini 4 Pro", "baterai"), ("DJI Mini 4 Pro", "RC-N2"),
            ("Nintendo Switch 2", "joycon"), ("Nintendo Switch 2", "game cartridge"),
            ("Nintendo Switch 2", "卡带"), ("Nintendo Switch 2", "kaset"),
        ):
            with self.subTest(query=query, accessory=accessory):
                self.check(query, f"{accessory} for {query}", "mismatch")
                self.check(query, query + " with free case", "mismatch", accessory + " only")
                result = self.check(f"{accessory} for {query}", f"{accessory} for {query}")
                self.assertEqual(result["listing_kind"], "accessory")
                self.check(f"{accessory} for {query}", query, "uncertain")

    def test_bundle_positive_and_selected_accessory_negative(self):
        for query in ("Steam Deck OLED", "Sony WH-1000XM6", "AMD Ryzen 9800X3D",
                      "RTX 5070 Ti", "DJI Mini 4 Pro", "Nintendo Switch 2"):
            with self.subTest(query=query):
                for suffix in ("with free case", "includes case", "赠送保护套", "bonus tas"):
                    self.check(query, query + " " + suffix)
                for variant in ("case only", "casing saja", "保护套 单卖"):
                    self.check(query, query + " with free case", "mismatch", variant)
        self.check("Steam Deck OLED dock", "Steam Deck OLED case", "mismatch")

    def test_compatibility_preserves_accessory_role_in_all_profiles(self):
        for query, accessory in (
            ("Steam Deck OLED", "dock"),
            ("Sony WH-1000XM6", "replacement ear pads"),
            ("AMD Ryzen 9800X3D", "cooler"),
            ("RTX 5070 Ti", "water block"),
            ("DJI Mini 4 Pro", "propellers"),
            ("Nintendo Switch 2", "joycon"),
        ):
            for compatibility in ("Compatible with", "COMPATIBLE  WITH", "compatible\nwith"):
                with self.subTest(query=query, compatibility=compatibility):
                    title = f"{compatibility} {query} {accessory}"
                    result = self.check(query, title, "mismatch")
                    self.assertEqual(result["listing_kind"], "accessory_or_non_product")
                    self.check(query, query + " with free case", "mismatch", title)
                    self.check(f"{accessory} for {query}", title)

    def test_other_family_identity_conflicts_in_either_observation(self):
        for query, other in (
            ("Steam Deck OLED", "Nintendo Switch 2"),
            ("Nintendo Switch 2", "Steam Deck OLED"),
            ("RTX 5070 Ti", "AMD Radeon RX 9070 XT 16GB"),
            ("RTX 5070 Ti", "Intel Arc B580 12GB"),
            ("Sony WH-1000XM6", "AirPods Max USB-C"),
            ("AMD Ryzen 9800X3D", "Intel Core i9 14900K Desktop Processor"),
            ("AMD Ryzen 9800X3D", "Core Ultra 9 285K"),
            ("DJI Mini 4 Pro", "DJI Mavic 3 Pro"),
        ):
            with self.subTest(query=query, other=other):
                for title, variant, source in ((query, other, "selected_variant"),
                                               (other, query, "title")):
                    result = self.check(query, title, "mismatch", variant)
                    self.assertIn(f"{source}: different_explicit_product_family", result["reasons"])
                self.check(query, query, "mismatch", query + " / " + other)
                self.check(query, query, variant="Black / used, complete")

    def test_other_family_checks_require_bounded_identity(self):
        for variant in ("Intel blue", "AMD red", "Core collection", "airpodsmaximus",
                        "Radeonian", "Switchboard", "Nintendo Switchboard"):
            with self.subTest(variant=variant):
                self.check("Sony WH-1000XM6", "Sony WH-1000XM6", variant=variant)

    def test_independent_selected_observations_resolve_axes(self):
        result = assess_profile({"title": "Steam Deck LCD / OLED 512GB / 1TB"},
                                "Steam Deck OLED 1TB",
                                selected_observations=["Black", "OLED", "1TB"])
        self.assertEqual(result["status"], "match", result)
        title = "Sony WH-1000XM5 / WH-1000XM6"
        for observations in (["Black", "XM6"], ["XM6", "Black"]):
            result = assess_profile({"title": title}, "Sony WH-1000XM6",
                                    selected_observations=observations)
            self.assertEqual(result["status"], "match", result)
        for observations, status in (
            (["Black"], "uncertain"),
            (["XM6", "XM5"], "mismatch"),
            (["XM6", "XM5 / XM6"], "uncertain"),
            (["XM6 with free case", "ear pads only"], "mismatch"),
            (["XM6 with free case", "AirPods Max USB-C"], "mismatch"),
        ):
            with self.subTest(observations=observations):
                result = assess_profile({"title": title}, "Sony WH-1000XM6",
                                        selected_observations=observations)
                self.assertEqual(result["status"], status, result)
        for query, partial in (("AMD Ryzen 9800X3D", "9800"),
                               ("DJI Mini 4 Pro", "Mini 4")):
            result = assess_profile({"title": query}, query,
                                    selected_observations=["Black", partial])
            self.assertEqual(result["status"], "uncertain", result)

    def test_independent_observations_contract_replaces_variant(self):
        offer = {"title": "Sony WH-1000XM6", "variant": "XM5"}
        result = assess_profile(offer, "Sony WH-1000XM6", selected_observations=["XM6"])
        self.assertEqual(result["status"], "match", result)
        self.assertEqual(offer["variant"], "XM5")
        for invalid in ("XM6", [{"model": "XM6"}]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                assess_profile(offer, "Sony WH-1000XM6", selected_observations=invalid)

    def test_advertised_model_suffix_pairs_cannot_cross(self):
        for query, title, selection in (
            ("AMD Ryzen 9900X3D", "AMD Ryzen 9900X / Ryzen 9800X3D", "9900X3D"),
            ("DJI Mini 4 Pro", "DJI Mini 4 / Mini 3 Pro", "Mini 4 Pro"),
        ):
            with self.subTest(query=query):
                for advertised in (title, " / ".join(reversed(title.split(" / ")))):
                    result = assess_profile({"title": advertised, "variant": selection}, query)
                    self.assertNotEqual(result["status"], "match", result)
                result = assess_profile({"title": query, "variant": title}, query)
                self.assertNotEqual(result["status"], "match", result)
        for query, title, selected in (
            ("AMD Ryzen 9900X3D", "AMD Ryzen 9900X / Ryzen 9800X3D", ["9900", "X3D"]),
            ("DJI Mini 4 Pro", "DJI Mini 4 / Mini 3 Pro", ["Mini 4", "Pro"]),
        ):
            result = assess_profile({"title": title}, query, selected_observations=selected)
            self.assertNotEqual(result["status"], "match", result)

    def test_independent_model_suffix_fields_still_combine(self):
        for query, title, model, suffix in (
            ("AMD Ryzen 9800X3D", "AMD Ryzen 9900X / Ryzen 9800X3D", "9800", "X3D"),
            ("AMD Ryzen 9800X3D", "AMD Ryzen 9800X / Ryzen 9800X3D", "9800", "X3D"),
            ("DJI Mini 4 Pro", "DJI Mini 3 / Mini 4 Pro", "Mini 4", "Pro"),
            ("DJI Mini 4 Pro", "DJI Mini 4 SE / Mini 4 Pro", "Mini 4", "Pro"),
        ):
            for observations in ([model, suffix], [suffix, "Black", model]):
                with self.subTest(query=query, observations=observations):
                    result = assess_profile({"title": title}, query,
                                            selected_observations=observations)
                    self.assertEqual(result["status"], "match", result)
            for observations in ([model], [model, suffix, "SE" if suffix == "Pro" else "X"]):
                result = assess_profile({"title": title}, query,
                                        selected_observations=observations)
                self.assertNotEqual(result["status"], "match", result)

    def test_deck_ram_and_storage_are_separate_literal_axes(self):
        for specification in ("16GB RAM 1TB SSD", "RAM 16GB SSD 1TB",
                              "16GB RAM 1TB", "RAM: 16GB storage: 1TB"):
            with self.subTest(specification=specification):
                title = "Valve Steam Deck OLED " + specification
                self.check("Steam Deck OLED 1TB", title)
                self.check("Steam Deck OLED " + specification, title)
        query = "Steam Deck OLED 16GB RAM 1TB SSD"
        for title, variant, expected in (
            ("Steam Deck OLED 16GB RAM 512GB SSD", "", "mismatch"),
            ("Steam Deck OLED 32GB RAM 1TB SSD", "", "mismatch"),
            ("Steam Deck OLED 1TB SSD", "", "uncertain"),
            ("Steam Deck OLED 16GB RAM", "", "uncertain"),
            ("Steam Deck OLED 16GB 1TB", "", "uncertain"),
            (query, "32GB RAM", "mismatch"),
            (query, "512GB SSD", "mismatch"),
            ("Steam Deck OLED 16GB RAM 512GB / 1TB SSD", "", "uncertain"),
            ("Steam Deck OLED 16GB RAM 512GB / 1TB SSD", "1TB SSD", "match"),
        ):
            with self.subTest(title=title, variant=variant):
                self.check(query, title, expected, variant)
        self.check("Steam Deck OLED 1TB", "Steam Deck OLED 1TB RAM", "uncertain")
        self.check("Steam Deck OLED 1TB", "Steam Deck OLED 16GB RAM", "uncertain")
        self.check("Steam Deck OLED 1TB", "Steam Deck OLED", "uncertain", "1024")
        for observations, expected in (
            (["16GB RAM", "1TB SSD"], "match"),
            (["1TB SSD", "16GB RAM", "Black"], "match"),
            (["16GB RAM", "32GB RAM", "1TB SSD"], "mismatch"),
            (["16GB RAM", "1TB SSD", "512GB SSD"], "mismatch"),
        ):
            result = assess_profile({"title": "Steam Deck OLED"}, query,
                                    selected_observations=observations)
            self.assertEqual(result["status"], expected, result)

    def test_explicit_identity_families_public_contract(self):
        for text, expected in (
            ("Nintendo Switch 2 / Steam Deck OLED", {"nintendo-switch", "steam-deck"}),
            ("iPhone 17 Pro Max", {"apple-iphone"}),
            ("AirPods Max", {"apple-airpods"}),
            ("ROG Zephyrus G16", {"rog-zephyrus"}),
            ("Sony WH-1000XM6", {"sony-wh"}),
            ("Black / used, complete", set()),
            ("Intel blue AMD red Core collection airpodsmaximus", set()),
            ("9800X3D 5070 Ti", set()),
        ):
            with self.subTest(text=text):
                result = explicit_identity_families(text)
                self.assertIsInstance(result, frozenset)
                self.assertEqual(result, expected)
        for invalid in (None, 123, {"model": "Steam Deck OLED"}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                explicit_identity_families(invalid)

    def test_tuple_and_typed_capacity_ranking_survive_json_roundtrips(self):
        from china_deals.ranking import rank_offers

        cases = (
            ("AMD Ryzen 9900X3D", "AMD Ryzen 9900X / Ryzen 9800X3D", "9900X3D", False),
            ("DJI Mini 4 Pro", "DJI Mini 4 / Mini 3 Pro", "Mini 4 Pro", False),
            ("Steam Deck OLED 1TB", "Valve Steam Deck OLED 16GB RAM 1TB SSD", "", True),
            ("Steam Deck OLED 16GB RAM 1TB SSD", "Steam Deck OLED 16GB RAM 1TB SSD", "", True),
            ("Steam Deck OLED 1TB", "Steam Deck OLED 16GB RAM 512GB SSD", "", False),
        )
        with patch("socket.socket", side_effect=AssertionError("offline test attempted network")):
            for query, title, selected, expected in cases:
                with self.subTest(query=query, title=title):
                    rows = [{"marketplace": "jd", "sku": "123", "title": title,
                             "selected_variant": selected, "price": "100",
                             "url": "https://item.jd.com/123.html"}]
                    for iteration in range(3):
                        result = rank_offers(rows, query=query if iteration == 0 else None)
                        self.assertEqual(bool(result["groups"]), expected, result)
                        rows = [row for group in result["groups"].values() for row in group]
                        rows += result["unranked"]
                        rows = json.loads(json.dumps(rows))

    def test_dji_and_cpu_refinements_survive_role_checks(self):
        query = "DJI Mini 4 Pro Fly More Combo RC2"
        self.check(query, "DJI Mini 4 Pro Fly More Combo with RC2 and free case")
        self.check(query, query, "mismatch", "RC-N2")
        self.check(query, query, "mismatch", "RC2 only")
        self.check(query, "RC2 controller for DJI Mini 4 Pro", "mismatch")
        self.check("AMD Ryzen 9800X3D boxed", "AMD Ryzen 9800X3D boxed with free case")
        self.check("AMD Ryzen 9800X3D boxed", "AMD Ryzen 9800X3D tray", "mismatch")

    def test_nonproduct_and_descriptions_cannot_establish_role(self):
        for query in ("Steam Deck OLED", "Sony WH-1000XM6", "AMD Ryzen 9800X3D",
                      "RTX 5070 Ti", "DJI Mini 4 Pro", "Nintendo Switch 2"):
            for label in ("repair service", "replica", "维修", "高仿", "servis", "replika"):
                with self.subTest(query=query, label=label):
                    self.check(query, query + " " + label, "mismatch")
                    self.check(query, query, "mismatch", label)
            self.check(query, "Special offer", "uncertain", description=query, source_summary=query)
            self.check(query, query, description="replica accessory repair")
            self.check(query, query + " no repairs")
        self.check("Steam Deck OLED dock", "Steam Deck OLED", "uncertain", description="dock only")

    def test_components_are_not_complete_computers_or_laptop_gpus(self):
        for wording in ("laptop GPU", "notebook", "mobile", "笔记本", "移动版", "gaming PC",
                        "complete computer", "prebuilt", "整机", "PC rakitan"):
            with self.subTest(wording=wording):
                self.check("RTX 5070 Ti", "RTX 5070 Ti " + wording, "mismatch")
                self.check("RTX 5070 Ti", "RTX 5070 Ti graphics card", "mismatch", wording)
        self.check("RTX 5070 laptop", "RTX 5070 desktop graphics card", "mismatch")
        self.check("RTX 5070 laptop", "RTX 5070 laptop GPU")
        self.check("RTX 5070 laptop", "RTX 5070", "uncertain")
        self.check("AMD Ryzen 9800X3D", "AMD Ryzen 9800X3D gaming PC", "mismatch")

    def test_contract_unsupported_and_transaction_scope_deferred(self):
        self.check("unknown lamp", "unknown lamp", "uncertain")
        self.check("Steam Deck OLED", "Steam Deck OLED monthly deposit", price=10)
        self.check("锐龙9800X3D", "AMD Ryzen 9800X3D")
        self.check("AMD Ryzen 9800 X3D", "AMD Ryzen 9800X3D")
        self.check("AMD Ryzen 9800 X3D", "AMD Ryzen 9800X", "mismatch")
        self.check("大疆Mini4Pro", "DJI Mini 4 Pro")
        self.check("Nintendo Switch OLED", "NintendoSwitchOLED")
        for qualifier in ("no cooler", "without cooler", "tanpa cooler", "不含散热器"):
            self.check("AMD Ryzen 9800X3D", "AMD Ryzen 9800X3D " + qualifier)


if __name__ == "__main__":
    unittest.main()
