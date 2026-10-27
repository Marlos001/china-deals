"""Cross-command coverage for the new China marketplaces; no live requests."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from china_deals import adapters, guest, promotions, refresh
from china_deals.capabilities import marketplace_capabilities, resolve_markets
from china_deals.cli import build_parser, run
from china_deals.config import DEFAULT_CONFIG, load_config
from china_deals.coupons import assess_coupon_freshness, evaluate_coupons
from china_deals.filters import native_plan
from china_deals.marketplaces import FANSBUY_MARKETPLACES, MARKETPLACES, item_url
from china_deals.models import normalize_offer
from china_deals.products import query_plan
from china_deals.ranking import rank_offers

NEW = ('tmall', '1688', 'weidian')
STAMP = '2026-10-27T12:00:00Z'


def observation(market, **changes):
    return {'marketplace': market, 'item_id': '123', 'url': item_url(market, '123'),
            'title': 'Sony WH-1000XM6', 'price': '100', 'currency': 'CNY',
            'source_mode': 'user_observation', 'observed_at': STAMP, **changes}


class MarketplaceIntegration(unittest.TestCase):
    def test_inventory_groups_and_configuration_agree(self):
        self.assertEqual(resolve_markets('fansbuy'), list(FANSBUY_MARKETPLACES))
        self.assertEqual(resolve_markets('all'), list(MARKETPLACES))
        self.assertEqual(resolve_markets('tmall, fansbuy, weidian.com'), ['tmall', 'taobao', '1688', 'weidian', 'jd'])
        self.assertEqual(set(load_config()['marketplaces']), set(MARKETPLACES))
        matrix = marketplace_capabilities()
        self.assertEqual({r['marketplace'] for r in matrix['marketplaces']}, set(MARKETPLACES))
        for market in NEW:
            self.assertEqual(DEFAULT_CONFIG['marketplaces'][market],
                             {'access': 'guest', 'shipping': 'fansbuy', 'currency': 'CNY'})
            row = next(r for r in matrix['marketplaces'] if r['marketplace'] == market)
            self.assertFalse(row['live_access_verified'])
            self.assertIn('unavailable', row['native_access'])

    def test_existing_configuration_remains_additive(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'prefs.json'
            path.write_text(json.dumps({'marketplaces': {'jd': {'shipping': 'manual'}}}))
            config = load_config(path)
            self.assertEqual(config['marketplaces']['jd']['shipping'], 'manual')
            for market in NEW:
                self.assertEqual(config['marketplaces'][market]['shipping'], 'fansbuy')

    def test_plans_and_filters_do_not_invent_native_parameters(self):
        plan = query_plan('Sony WH-1000XM6')
        self.assertEqual(set(plan['marketplace_queries']), set(MARKETPLACES))
        for market in NEW:
            self.assertRegex(plan['marketplace_queries'][market][0], '[\u3400-\u9fff]')
            filters = native_plan(market, '索尼 WH-1000XM6', {'max_price': '200', 'city': '深圳'})
            self.assertIsNone(filters['native_search_url'])
            self.assertEqual(filters['opencli_argv'], [])
            self.assertEqual(filters['submitted_native_filters'], [])
            self.assertEqual(set(filters['unverified_or_local_filters']), {'max_price', 'city'})

    def test_native_unavailable_is_zero_io(self):
        with patch.object(adapters, '_run', side_effect=AssertionError('unsupported native I/O')):
            for market in NEW:
                for result in (adapters.search_marketplace(market, '索尼 WH-1000XM6'),
                               adapters.get_item(market, item_url(market, '123'))):
                    self.assertEqual(result['status'], 'unavailable')
                    self.assertEqual(result['error']['code'], 'native_adapter_unavailable')
                    self.assertEqual(result['items'], [])

    def test_chinese_gate_and_fansbuy_group_work_through_cli(self):
        with patch.object(guest, '_fetch', side_effect=AssertionError('missing Chinese must not fetch')):
            result, code = run(build_parser().parse_args(
                ['search', 'Sony WH-1000XM6', '--markets', 'fansbuy', '--currency', 'native']))
        self.assertEqual(code, 3)
        self.assertEqual([r['marketplace'] for r in result['sources']], list(FANSBUY_MARKETPLACES))
        self.assertTrue(all(r['error']['code'] == 'chinese_query_required' for r in result['sources']))

    def test_actual_index_parser_retains_new_routes_as_unpriced_discovery(self):
        for market in NEW:
            url = item_url(market, '123')
            body = ('<div class="result"><a class="result__a" href="' + url + '">'
                    'Sony WH-1000XM6 ¥100</a><a class="result__snippet">Cached quote ¥100</a></div>')
            with patch.object(guest, '_fetch', return_value=(body, 'https://html.duckduckgo.com/html/')):
                result = guest.search_guest(market, '索尼 WH-1000XM6')
            self.assertEqual(result['status'], 'discovery_only')
            self.assertEqual(result['items'][0]['url'], url)
            self.assertIsNone(result['items'][0]['price'])
            self.assertFalse(rank_offers([dict(result['items'][0], marketplace=market)], query='Sony WH-1000XM6')['groups'])

    def test_same_numeric_ids_are_separate_and_wrong_urls_cannot_qualify(self):
        rows = [observation(market) for market in NEW]
        result = rank_offers(rows, query='Sony WH-1000XM6')
        self.assertEqual(len(result['groups']['CNY']), 3)
        for market in NEW:
            row = normalize_offer(market, observation(market, url=item_url(market, '456')), STAMP)
            self.assertIsNone(row['price']['amount'])
            for _ in range(3):
                result = rank_offers([row], query='Sony WH-1000XM6')
                self.assertFalse(result['groups'])
                row = json.loads(json.dumps(result['unranked'][0]))

    def test_freshness_and_query_holds_survive_new_market_roundtrips(self):
        for market in NEW:
            row = observation(market, observed_at='2026-10-27T10:00:00Z')
            for _ in range(3):
                result = rank_offers([row], query='Sony WH-1000XM6', fresh_only=True,
                                     max_age_hours=1, as_of=STAMP)
                self.assertFalse(result['groups'])
                row = json.loads(json.dumps(result['unranked'][0]))
                self.assertEqual(row['price_freshness_policy']['max_age_hours'], '1')

    def test_failed_refresh_history_keeps_new_identity_and_no_current_price(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Path(folder) / 'history.sqlite3'
            for market in NEW:
                failure = {'marketplace': market, 'status': 'blocked', 'items': [],
                           'error': {'code': 'challenge'}, 'access': {'attempts': []}}
                with patch.object(guest, 'get_guest_item', return_value=failure) as getter:
                    result = refresh.refresh_offers([observation(market)], as_of=STAMP, store_path=store)
                getter.assert_called_once()
                row = result['items'][0]
                self.assertEqual(row['marketplace'], market)
                self.assertEqual(row['url'], item_url(market, '123'))
                self.assertIsNone(row['price']['amount'])
                self.assertEqual(row['previous_observation']['price']['amount'], '100')
                self.assertEqual(len(refresh.history(store, marketplace=market, item_id='123')), 1)

    def test_primary_promotion_capture_and_coupon_identity_requirements(self):
        for market in NEW:
            text = '优惠券 满100减10 仅指定商品'
            url = item_url(market, '123')
            cap = {'url': url, 'capturedAt': STAMP, 'visibleText': text,
                   'visibleTextBytes': len(text.encode()), 'visibleTextTruncated': False}
            evidence = promotions.parse_capture(cap, market, url)
            self.assertEqual(evidence['status'], 'ok')
            self.assertNotIn('campaigns', evidence)
            campaign = {'id': 'synthetic', 'marketplace': market, 'currency': 'CNY',
                        'discount': {'amount': '10'}, 'confirmed': True, 'eligibility': 'confirmed',
                        'product_ids': ['123'], 'source_url': url, 'source_mode': 'coupon_page',
                        'observed_at': STAMP, 'starts_at': '2026-10-27T00:00:00Z',
                        'ends_at': '2026-10-28T00:00:00Z'}
            self.assertTrue(assess_coupon_freshness(campaign, STAMP)['fresh'])
            row = normalize_offer(market, observation(market), STAMP)
            result = evaluate_coupons(row, [campaign], as_of=STAMP, require_fresh=True)
            self.assertEqual(result['campaigns'][0]['status'], 'eligible')
            row = normalize_offer(market, observation(market, url=item_url(market, '456')), STAMP)
            result = evaluate_coupons(row, [campaign], as_of=STAMP, require_fresh=True)
            self.assertNotEqual(result['campaigns'][0]['status'], 'eligible')
