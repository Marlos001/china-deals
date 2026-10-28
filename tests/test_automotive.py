import json
import unittest

from china_deals.automotive import parts_query_plan
from china_deals.marketplaces import CHINESE_MARKETPLACES, MARKETPLACES
from china_deals.products import query_plan
from china_deals.ranking import rank_offers


class AutomotivePlans(unittest.TestCase):
    def test_exact_user_vehicle_and_scope_survive_every_market(self):
        q = 'Audi A4 B9 2018-2019 Ambiente sedan 2.0T FWD standard bumper intake Revo RA841M200100'
        plan = query_plan(q)
        self.assertEqual(plan['categories'], ['bumper', 'intake'])
        self.assertEqual(set(plan['marketplace_queries']), set(MARKETPLACES))
        for market, queries in plan['marketplace_queries'].items():
            self.assertTrue(queries)
            for value in queries:
                self.assertIn(q, value)
                self.assertLessEqual(len(value), 500)
                if market in CHINESE_MARKETPLACES:
                    self.assertIn('奥迪', value)
        self.assertIsNone(plan['family'])
        self.assertIn('seller_evidence_required', plan)

    def test_category_aliases_and_no_inferred_car_specifications(self):
        for suffix, category in [('rodas', 'wheels'), ('farol', 'headlights'),
                                 ('lanternas', 'taillights'), ('admissão', 'intake'),
                                 ('escapamento', 'exhaust'), ('轮毂', 'wheels')]:
            plan = query_plan('Audi A4 B9 ' + suffix)
            self.assertEqual(plan['categories'], [category])
            for values in plan['marketplace_queries'].values():
                for value in values:
                    for inferred in ('FWD', 'quattro', 'sedan', '190', '252', '标准', 'MAF'):
                        self.assertNotIn(inferred, value)
        explicit = 'Audi A4 B9 Avant quattro S-line MAP intake'
        for values in query_plan(explicit)['marketplace_queries'].values():
            self.assertTrue(all(explicit in value for value in values))

    def test_broad_plan_bounded_and_long_refinements_never_truncated(self):
        plan = query_plan('Audi A4 B9')
        self.assertEqual(len(plan['categories']), 11)
        self.assertEqual(len(plan['marketplace_queries']['alibaba']), 11)
        self.assertIn('Audi A4 B9 headlights', plan['marketplace_queries']['aliexpress'])
        self.assertTrue(all(len(q) <= 500 for values in plan['marketplace_queries'].values() for q in values))
        long = 'Audi A4 B9 ' + 'a' * 485
        fallback = query_plan(long)
        self.assertNotIn('planning_profile', fallback)
        self.assertEqual(fallback['marketplace_queries']['alibaba'], [long])
        self.assertTrue(fallback['requires_agent_translation'])

    def test_other_generations_and_models_not_silently_rebound(self):
        for q in ('Audi A4 B8 wheels', 'Audi A5 B9 spoiler', 'Audi S4 B9 turbo',
                  'Audi A40 B9 wheels', 'Audi A4 B90 wheels', 'Audi A4 wheels'):
            self.assertIsNone(parts_query_plan(q))

    def test_planning_does_not_promote_unknown_automotive_fitment(self):
        q = 'Audi A4 B9 2018 Ambiente 2.0T FWD headlights'
        row = {'marketplace': 'aliexpress', 'title': 'Audi A4 B9 2013-2016 8K0941753 headlights',
               'url': 'https://www.aliexpress.com/item/1005001234567890.html',
               'price': '20', 'currency': 'USD'}
        for _ in range(4):
            result = rank_offers(json.loads(json.dumps([row])), query=q)
            self.assertFalse(result['groups'])
            row = result['unranked'][0]
            self.assertIn('product_relevance_uncertain', row['ranking_exclusions'])

    def test_controls_reject_at_public_boundary(self):
        for q in ('Audi A4 B9\nintake', 'Audi A4 B9 ' + 'x'*500):
            with self.assertRaises(ValueError):
                query_plan(q)
