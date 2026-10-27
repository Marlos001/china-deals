"""Portable synthetic equivalents of the observed public main-item selectors."""

import unittest
from html import escape

from china_deals.goofish_public import CAPTURE_JS, parse_capture
from china_deals.models import normalize_offer
from china_deals.ranking import rank_offers

URL = 'https://www.goofish.com/item?id=1096499480089'


def capture(description='17promax 国行双卡 1TB 橙色 电池寿命91 纯原装 无拆修 机器边框有磕碰 屏幕有划痕',
            price='7999', storage='1TB', repair='无任何维修', shipping='包邮', title='17ProMax 1TB_闲鱼'):
    attrs = [('型号', 'iPhone 17 Pro Max'), ('存 储 容 量', storage),
             ('成色', '少量磕碰划痕'), ('拆 修 和 功 能', repair)]
    labels = ''.join(f'<div>{escape(k)}：<span>{escape(v)}</span></div>' for k, v in attrs)
    html = (f'<div class="item-main-container--abc"><div class="item-main-info--abc">'
            f'<div class="price--abc">{escape(price)}</div><div class="post--abc">{shipping}</div>'
            '<div class="desc--policy">Seven-day platform return policy, NOT product prose</div>'
            f'<div class="notLoginContainer--abc"><div class="main--abc">{escape(description)}</div>'
            f'<div class="labels--abc">{labels}</div></div>'
            '<a class="buy--abc">立即购买</a></div></div>')
    return {'url': URL, 'title': title, 'capturedAt': '2026-10-27T16:29:23.028Z', 'mainHtml': html,
            'cardinalities': {'main': 1, 'info': 1, 'price': 1, 'description': 1, 'labels': 1}}


