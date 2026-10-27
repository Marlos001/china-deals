"""Offline regressions: sanitized selectors plus hash-bound private captures."""

import hashlib
import json
import unittest
from html import escape
from pathlib import Path

from china_deals.goofish_public import parse_capture
from china_deals.models import normalize_offer

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / 'tests/fixtures/goofish-diverse-sanitized.json').read_text())['cases']


def capture(description, attributes=None, title='商品', price='1000', status='立即购买'):
    labels = ''.join(f'<div>{escape(k)}：<span>{escape(v)}</span></div>'
                     for k, v in (attributes or {}).items())
    return {'url': 'https://www.goofish.com/item?id=123', 'title': title,
            'capturedAt': '2026-10-27T17:37:48.918Z',
            'mainHtml': '<div class="item-main-container--sanitized">'
            '<div class="item-main-info--sanitized"><div class="tips--sanitized">'
            f'<span>¥</span><span class="price--sanitized">{escape(price)}</span></div>'
            '<div class="notLoginContainer--sanitized">'
            f'<div class="main--sanitized">{escape(description)}</div>'
            f'<div class="labels--sanitized">{labels}</div></div>'
            f'<div class="buy--sanitized">{escape(status)}</div></div></div>',
            'cardinalities': {'main': 1, 'info': 1, 'price': 1, 'description': 1, 'labels': 1}}


def parse(cap):
    return parse_capture(cap, cap['url'])


