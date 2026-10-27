import unittest
from copy import deepcopy

from china_deals.freshness import annotate_price_freshness, assess_price_freshness
from china_deals.ranking import rank_offers

NOW = '2026-10-27T18:00:00Z'


def offer(**overrides):
    return dict({'marketplace': 'jd', 'item_id': '123', 'title': 'iPhone 17 Pro Max 1TB',
                 'url': 'https://item.jd.com/123.html', 'price': '7999',
                 'source_mode': 'guest_product_page', 'observed_at': '2026-10-27T17:00:00Z'}, **overrides)


class FreshnessTests(unittest.TestCase):
    def test_recent_and_expired_boundary(self):
        self.assertTrue(assess_price_freshness(offer(), 1, NOW)['recent_observation'])
        self.assertFalse(assess_price_freshness(offer(), '.99', NOW)['recent_observation'])

    def test_cached_retrieval_never_renews_price(self):
        for mode in ('proxy_catalog', 'search_index', 'indexed_product_block', 'connector_product_open_cached', 'category_card'):
            result = assess_price_freshness(offer(source_mode=mode, observed_at=NOW,
                source_detail={'price_observation': {'crawl_age': '2 weeks'}}), as_of=NOW)
            self.assertEqual(result['status'], 'cached_or_aggregated_source')
            self.assertFalse(result['recent_observation'])
            self.assertEqual(result['cache_age_label'], '2 weeks')

    def test_unknown_naive_future(self):
        for stamp in (None, 'garbage', '2026-10-27T17:00:00', '2026-10-28T00:00:00Z'):
            self.assertFalse(assess_price_freshness(offer(observed_at=stamp), as_of=NOW)['recent_observation'])
        self.assertFalse(assess_price_freshness(offer(source_mode='unspecified'), as_of=NOW)['recent_observation'])

    def test_invalid_clock_and_limits(self):
        for limit in (0, -1, 'NaN', 8761, True):
            with self.assertRaises(ValueError):
                assess_price_freshness(offer(), limit, NOW)
        with self.assertRaises(ValueError):
            assess_price_freshness(offer(), as_of='2026-10-27')

    def test_fresh_only_retains_stale_observations_unranked(self):
        rows = [offer(), offer(item_id='456', url='https://item.jd.com/456.html', observed_at='2026-10-20T17:00:00Z')]
        result = rank_offers(rows, fresh_only=True, as_of=NOW)
        self.assertEqual(len(result['groups']['CNY']), 1)
        self.assertIn('price_freshness_older_than_limit', result['unranked'][0]['ranking_exclusions'])
        self.assertEqual(result['unranked'][0]['price']['amount'], '7999')

    def test_required_policy_survives_query_array_roundtrip(self):
        result = rank_offers([offer(observed_at='2026-10-20T17:00:00Z')], query='iPhone 17 Pro Max', fresh_only=True, as_of=NOW)
        for _ in range(2):
            result = rank_offers(result['unranked'], query='iPhone 17 Pro Max', as_of=NOW)
            self.assertFalse(result['groups'])
            self.assertEqual(result['unranked'][0]['ranking_exclusions'].count('price_freshness_older_than_limit'), 1)

    def test_default_annotates_without_age_filter(self):
        rows = [offer(observed_at='2026-10-20T17:00:00Z')]
        original = deepcopy(rows)
        result = rank_offers(rows, as_of=NOW)
        self.assertEqual(result['groups']['CNY'][0]['price_freshness']['status'], 'older_than_limit')
        self.assertEqual(rows, original)

    def test_annotation_recomputes_instead_of_trusting_supplied_result(self):
        row = offer(observed_at='2026-10-20T17:00:00Z', price_freshness={'recent_observation': True})
        annotate_price_freshness(row, True, as_of=NOW)
        self.assertFalse(row['price_freshness']['recent_observation'])

    def test_fresh_only_default_cannot_weaken_stricter_export(self):
        row = offer(observed_at='2026-10-27T16:00:00Z')
        result = rank_offers([row], fresh_only=True, max_age_hours=1, as_of=NOW)
        result = rank_offers(result['unranked'], fresh_only=True, as_of=NOW)
        self.assertFalse(result['groups'])
        self.assertEqual(result['unranked'][0]['price_freshness_policy']['max_age_hours'], '1')