class PublicCaptureTests(unittest.TestCase):
    def test_consistent_used_pickup_listing_preserves_claims(self):
        cap = capture(description='17promax 国行双卡 1TB 橙色 纯原装 无拆修 屏幕有划痕 电池寿命91 仅支持青岛城阳自提')
        row = parse_capture(cap, URL)
        self.assertEqual(row['price'], '7999')
        self.assertEqual(row['configuration_binding'], 'single_listing_consistent')
        self.assertEqual(row['condition'], 'used')
        self.assertEqual(row['availability'], 'source_claimed_available')
        self.assertIsNone(row['selected_sku_id'])
        self.assertIsNone(row['stock_quantity'])
        self.assertFalse(row['checkout_verified'])
        self.assertIsNone(row['domestic_free_shipping'])
        self.assertEqual(row['source_detail']['capture'], cap)
        self.assertEqual(row['attributes']['拆修和功能'], '无任何维修')
        self.assertTrue(row['source_detail']['pickup_only'])
        self.assertTrue(any('conflicts' in w for w in row['source_warnings']))
        self.assertIn('电池寿命91', row['description'])
        self.assertNotIn('return policy', row['description'])
        self.assertEqual(normalize_offer('goofish', row)['price']['amount'], '7999')

    def test_literal_model_attributes_support_title_shorthand_without_selected_sku_claim(self):
        row = normalize_offer('goofish', parse_capture(capture(title='17promax 国行双卡 1TB 橙色_闲鱼'), URL))
        result = rank_offers([row], query='iPhone 17 Pro Max 1TB')
        self.assertEqual(result['groups']['CNY'][0]['price']['amount'], '7999')
        self.assertIsNone(row['source_detail']['selected_sku_id'])
        self.assertIn('literal_listing_attributes', row['source_detail']['variant_basis'])

    def test_network_generation_does_not_become_storage_capacity(self):
        row = parse_capture(capture(description='iPhone17ProMax 1TB 国行 全网通5G'), URL)
        self.assertEqual(row['price'], '7999')
        self.assertEqual(row['source_detail']['capacity_evidence'], ['1T'])

    def test_repaired_wholesale_and_financing_is_full_price(self):
        row = parse_capture(capture(
            description='苹果17ProMax、1TB国行 银色 7161# 批发价¥7499 电池90% 成色95新 换过外屏 可分期 可全款',
            price='7499', repair='屏幕有维修', shipping='可自提'), URL)
        self.assertEqual(row['price'], '7499')
        self.assertEqual(row['condition'], 'used')
        self.assertEqual(row['source_detail']['repair_claim'], '屏幕有维修')
        self.assertTrue(row['source_detail']['wholesale_qualifier'])
        self.assertFalse(row['source_detail']['pickup_only'])
        self.assertIn('电池90%', row['description'])
        self.assertTrue(any('Wholesale' in w for w in row['source_warnings']))

    def test_old_capacity_conflict_keeps_schedule_unpriced(self):
        row = parse_capture(capture(price='6999', storage='512GB', description=(
            '17ProMax 1T 内存256G 蓝色6999橙色7099白色7499 512G加1000 1T加1800 '
            '美版无锁 开孔支持双卡 全新未拆封 无任何维修 半年保修 不撕标')), URL)
        self.assertIsNone(row['price'])
        self.assertIsNone(normalize_offer('goofish', row)['price']['amount'])
        self.assertEqual(row['source_detail']['price_text'], '6999')
        self.assertIn('512G加1000', row['description'])
        self.assertIn('半年保修', row['description'])

    def test_range_mixed_models_and_capacities(self):
        row = parse_capture(capture(price='6699 - 9399', storage='', description=(
            '17ProMax1TB 型号17ProMax/17Pro 内存256G/512G/1TB 电池92%到100% 全原装无维修')), URL)
        self.assertIsNone(row['price'])
        self.assertEqual(row['source_detail']['price_text'], '6699 - 9399')
        self.assertEqual(row['source_detail']['model_evidence'], ['17pro', '17promax'])
        self.assertEqual(row['configuration_binding'], 'mixed_or_conflicting_variants')

    def test_range_without_variant_conflict_stays_unpriced(self):
        self.assertIsNone(parse_capture(capture(price='7999 - 8999'), URL)['price'])

    def test_deposit_and_monthly_prices_are_unpriced(self):
        for qualifier in ('定金7999', '月供7999', '首付7999'):
            with self.subTest(qualifier=qualifier):
                row = parse_capture(capture(description='17ProMax 1TB ' + qualifier), URL)
                self.assertIsNone(row['price'])

    def test_recommendation_price_never_enters_main_extraction(self):
        cap = capture()
        cap['mainHtml'] += '<aside><div class="price--other">1</div><div class="main--other">17Pro 256GB</div></aside>'
        row = parse_capture(cap, URL)
        self.assertEqual(row['price'], '7999')
        self.assertNotIn('256GB', row['description'])

    def test_duplicate_price_is_unpriced(self):
        cap = capture()
        cap['mainHtml'] = cap['mainHtml'].replace('<div class="price--abc">',
                                                              '<div class="price--x">1</div><div class="price--abc">')
        cap['cardinalities']['price'] = 2
        row = parse_capture(cap, URL)
        self.assertIsNone(row['price'])
        self.assertEqual(row['source_detail']['price_texts'], ['1', '7999'])

    def test_requested_final_identity_binding(self):
        for url in (URL.replace('1096499480089', '1023378656793'), URL + '&id=1096499480089',
                    URL.replace('www.goofish.com', 'evil.test'), URL.replace('https:', 'http:'),
                    URL.replace('/item?', '/login?'), URL.replace('1096499480089', 'opaque')):
            with self.subTest(url=url), self.assertRaises(ValueError):
                parse_capture(capture(), url)
        cap = capture()
        cap['url'] += '&categoryId=0'
        self.assertEqual(parse_capture(cap, URL)['item_id'], '1096499480089')

    def test_missing_final_url_rejected(self):
        cap = capture()
        del cap['url']
        with self.assertRaises(ValueError):
            parse_capture(cap, URL)

    def test_cardinality_and_truncation_rejected(self):
        for mutate in (lambda c: c['cardinalities'].update(main=2),
                       lambda c: c.update(mainHtmlTruncated=True),
                       lambda c: c.update(mainHtml=c['mainHtml'][:-6]),
                       lambda c: c.update(mainHtml=c['mainHtml'] * 2),
                       lambda c: c.update(mainHtml=c['mainHtml'] + '中' * 22000)):
            cap = capture()
            mutate(cap)
            with self.assertRaises(ValueError):
                parse_capture(cap, URL)

    def test_sold_overrides_purchase_control_and_price(self):
        row = parse_capture(capture(description='17ProMax 1TB 已售出'), URL)
        self.assertEqual(row['availability'], 'sold')
        self.assertIsNone(row['price'])

    def test_unknown_storage_and_missing_purchase_control(self):
        cap = capture(storage='')
        cap['mainHtml'] = cap['mainHtml'].replace('立即购买', '联系卖家')
        row = parse_capture(cap, URL)
        self.assertIsNone(row['price'])
        self.assertEqual(row['availability'], 'unknown')

    def test_aware_timestamp_required(self):
        for stamp in (None, '', 'yesterday', '2026-10-27T16:29:23'):
            cap = capture()
            cap['capturedAt'] = stamp
            with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                parse_capture(cap, URL)

    def test_capture_expression_is_fixed_read_only_and_bounded(self):
        self.assertIn('65536', CAPTURE_JS)
        self.assertIn('TextEncoder', CAPTURE_JS)
        self.assertIn('cardinalities', CAPTURE_JS)
        self.assertNotIn('fetch(', CAPTURE_JS)
        self.assertNotIn('eval(', CAPTURE_JS)


if __name__ == '__main__':
    unittest.main()