class DiverseGoofishTests(unittest.TestCase):
    def check_cases(self, captures):
        rows = [parse(c) for c in captures]
        for row in rows:
            self.assertIsNone(row['price'])
            self.assertIsNone(normalize_offer('goofish', row)['price']['amount'])
            self.assertFalse(row['checkout_verified'])
            self.assertIsNone(row['selected_sku_id'])
        self.assertEqual([r['availability'] for r in rows],
                         ['delisted', 'source_claimed_available', 'sold', 'delisted'])
        self.assertEqual([r['condition'] for r in rows], ['used', 'used', 'unknown', 'new'])
        deck = rows[1]
        self.assertEqual(deck['price_basis'], 'wrong_basis')
        self.assertIn('64G', deck['source_detail']['capacity_evidence'])
        claim = next(c for c in deck['source_detail']['capacity_claims'] if c['label'] == '内存容量')
        self.assertEqual(claim['interpretation'], 'unresolved')
        self.assertIn('64GB', claim['source_excerpt'])
        self.assertFalse(deck['source_detail']['partial_price_claim'])
        self.assertTrue(any('标价为预售64裸机' in e['source_excerpt']
                            for e in deck['source_detail']['price_basis_evidence']))
        self.assertNotIn('9800', rows[2]['description'])
        self.assertNotIn('5070', rows[3]['description'])

    def test_sanitized_realistic_main_selectors(self):
        self.check_cases([capture(c['description'], c['attributes'], c['title'], c['price_text'],
                                  c['status']) for c in CASES])

    def test_retained_four_capture_hashes_and_offline_import(self):
        paths = [ROOT / '.local/diverse-search/china' / c['retained_file'] for c in CASES]
        if not all(p.exists() for p in paths):
            self.skipTest('Private captures are optional; sanitized cases run everywhere')
        captures = []
        for case, path in zip(CASES, paths):
            raw = path.read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), case['retained_sha256'])
            captures.append(json.loads(raw)['structuredContent']['value'])
        self.check_cases(captures)

    def test_literal_sold_overrides_buy_control_and_ambiguous_price(self):
        for price in ('1000', '1000 - 2000'):
            row = parse(capture('商品 卖掉了', price=price))
            self.assertEqual(row['availability'], 'sold')
            self.assertIn('卖掉了', row['source_detail']['availability_claims'])
            self.assertIsNone(row['price'])

    def test_condition_source_claims_and_conflicts(self):
        for text, expected in [('散片', 'unknown'), ('二手', 'used'), ('全新', 'new'),
                               ('几乎全新', 'used'), ('轻微使用痕迹', 'used'),
                               ('全新 二手', 'unknown'), ('无划痕 全新', 'new'),
                               ('非全新', 'unknown')]:
            with self.subTest(text=text):
                row = parse(capture(text))
                self.assertEqual(row['condition'], expected)
                self.assertEqual(row['source_detail']['condition_basis'], 'source_claim_only')
                if text == '全新 二手':
                    self.assertEqual(row['source_detail']['condition_reason'], 'conflicting_source_claims')
                    self.assertEqual({c['condition'] for c in row['source_detail']['condition_evidence']},
                                     {'new', 'used'})
        row = parse(capture('全新', {'成色': '二手'}))
        self.assertEqual(row['condition'], 'unknown')

    def test_duplicate_condition_attributes_preserve_both_claims(self):
        cap = capture('商品', {'成色': '全新'})
        cap['mainHtml'] = cap['mainHtml'].replace(
            '<div>成色：', '<div>成色：<span>二手</span></div><div>成色：')
        row = parse(cap)
        self.assertEqual(row['condition'], 'unknown')
        self.assertEqual(row['source_detail']['condition_reason'], 'conflicting_source_claims')
        self.assertEqual([c['condition'] for c in row['source_detail']['condition_evidence']],
                         ['used', 'new'])

    def test_capacity_attribute_is_untyped_and_excerpt_bound(self):
        row = parse(capture('Steam Deck OLED', {'内存容量': '64GB'}))
        claim = row['source_detail']['capacity_claims'][0]
        self.assertEqual(claim['source_excerpt'], row['source_detail']['attribute_rows'][0]['raw'])
        self.assertEqual(claim['interpretation'], 'unresolved')
        self.assertNotIn('ram_gb', row)
        self.assertNotIn('ssd_gb', row)
        self.assertIsNone(row['price'])

    def test_presale_base_is_not_deposit_even_with_consistent_phone(self):
        attrs = {'型号': 'iPhone 17 Pro Max', '存储容量': '1TB'}
        row = parse(capture('iPhone 17 Pro Max 1TB 标价为预售64裸机', attrs))
        self.assertIsNone(row['price'])
        self.assertEqual(row['price_basis'], 'wrong_basis')
        self.assertFalse(row['source_detail']['partial_price_claim'])
        row = parse(capture('iPhone 17 Pro Max 1TB 预售定金1000', attrs))
        self.assertTrue(row['source_detail']['partial_price_claim'])
        self.assertIsNone(row['price'])

    def test_recommendations_cannot_supply_price_condition_or_status(self):
        cap = capture('iPhone 17 Pro Max 1TB 二手',
                      {'型号': 'iPhone 17 Pro Max', '存储容量': '1TB'}, price='7999')
        cap['mainHtml'] += ('<aside><div class="price--other">1</div>'
                            '<div class="main--other">全新 卖掉了 256GB RTX5070Ti</div></aside>')
        row = parse(cap)
        self.assertEqual(row['price'], '7999')
        self.assertEqual(row['condition'], 'used')
        self.assertEqual(row['availability'], 'source_claimed_available')

    def test_four_iphone_positive_and_held_controls(self):
        for price, storage, description, expected in [
            ('7999', '1TB', '17ProMax 1TB 无拆修 少量磕碰划痕', '7999'),
            ('7499', '1TB', '17ProMax 1TB 批发价7499 换过外屏 可分期 可全款', '7499'),
            ('6999', '512GB', '17ProMax 1T 内存256G 512G加1000 1T加1800', None),
            ('6699 - 9399', '', '17ProMax/17Pro 256G/512G/1TB', None),
        ]:
            with self.subTest(price=price):
                row = parse(capture(description, {'型号': 'iPhone 17 Pro Max', '存储容量': storage},
                                    title='17ProMax 1TB_闲鱼', price=price))
                self.assertEqual(row['price'], expected)
                self.assertEqual(normalize_offer('goofish', row)['price']['amount'], expected)

    def test_retained_iphone_positive_and_held_controls(self):
        controls = [
            ('goofish-main-structure.json',
             '8c412e1bfb7f39048d1e7763dd61fe34a09b01dc6ec5533f85394d1848a2e85b', None),
            ('goofish-1093271890833.json',
             '4ef8b9e2628ff2c2ad877d86c9b3059b45fc89d066199011666e98a0bb86ec9c', None),
            ('goofish-1096499480089.json',
             '32e21b375ee1773eb1bc4824b6f8ce703fc82691152c1e0ff427058a3d107afe', '7999'),
            ('goofish-1092800987315.json',
             'fda8ed8fadcb5fca8583ec7e17349e691c5f6d779ea23f573dba878b141bd0f0', '7499'),
        ]
        directory = ROOT / '.local/deeper-validation/iphone'
        if not all((directory / name).exists() for name, _, _ in controls):
            self.skipTest('Private iPhone captures are optional; synthetic controls run everywhere')
        for name, digest, expected in controls:
            with self.subTest(capture=name):
                raw = (directory / name).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                row = parse(json.loads(raw)['structuredContent']['value'])
                self.assertEqual(row['price'], expected)
                self.assertEqual(normalize_offer('goofish', row)['price']['amount'], expected)


