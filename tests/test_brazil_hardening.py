import unittest

from china_deals.brazil import compare_brazil
from china_deals.models import normalize_offer
from china_deals.ranking import rank_offers
from tests.test_brazil import AS_OF, money, payload
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

    def test_textual_configurations_hold_even_for_unsupported_family(self):
        for side in ('imported', 'brazil'):
            for field, text, reason in [('variant', '32GB RAM', 'textual_variant_unverified'),
                                        ('selected_variant', 'RTX 4090', 'textual_variant_unverified'),
                                        ('title', 'SYNTHETIC Model A RAM 32GB', 'textual_configuration_unverified'),
                                        ('title', 'SYNTHETIC Model A 32GB', 'textual_configuration_unverified')]:
                with self.subTest(side=side, field=field):
                    data = payload()
                    data['cases'][0][side]['offer'][field] = text
                    result = self.compare(data)
                    self.assertEqual(result['status'], 'needs_review')
                    self.assertIn(f'{side}.{reason}', result['reasons'])
                    self.assertIsNone(result['savings_amount_brl'])

    def test_stricter_exported_age_policy_is_respected_on_both_sides(self):
        for side in ('imported', 'brazil'):
            data = payload()
            data['cases'][0][side]['offer'].update(observed_at='2026-10-27T10:00:00Z',
                price_freshness_policy={'required': True, 'max_age_hours': '1'})
            self.assertEqual(self.compare(data)['financial_outcome'], 'needs_review')

    def test_out_of_stock_alias_cannot_win(self):
        for side in ('imported', 'brazil'):
            for availability in ('out_of_stock', 'OutOfStock', ' OUT-OF-STOCK ',
                                 'https://schema.org/OutOfStock', 'HTTP://schema.org/outofstock'):
                with self.subTest(side=side, availability=availability):
                    data = payload()
                    data['cases'][0][side]['offer']['availability'] = availability
                    row = self.compare(data)
                    self.assertEqual(row['financial_outcome'], 'needs_review')
                    self.assertIn(side + '_offer_unavailable', row['reasons'])

    def test_excluded_carrier_still_counts_explicit_freight_and_can_reverse_winner(self):
        data = payload()
        case = data['cases'][0]
        case['imported']['offer'] = {'marketplace': 'blibli', 'title': 'SYNTHETIC Model A',
            'url': 'https://www.blibli.com/p/synthetic/ps--FAKE', 'price': 'Rp100.000',
            'source_mode': 'guest_product_page', 'observed_at': AS_OF}
        freight = case['imported']['costs']['international_freight']
        row = self.compare(data)
        self.assertEqual(row['financial_outcome'], 'import_cheaper')
        freight['amount'] = '150'
        row = self.compare(data)
        self.assertEqual(row['imported']['shipping_policy'], 'excluded')
        self.assertEqual(row['imported']['costs']['international_freight']['amount_brl'], '150.00')
        self.assertEqual(row['imported']['landed_total_brl'], '180.00')
        self.assertEqual(row['financial_outcome'], 'brazil_cheaper')
        self.assertEqual(row['conditional_math']['outcome'], 'brazil_cheaper')
        del case['imported']['costs']['international_freight']
        row = self.compare(data)
        self.assertIn('international_freight', row['missing_costs']['imported'])
        self.assertIsNone(row['imported']['landed_total_brl'])
        self.assertIsNone(row['conditional_math'])
        self.assertEqual(row['financial_outcome'], 'needs_review')
        case['imported']['costs']['international_freight'] = money('150')
        case['imported']['costs']['international_freight'].update(basis='observed', observed_at='2026-10-20T12:00:00Z')
        self.assertIn('imported.international_freight_observation_older_than_limit', self.compare(data)['reasons'])

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
