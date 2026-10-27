import unittest

from china_deals.brazil import compare_brazil
from china_deals.products import transaction_scope_warnings
from china_deals.ranking import rank_offers
from tests.test_brazil import payload


class TransactionScopeBoundaries(unittest.TestCase):
    def test_model_suffix_and_memory_kit_are_not_payment_evidence(self):
        for title in ('NVIDIA RTX 5070 Ti MSI VENTUS 3X OC 16GB',
                      'ROG Zephyrus G16 2x16GB RAM 1TB SSD'):
            self.assertEqual(transaction_scope_warnings({'title': title}), [])
        row = {'marketplace': 'jd', 'sku': '123', 'title': 'NVIDIA RTX 5070 Ti MSI VENTUS 3X OC 16GB',
               'price': '100', 'url': 'https://item.jd.com/123.html'}
        self.assertTrue(rank_offers([row], query='RTX 5070 Ti')['groups'])

    def test_payment_amount_and_remaining_balance_are_withheld(self):
        for extra in ({'payment_method': '12x R$150,00'},
                      {'selected_variant': 'monthly installment'},
                      {'price': {'priceDisplay': '100', 'scope': 'remaining balance only'}}):
            row = {'marketplace': 'jd', 'sku': '123', 'title': 'Sony WH-1000XM6',
                   'price': '100', 'url': 'https://item.jd.com/123.html', **extra}
            result = rank_offers([row], query='Sony WH-1000XM6')
            self.assertFalse(result['groups'])
            self.assertIsNone(result['unranked'][0]['price']['amount'])

    def test_brazil_comparison_does_not_treat_gpu_3x_as_payment(self):
        scenario = payload()
        scenario['cases'][0]['imported']['offer']['title'] += ' MSI VENTUS 3X OC'
        result = compare_brazil(scenario)['cases'][0]
        self.assertEqual(result['financial_outcome'], 'import_cheaper')

    def test_currency_amount_installment_spellings_hold_brazil_decisions(self):
        for payment in ('12x Rp.100', '12x 100 CNY', '12x de R$ 150', '12 x ¥100'):
            with self.subTest(payment=payment):
                row = {'marketplace': 'jd', 'sku': '123', 'title': 'Sony WH-1000XM6',
                       'price': '100', 'payment_terms': payment}
                result = rank_offers([row], query='Sony WH-1000XM6')
                self.assertFalse(result['groups'])
                self.assertIsNone(result['unranked'][0]['price']['amount'])
                scenario = payload()
                scenario['cases'][0]['brazil']['offer']['payment_method'] = payment
                comparison = compare_brazil(scenario)['cases'][0]
                self.assertEqual(comparison['financial_outcome'], 'needs_review')
                self.assertIsNone(comparison['savings_amount_brl'])
