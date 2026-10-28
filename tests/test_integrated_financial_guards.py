import copy
import json
import unittest
from decimal import localcontext

from china_deals.brazil import compare_brazil
from china_deals.models import normalize_offer
from china_deals.ranking import rank_offers
from tests.test_brazil import payload


class IntegratedFinancialGuards(unittest.TestCase):
    def test_specific_unavailable_status_survives_nested_claims_and_reimport(self):
        for status in ('delisted', 'sold'):
            with self.subTest(status=status):
                source = copy.deepcopy(payload()['cases'][0]['imported']['offer'])
                nested = {'availability': 'https://schema.org/OutOfStock'}
                source.update(availability=status, offers=nested,
                              availability_observations=['https://schema.org/InStock'])
                for _ in range(3):
                    normalized = normalize_offer('jd', source)
                    self.assertEqual(normalized['availability'], status)
                    self.assertIsNone(normalized['price']['amount'])
                    self.assertEqual(normalized['offers'], nested)
                    self.assertIn('https://schema.org/InStock', normalized['availability_observations'])
                    self.assertIn(status, normalized['availability_observations'])
                    result = rank_offers([normalized])
                    self.assertFalse(result['groups'])
                    self.assertEqual(len(result['unranked']), 1)
                    source = json.loads(json.dumps(result['unranked'][0]))

    def test_nested_availability_survives_normalize_rank_export_and_reimport(self):
        for nested in ({'availability': 'https://schema.org/OutOfStock'},
                       [{'availability': 'InStock'}, {'offers': [{'availability': 'OutOfStock'}]}]):
            with self.subTest(nested=nested):
                source = copy.deepcopy(payload()['cases'][0]['imported']['offer'])
                source.update(availability='https://schema.org/InStock', offers=nested)
                normalized = normalize_offer('jd', source)
                self.assertEqual(normalized['availability'], 'unavailable')
                self.assertIn('https://schema.org/InStock', normalized['availability_observations'])
                self.assertEqual(normalized['offers'], nested)
                for _ in range(3):
                    result = rank_offers([normalized])
                    self.assertFalse(result['groups'])
                    self.assertEqual(len(result['unranked']), 1)
                    normalized = json.loads(json.dumps(result['unranked'][0]))
                    self.assertEqual(normalized['availability'], 'unavailable')
                    self.assertEqual(normalized['offers'], nested)
                    self.assertIn('https://schema.org/InStock', normalized['availability_observations'])

    def test_available_offers_rank_and_compare_on_both_sides(self):
        data = payload()
        for side in ('imported', 'brazil'):
            data['cases'][0][side]['offer']['offers'] = {'availability': 'https://schema.org/InStock'}
        result = compare_brazil(data)['cases'][0]
        self.assertEqual(result['status'], 'comparable')
        self.assertEqual(len(rank_offers([result['imported']['offer']])['groups']['CNY']), 1)
        for side in ('imported', 'brazil'):
            changed = copy.deepcopy(data)
            changed['cases'][0][side]['offer']['offers'] = {'availability': 'https://schema.org/OutOfStock'}
            self.assertIn(side + '_offer_unavailable', compare_brazil(changed)['cases'][0]['reasons'])

    def test_brazil_arithmetic_independent_of_caller_context(self):
        data = payload()
        data['cases'][0]['brazil']['offer']['price']['amount'] = '12345.67'
        data['cases'][0]['brazil']['costs']['delivery']['amount'] = '123.45'
        expected = compare_brazil(data)
        with localcontext() as context:
            context.prec = 4
            context.rounding = 'ROUND_DOWN'
            actual = compare_brazil(data)
        self.assertEqual(actual, expected)
        self.assertEqual(actual['cases'][0]['brazil']['complete_total_brl'], '12469.12')

    def test_out_of_bounds_values_raise_value_error(self):
        for side, field in (('brazil', 'price'), ('brazil', 'cost'), ('imported', 'cost'), ('imported', 'price')):
            with self.subTest(side=side, field=field):
                data = payload()
                if field == 'price' and side == 'brazil':
                    data['cases'][0][side]['offer']['price']['amount'] = '12345678901234567890123456789'
                elif field == 'price':
                    data['cases'][0][side]['offer']['price'] = '12345678901234567890123456789'
                else:
                    cost = 'delivery' if side == 'brazil' else 'taxes'
                    data['cases'][0][side]['costs'][cost]['amount'] = '12345678901234567890123456789'
                with localcontext() as context:
                    context.prec = 4
                    with self.assertRaises(ValueError):
                        compare_brazil(data)


if __name__ == '__main__':
    unittest.main()