class ConditionSubjectRegressions(unittest.TestCase):
    def test_new_component_or_gift_does_not_make_phone_new(self):
        from china_deals.filters import evaluate_offer
        for description in ('iPhone 17 Pro Max 1TB 换过全新屏幕',
                            'iPhone 17 Pro Max 1TB 赠送全新手机壳',
                            'iPhone 17 Pro Max 1TB，全新屏幕'):
            row = parse(capture(description, {'型号': 'iPhone 17 Pro Max', '存储容量': '1TB'}, price='7999'))
            self.assertEqual(row['condition'], 'unknown')
            normalized = normalize_offer('goofish', row, row['observed_at'])
            self.assertEqual(evaluate_offer(normalized, {'condition': 'new'})['status'], 'unknown')
            self.assertTrue(any(c['scope'] == 'component_or_gift' for c in row['source_detail']['condition_evidence']))

    def test_main_condition_and_accessory_condition_are_separate(self):
        self.assertEqual(parse(capture('全新手机壳'))['condition'], 'new')
        self.assertEqual(parse(capture('全新 iPhone 17 Pro Max 1TB，赠送全新手机壳'))['condition'], 'new')
        repaired = parse(capture('iPhone 17 Pro Max 1TB 换过全新屏幕', {'成色': '全新'}))
        self.assertEqual(repaired['condition'], 'unknown')
        self.assertEqual(repaired['source_detail']['condition_reason'], 'main_condition_with_repair_claim')

    def test_component_condition_is_scoped_in_titles_and_in_both_directions(self):
        for cap in (
            capture('iPhone 17 Pro Max 1TB', title='iPhone 17 Pro Max 1TB 全新屏幕'),
            capture('iPhone 17 Pro Max 1TB 屏幕全新'),
        ):
            self.assertEqual(parse(cap)['condition'], 'unknown')

    def test_trailing_repair_claim_holds_explicit_new_device(self):
        row = parse(capture('iPhone 17 Pro Max 1TB 全新，换过电池'))
        self.assertEqual(row['condition'], 'unknown')
        self.assertEqual(row['source_detail']['condition_reason'], 'main_condition_with_repair_claim')
        self.assertTrue(any(c['repair_or_replacement_claim'] for c in row['source_detail']['condition_evidence']))
        self.assertEqual(parse(capture('iPhone 17 Pro Max 1TB 全新，没有换过电池'))['condition'], 'new')

    def test_gift_scope_stops_at_clause_boundary(self):
        row = parse(capture('iPhone 17 Pro Max 1TB 赠送全新手机壳，手机二手'))
        self.assertEqual(row['condition'], 'used')
        claims = row['source_detail']['condition_evidence']
        self.assertTrue(any(c['condition'] == 'used' and c['scope'] == 'main_product' for c in claims))

    def test_whitespace_cannot_hide_component_or_revive_negated_repair(self):
        for text, expected in (
            ('iPhone 17 Pro Max 1TB 全新 屏幕', 'unknown'),
            ('iPhone 17 Pro Max 1TB 屏幕 全新', 'unknown'),
            ('iPhone 17 Pro Max 1TB 没有换过电池 全新', 'new'),
            ('iPhone 17 Pro Max 1TB 换过 全新 屏幕', 'unknown'),
        ):
            with self.subTest(text=text):
                self.assertEqual(parse(capture(text))['condition'], expected)
