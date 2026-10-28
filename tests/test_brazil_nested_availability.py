import unittest

from china_deals.brazil import compare_brazil
from tests.test_brazil import payload


class NestedAvailabilityTests(unittest.TestCase):
    def test_nested_unavailable_evidence_holds_both_sides(self):
        for side in ('imported', 'brazil'):
            for value in ('out_of_stock', 'OutOfStock', ' OUT-OF-STOCK ',
                          'https://schema.org/OutOfStock', 'HTTP://schema.org/outofstock'):
                for nested in ({'availability': value}, [{'availability': value}]):
                    with self.subTest(side=side, value=value, nested=nested):
                        data = payload()
                        offer = data['cases'][0][side]['offer']
                        offer['availability'] = 'https://schema.org/InStock'
                        offer['offers'] = nested
                        row = compare_brazil(data)['cases'][0]
                        self.assertEqual(row['financial_outcome'], 'needs_review')
                        self.assertIn(side + '_offer_unavailable', row['reasons'])
                        self.assertIsNone(row['savings_amount_brl'])

    def test_outer_unavailable_overrides_nested_in_stock(self):
        for side in ('imported', 'brazil'):
            with self.subTest(side=side):
                data = payload()
                offer = data['cases'][0][side]['offer']
                offer['availability'] = 'OutOfStock'
                offer['offers'] = {'availability': 'https://schema.org/InStock'}
                row = compare_brazil(data)['cases'][0]
                self.assertEqual(row['financial_outcome'], 'needs_review')
                self.assertIn(side + '_offer_unavailable', row['reasons'])

    def test_nested_lists_and_offer_containers_are_checked(self):
        for side in ('imported', 'brazil'):
            with self.subTest(side=side):
                data = payload()
                data['cases'][0][side]['offer']['offers'] = [
                    {'availability': 'InStock'},
                    {'offers': [{'availability': 'https://schema.org/OutOfStock'}]},
                ]
                row = compare_brazil(data)['cases'][0]
                self.assertEqual(row['financial_outcome'], 'needs_review')
                self.assertIn(side + '_offer_unavailable', row['reasons'])

    def test_available_and_unrecognized_values_do_not_create_unavailable_evidence(self):
        for side in ('imported', 'brazil'):
            for value in ('https://schema.org/InStock', 'unknown', None):
                with self.subTest(side=side, value=value):
                    data = payload()
                    data['cases'][0][side]['offer']['offers'] = {'availability': value}
                    row = compare_brazil(data)['cases'][0]
                    self.assertEqual(row['financial_outcome'], 'import_cheaper')
                    self.assertNotIn(side + '_offer_unavailable', row['reasons'])
                    if side == 'imported':
                        self.assertEqual(row['imported']['offer']['availability'], 'unknown')

    def test_imported_specific_unavailable_status_survives_comparison(self):
        for status in ('delisted', 'sold'):
            with self.subTest(status=status):
                data = payload()
                data['cases'][0]['imported']['offer']['availability'] = status
                row = compare_brazil(data)['cases'][0]
                self.assertEqual(row['imported']['offer']['availability'], status)
                self.assertEqual(row['financial_outcome'], 'needs_review')
                data['cases'][0]['imported']['offer'] = row['imported']['offer']
                self.assertEqual(compare_brazil(data)['cases'][0]['imported']['offer']['availability'], status)

    def test_imported_nested_hold_survives_normalized_offer_roundtrip(self):
        data = payload()
        data['cases'][0]['imported']['offer']['offers'] = {'availability': 'OutOfStock'}
        row = compare_brazil(data)['cases'][0]
        self.assertEqual(row['imported']['offer']['availability'], 'unavailable')
        data['cases'][0]['imported']['offer'] = row['imported']['offer']
        row = compare_brazil(data)['cases'][0]
        self.assertEqual(row['financial_outcome'], 'needs_review')
        self.assertIn('imported_offer_unavailable', row['reasons'])


if __name__ == '__main__':
    unittest.main()
