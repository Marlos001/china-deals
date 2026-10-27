import unittest

from china_deals.brazil import compare_brazil
from china_deals.models import normalize_offer
from china_deals.ranking import rank_offers
from tests.test_brazil import AS_OF, payload
from tests.test_freshness import offer


class BrazilHardeningTests(unittest.TestCase):
    def compare(self, data):
        return compare_brazil(data)['cases'][0]

    def test_stale_and_future_fx_cannot_establish_savings(self):
        for date in ('2025-10-27', '2026-10-28'):
            data = payload()
            data['fx']['rate_date'] = date
            row = self.compare(data)
            self.assertEqual(row['financial_outcome'], 'needs_review')
            self.assertIsNone(row['savings_amount_brl'])

    def test_observed_freight_needs_recent_quote(self):
        for stamp in (None, '2026-10-20T12:00:00Z'):
            data = payload()
            cost = data['cases'][0]['imported']['costs']['international_freight']
            cost.update(basis='observed', observed_at=stamp)
            self.assertEqual(self.compare(data)['financial_outcome'], 'needs_review')
        cost['observed_at'] = AS_OF
        self.assertEqual(self.compare(data)['financial_outcome'], 'import_cheaper')

    def test_monthly_amount_on_either_side_cannot_win(self):
        for side in ('imported', 'brazil'):
            data = payload()
            data['cases'][0][side]['offer']['title'] += ' monthly payment'
            self.assertEqual(self.compare(data)['financial_outcome'], 'needs_review')

    def test_foreign_search_url_cannot_establish_comparable_quote(self):
        data = payload()
        data['cases'][0]['imported']['offer']['url'] = 'https://search.jd.com/Search?keyword=test'
        row = self.compare(data)
        self.assertIsNone(row['imported']['landed_total_brl'])
        self.assertEqual(row['financial_outcome'], 'needs_review')

    def test_accessory_title_cannot_override_confirmed_identity(self):
        data = payload()
        case = data['cases'][0]
        for side in ('imported', 'brazil'):
            case[side]['identity']['model'] = 'AirPods Max'
            case[side]['offer']['title'] = 'AirPods Max'
        case['imported']['offer']['variant'] = 'Smart Case only'
        self.assertEqual(self.compare(data)['financial_outcome'], 'needs_review')

    def test_exclusions_on_either_side_survive_normalization_and_export(self):
        for side in ('imported', 'brazil'):
            data = payload()
            data['cases'][0][side]['offer']['ranking_exclusions'] = ['manual_identity_conflict']
            for _ in range(3):
                row = self.compare(data)
                self.assertEqual(row['financial_outcome'], 'needs_review')
                data['cases'][0][side]['offer'] = row[side]['offer']

    def test_variant_dictionary_and_model_survive_normalization(self):
        data = payload()
        foreign = data['cases'][0]['imported']['offer']
        foreign['variant'] = {'gpu': 'Other GPU'}
        data['cases'][0]['imported']['offer'] = normalize_offer('jd', foreign, AS_OF)
        self.assertIn('imported.offer_gpu_conflict', self.compare(data)['reasons'])

    def test_stricter_exported_age_policy_is_respected_on_both_sides(self):
        for side in ('imported', 'brazil'):
            data = payload()
            data['cases'][0][side]['offer'].update(observed_at='2026-10-27T10:00:00Z',
                price_freshness_policy={'required': True, 'max_age_hours': '1'})
            self.assertEqual(self.compare(data)['financial_outcome'], 'needs_review')

    def test_out_of_stock_alias_cannot_win(self):
        data = payload()
        data['cases'][0]['imported']['offer']['availability'] = 'out_of_stock'
        self.assertEqual(self.compare(data)['financial_outcome'], 'needs_review')

    def test_payment_fields_and_installments_cannot_be_total(self):
        for side, field, value in [('imported', 'title', 'SYNTHETIC 12 installments'),
                                   ('imported', 'title', 'SYNTHETIC 月付 100'),
                                   ('brazil', 'payment_method', '12x R$150,00')]:
            data = payload()
            data['cases'][0][side]['offer'][field] = value
            self.assertEqual(self.compare(data)['financial_outcome'], 'needs_review')

    def test_query_recomputes_relevance_without_removing_independent_holds(self):
        row = offer(ranking_exclusions=['manual_identity_conflict'])
        result = rank_offers([row], query='iPhone 17 Pro Max', as_of=AS_OF)
        self.assertFalse(result['groups'])
        self.assertIn('manual_identity_conflict', result['unranked'][0]['ranking_exclusions'])

    def test_payment_scope_survives_rank_normalization(self):
        for kind in ('payment_method', 'variant', 'price_scope'):
            data = payload()
            foreign = data['cases'][0]['imported']['offer']
            if kind == 'payment_method':
                foreign[kind] = '12x R$100'
            elif kind == 'variant':
                foreign[kind] = {'payment': '12 installments'}
            else:
                foreign['price'] = {'raw': '100', 'amount': '100', 'currency': 'CNY', 'basis': 'displayed', 'scope': 'installment'}
            for _ in range(3):
                ranked = rank_offers([foreign], as_of=AS_OF)
                foreign = next(iter(ranked['groups'].values()))[0] if ranked['groups'] else ranked['unranked'][0]
                data['cases'][0]['imported']['offer'] = foreign
                self.assertEqual(self.compare(data)['financial_outcome'], 'needs_review')
