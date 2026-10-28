import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from china_deals.brazil import IMPORT_COSTS, compare_brazil
from china_deals.config import DEFAULT_CONFIG
from china_deals.models import normalize_offer

AS_OF = '2026-10-27T12:00:00Z'
FX = {'base': 'BRL', 'rate_date': '2026-10-27', 'source': 'synthetic.example.invalid',
      'brl_per_unit': {'CNY': '0.75', 'IDR': '0.0003', 'USD': '5.00'}}


def money(amount='0', currency='BRL'):
    return {'amount': amount, 'currency': currency, 'basis': 'scenario'}


def payload():
    identity = {'model': 'SYNTHETIC Model A', 'condition': 'new',
                'variant': {'gpu': 'SYNTHETIC GPU', 'ram_gb': 16, 'storage_gb': 512}}
    return {'as_of': AS_OF, 'fx': copy.deepcopy(FX), 'cases': [{
        'id': 'synthetic-case',
        'imported': {'offer': {'marketplace': 'jd', 'sku': '123', 'title': 'SYNTHETIC Model A',
                              'price': '¥100', 'currency': 'CNY', 'condition': 'new',
                              'source_mode': 'guest_product_page', 'observed_at': AS_OF,
                              'payment_method': 'synthetic wire transfer'},
                     'identity': copy.deepcopy(identity), 'costs': {k: money() for k in IMPORT_COSTS}},
        'brazil': {'offer': {'title': 'SYNTHETIC Model A', 'url': 'https://retailer.example.invalid/fake-product',
                            'price': {'amount': '150', 'currency': 'BRL', 'basis': 'displayed'},
                            'source_mode': 'retailer_product_page', 'observed_at': AS_OF,
                            'availability': 'source_claimed_available', 'condition': 'new', 'payment_method': 'Pix'},
                   'identity': copy.deepcopy(identity), 'costs': {'delivery': money('10'), 'fees': money()}},
        'equivalence': {'status': 'confirmed', 'note': 'Synthetic exact identities supplied for testing only.'},
        'import_eligibility': {'status': 'confirmed', 'note': 'Synthetic assertion, no legal clearance.'},
    }]}


class BrazilTests(unittest.TestCase):
    def setUp(self):
        self.data = payload()
        self.case = self.data['cases'][0]

    def compare(self):
        return compare_brazil(self.data, config=copy.deepcopy(DEFAULT_CONFIG))['cases'][0]

    def test_complete_positive_scenario_and_no_discount(self):
        self.case['imported']['offer']['potential_coupon'] = {'amount': '70', 'currency': 'BRL'}
        self.case['brazil']['offer']['cashback'] = '50'
        result = self.compare()
        self.assertEqual(result['status'], 'comparable')
        self.assertEqual(result['financial_outcome'], 'import_cheaper')
        self.assertEqual(result['imported']['landed_total_brl'], '75.00')
        self.assertEqual(result['brazil']['complete_total_brl'], '160.00')
        self.assertEqual(result['savings_amount_brl'], '85.00')
        self.assertEqual(result['savings_percent'], '53.13')
        self.assertEqual(result['brazil']['offer']['payment_method'], 'Pix')
        self.assertEqual(result['imported']['offer']['payment_method'], 'synthetic wire transfer')

    def test_negative_and_equal_scenarios(self):
        for taxes, outcome, savings in [('100', 'brazil_cheaper', '-15.00'), ('85', 'equal', '0.00')]:
            with self.subTest(taxes=taxes):
                self.case['imported']['costs']['taxes'] = money(taxes)
                result = self.compare()
                self.assertEqual(result['financial_outcome'], outcome)
                self.assertEqual(result['savings_amount_brl'], savings)

    def test_new_used_and_component_mismatch_cannot_be_overridden(self):
        for field, value in [('condition', 'used'), ('model', 'Different'),
                             ('variant', {'gpu': 'Other GPU', 'ram_gb': 16, 'storage_gb': 512})]:
            with self.subTest(field=field):
                self.case['brazil']['identity'] = copy.deepcopy(payload()['cases'][0]['brazil']['identity'])
                self.case['brazil']['identity'][field] = value
                result = self.compare()
                self.assertEqual(result['financial_outcome'], 'needs_review')
                self.assertFalse(result['identity']['matches'])
                self.assertIsNone(result['savings_amount_brl'])

    def test_offer_condition_or_hardware_conflict_holds(self):
        self.case['imported']['offer']['condition'] = 'used'
        self.case['imported']['offer']['hardware'] = {'gpu': 'Other GPU'}
        result = self.compare()
        self.assertIn('imported.offer_condition_conflict', result['reasons'])
        self.assertIn('imported.offer_gpu_conflict', result['reasons'])

    def test_missing_identity_and_unconfirmed_equivalence(self):
        for key, value in [('variant', {}), ('condition', 'unknown'), ('model', '')]:
            with self.subTest(key=key):
                self.case['imported']['identity'] = copy.deepcopy(self.case['brazil']['identity'])
                self.case['imported']['identity'][key] = value
                self.assertEqual(self.compare()['status'], 'needs_review')
        self.case['imported']['identity'] = copy.deepcopy(self.case['brazil']['identity'])
        self.case['equivalence']['status'] = 'unknown'
        self.assertIn('equivalence_not_confirmed', self.compare()['reasons'])

    def test_foreign_currency_mismatch(self):
        self.case['imported']['offer']['currency'] = 'USD'
        result = self.compare()
        self.assertIsNone(result['imported']['product_price_brl'])
        self.assertIsNone(result['imported']['landed_total_brl'])
        self.assertEqual(result['status'], 'needs_review')

    def test_conflicting_currency_envelopes_cannot_hide_mismatch(self):
        self.case['imported']['offer']['price'] = {'amount': '100', 'raw': '100',
                                                  'currency': 'USD', 'basis': 'displayed'}
        result = self.compare()
        self.assertIsNone(result['imported']['product_price_brl'])
        self.assertIn('foreign_explicit_currency_conflict', result['reasons'])
        self.case['brazil']['offer']['currency'] = 'USD'
        self.assertIsNone(self.compare()['brazil']['product_price_brl'])

    def test_subcent_price_does_not_create_a_zero_price_winner(self):
        self.case['brazil']['offer']['price']['amount'] = '0.001'
        result = self.compare()
        self.assertEqual(result['status'], 'needs_review')
        self.assertIsNone(result['brazil']['complete_total_brl'])

    def test_missing_freight_and_taxes_budget(self):
        del self.case['imported']['costs']['international_freight']
        self.case['imported']['costs']['taxes'] = None
        result = self.compare()
        self.assertEqual(result['missing_costs']['imported'], ['international_freight', 'taxes'])
        self.assertEqual(result['imported']['known_subtotal_brl'], '75.00')
        self.assertEqual(result['break_even_remaining_cost_budget_brl'], '85.00')
        self.assertIsNone(result['imported']['landed_total_brl'])
        self.assertIsNone(result['savings_percent'])

    def test_negative_budget_retained(self):
        self.case['imported']['costs']['taxes'] = money('100')
        del self.case['imported']['costs']['international_freight']
        self.assertEqual(self.compare()['break_even_remaining_cost_budget_brl'], '-15.00')

    def test_brazil_missing_delivery_or_fees(self):
        for name in ('delivery', 'fees'):
            with self.subTest(name=name):
                self.case['brazil']['costs'] = {'delivery': money(), 'fees': money()}
                del self.case['brazil']['costs'][name]
                result = self.compare()
                self.assertIsNone(result['brazil']['complete_total_brl'])
                self.assertIsNone(result['break_even_remaining_cost_budget_brl'])
                self.assertIn(name, result['missing_costs']['brazil'])

    def test_blibli_exclusion_does_not_waive_taxes_or_fees(self):
        self.case['imported']['offer'] = {'marketplace': 'blibli', 'title': 'SYNTHETIC Model A',
            'url': 'https://www.blibli.com/p/synthetic/ps--FAKE', 'price': 'Rp100.000',
            'source_mode': 'guest_product_page', 'observed_at': AS_OF}
        del self.case['imported']['costs']['international_freight']
        self.case['imported']['costs']['taxes'] = None
        result = self.compare()
        self.assertEqual(result['imported']['excluded_costs'], ['international_freight'])
        self.assertEqual(result['missing_costs']['imported'], ['international_freight', 'taxes'])
        self.assertIsNone(result['imported']['landed_total_brl'])
        self.case['imported']['costs']['taxes'] = money('10')
        self.assertIsNone(self.compare()['imported']['landed_total_brl'])
        config = copy.deepcopy(DEFAULT_CONFIG)
        config['marketplaces']['blibli']['shipping'] = 'manual'
        result = compare_brazil(self.data, config=config)['cases'][0]
        self.assertIn('international_freight', result['missing_costs']['imported'])

    def test_rounding_and_mixed_cost_currencies(self):
        self.data['fx']['brl_per_unit']['CNY'] = '0.74505'
        self.case['imported']['costs']['taxes'] = money('1.001', 'USD')
        self.case['imported']['costs']['domestic_freight'] = money('1', 'CNY')
        result = self.compare()
        self.assertEqual(result['imported']['product_price_brl'], '74.51')
        self.assertEqual(result['imported']['landed_total_brl'], '80.27')

    def test_stale_future_and_unknown_prices_never_win(self):
        for stamp in ('2026-10-25T12:00:00Z', '2026-10-28T12:00:00Z', None):
            with self.subTest(stamp=stamp):
                self.case['imported']['offer']['observed_at'] = stamp
                result = self.compare()
                self.assertEqual(result['financial_outcome'], 'needs_review')
                self.assertIsNone(result['savings_amount_brl'])
                self.assertIsNotNone(result['conditional_math'])

    def test_cached_catalog_math_never_promotes_price(self):
        offer = self.case['imported']['offer']
        offer['source_mode'] = 'connector_product_open_cached'
        offer['source_detail'] = {'catalog_observation': {'amount': '100', 'currency': 'CNY', 'crawl_age': 'today'}}
        result = self.compare()
        self.assertIsNone(result['imported']['offer']['price']['amount'])
        self.assertIsNone(result['imported']['landed_total_brl'])
        self.assertEqual(result['conditional_math']['import_total_brl'], '75.00')
        self.assertEqual(result['conditional_math']['basis'], 'unverified_source_observation')
        self.assertEqual(result['status'], 'needs_review')
        offer['source_detail']['catalog_observation']['currency'] = 'USD'
        self.assertIsNone(self.compare()['conditional_math'])

    def test_cached_or_stale_brazil_never_wins(self):
        for mode, stamp in [('category_card', AS_OF), ('retailer_product_page', '2026-10-01T00:00:00Z')]:
            self.case['brazil']['offer'].update(source_mode=mode, observed_at=stamp)
            self.assertEqual(self.compare()['status'], 'needs_review')

    def test_eligibility_is_explicit_hold_with_conditional_math(self):
        for status in ('unknown', 'manual_review', 'restricted'):
            with self.subTest(status=status):
                self.case['import_eligibility']['status'] = status
                result = self.compare()
                self.assertTrue(result['decision_hold'])
                self.assertIn('import_eligibility_' + status, result['decision_holds'])
                self.assertEqual(result['financial_outcome'], 'needs_review')
                self.assertIsNotNone(result['conditional_math'])

    def test_brazil_price_strict_currency_full_total(self):
        original = copy.deepcopy(self.case['brazil']['offer']['price'])
        for price in [dict(original, currency='USD'), dict(original, amount='10x 15'),
                      dict(original, amount='1.500,00'), dict(original, amount='1e2'),
                      dict(original, amount='0'), dict(original, amount=True),
                      dict(original, basis='installment'), dict(original, scope='deposit')]:
            with self.subTest(price=price):
                self.case['brazil']['offer']['price'] = price
                self.assertIsNone(self.compare()['brazil']['product_price_brl'])
        self.case['brazil']['offer']['price'] = original
        self.case['brazil']['offer']['title'] = 'Entrada SYNTHETIC Model A'
        self.assertIsNone(self.compare()['brazil']['product_price_brl'])

    def test_bad_costs_raise_instead_of_silent_zeros(self):
        for cost in [money('-1'), money('NaN'), money('1e2'), money('1', 'ZZZ'),
                     money(True), dict(money(), basis='potential_coupon')]:
            with self.subTest(cost=cost), self.assertRaises(ValueError):
                self.case['imported']['costs']['taxes'] = cost
                self.compare()

    def test_missing_fx_is_unknown_and_normalized_offer_roundtrip(self):
        offer = self.case['imported']['offer']
        self.case['imported']['offer'] = normalize_offer('jd', offer, AS_OF)
        self.assertEqual(self.compare()['imported']['product_price_brl'], '75.00')
        del self.data['fx']
        result = self.compare()
        self.assertIsNone(result['imported']['product_price_brl'])
        self.assertEqual(result['status'], 'needs_review')

    def test_pure_offline_no_mutation_deterministic_overrides(self):
        original = copy.deepcopy(self.data)
        with patch('urllib.request.urlopen', side_effect=AssertionError('network forbidden')):
            first = self.compare()
            self.assertEqual(first, self.compare())
        self.assertEqual(original, self.data)
        result = compare_brazil(self.data, config=DEFAULT_CONFIG, as_of='2026-10-29T12:00:00Z')['cases'][0]
        self.assertEqual(result['status'], 'needs_review')
        json.dumps(result, allow_nan=False)

    def test_synthetic_example(self):
        path = Path(__file__).parents[1] / 'examples/brazil-comparison.synthetic.json'
        example = json.loads(path.read_text())
        result = compare_brazil(example, config=DEFAULT_CONFIG)
        self.assertEqual(len(result['cases']), 3)
        self.assertEqual(result['cases'][0]['financial_outcome'], 'import_cheaper')
        self.assertEqual(result['cases'][1]['financial_outcome'], 'brazil_cheaper')
        self.assertEqual(result['cases'][2]['financial_outcome'], 'needs_review')


if __name__ == '__main__':
    unittest.main()
