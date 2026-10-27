import json
import unittest
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from china_deals.shipping import assess_import, estimate_landed_cost, fansbuy_quotes, normalize_fansbuy_quotes


def route(**overrides):
    data = {'shipping_area_id': 1, 'shipping_id': 2, 'shipping_name': 'Test', 'enabled': 1,
            'special': '{"ischarged":1,"iscell":0}', 'min_weight': '100', 'max_weight': '2000',
            'max_anySide': '60', 'max_sumSide': '100', 'sidelength': '0', 'v_percent': '8000',
            'side_v_percent': '0', 'volume_weight_limit': '2000', 'total_fee': 30,
            'travel_time': '10-20', 'discount_display': '26.00'}
    data.update(overrides)
    return data


def normalize(row, **kwargs):
    return normalize_fansbuy_quotes({'code': 0, 'data': [row]}, 1000, (20, 20, 15), **kwargs)


class ShippingTests(unittest.TestCase):
    def test_captured_live_shape(self):
        path = Path(__file__).resolve().parent / 'fixtures/fansbuy-estimates-2026-10-27.json'
        with path.open() as f:
            capture = json.load(f)
        self.assertEqual(capture['provenance']['request']['country'], '29')
        self.assertEqual(capture['provenance']['request']['volume'], 6000)
        payload = capture['response']
        result = normalize_fansbuy_quotes(payload, 1000, (20, 20, 15), [])
        self.assertEqual(len(result['quotes']) + len(result['rejected']), 15)
        self.assertEqual(result['quotes'][0]['total_fee'], '206.58')
        disabled = next(q for q in result['rejected'] if q['shipping_area_id'] == 1678)
        self.assertIn('route disabled by is_disable', disabled['reasons'])
        self.assertIsNone(result['source_observed_at'])
        json.dumps(result)

    def test_disabled_and_battery_are_rejected_and_preserved(self):
        result = normalize(route(enabled=0), categories=['Battery'])
        self.assertFalse(result['quotes'])
        self.assertIn('route disabled', result['rejected'][0]['reasons'])
        self.assertIn('category not accepted: Battery', result['rejected'][0]['reasons'])
        self.assertEqual(result['rejected'][0]['total_fee'], '30.00')
        self.assertEqual(len(normalize(route(), categories=['Electric'])['quotes']), 1)

    def test_unknown_constraints_and_size(self):
        for modified, categories, reason in [
            (route(special='bad'), ['Battery'], 'unknown constraint: Battery (iscell)'),
            (route(), None, 'unknown constraint: product categories not supplied'),
            (route(max_anySide=None), [], 'unknown constraint: max_anySide'),
            (route(), ['unrecognized'], 'unknown category: unrecognized'),
            (route(max_sumSide='40'), [], 'maximum sum of sides exceeded'),
            (route(v_percent='1000', volume_weight_limit='1000'), [], 'volumetric weight limit exceeded'),
        ]:
            result = normalize(modified, categories=categories)
            self.assertIn(reason, result['rejected'][0]['reasons'])
        self.assertIn('unknown constraint: dimensions required',
                      normalize_fansbuy_quotes({'code': 0, 'data': [route()]}, 1000, categories=[])['rejected'][0]['reasons'])

    def test_invalid_inputs(self):
        for weight in [0, -1, float('nan'), True]:
            with self.assertRaises(ValueError):
                normalize_fansbuy_quotes({'code': 0, 'data': []}, weight)
        with self.assertRaises(ValueError):
            normalize_fansbuy_quotes({'code': 1, 'data': []}, 1)

    @patch('china_deals.shipping._post')
    def test_live_resolves_region_and_sends_volume(self, post):
        post.side_effect = [{'code': 0, 'data': {'en': [{'region_id': 29, 'c_code': 'BR'}],
                                                   'cn': [{'region_id': 29, 'c_code': 'BR'}]}},
                            {'code': 0, 'data': [route()]}]
        result = fansbuy_quotes(1000, (20, 20, 15), [])
        self.assertEqual(post.call_args_list[1].args[1], {'weight': 1000.0, 'volume': 6000.0,
                                                            'currency': 'CNY', 'price': 0, 'country': '29'})
        self.assertIsNotNone(result['source_observed_at'])
        json.dumps(result)

    def test_landed_cost_gross_up_and_fees(self):
        result = estimate_landed_cost('100', '20', '1', '5', '.20', '10', '5', '5')
        self.assertEqual(result['customs_value_brl'], '135.00')
        self.assertEqual(result['import_duty_brl'], '81.00')
        self.assertEqual(result['icms_brl'], '54.00')
        self.assertEqual(result['total_brl'], '275.00')
        json.dumps(result)

    def test_rates_and_limits(self):
        for kwargs in [{'cny_brl': '0'}, {'usd_brl': '-1'}, {'icms_rate': '1'},
                       {'icms_rate': 'NaN'}, {'goods_cny': '15001'}]:
            args = dict(goods_cny='100', freight_cny='0', cny_brl='1', usd_brl='5', icms_rate='.2')
            args.update(kwargs)
            with self.assertRaises(ValueError):
                estimate_landed_cost(**args)
        self.assertEqual(estimate_landed_cost('15000', '0', '1', '5', '.2')['customs_value_usd'], '3000.00')

    def test_current_prc_threshold_and_deduction_are_conditional(self):
        low = estimate_landed_cost('250', '0', '1', '5', '.2', remessa_conforme=True)
        self.assertEqual(Decimal(low['import_duty_brl']), Decimal('0'))
        self.assertEqual(low['icms_brl'], '62.50')
        self.assertFalse(low['shipment_eligibility_verified'])
        edge = estimate_landed_cost('250.05', '0', '1', '5', '.2', remessa_conforme=True)
        self.assertEqual(edge['import_duty_brl'], '0.03')
        high = estimate_landed_cost('500', '0', '1', '5', '.2', remessa_conforme=True)
        self.assertEqual(high['import_duty_brl'], '150.00')
        self.assertEqual(high['import_duty_deduction_usd'], '30')
        self.assertEqual(high['policy']['prc_effective_from'], '2026-05-12')
        normal = estimate_landed_cost('250', '0', '1', '5', '.2')
        self.assertEqual(normal['import_duty_brl'], '150.00')

    def test_restrictions_do_not_claim_clearance(self):
        self.assertEqual(assess_import('used', ['Battery'], '1234.56.78')['status'], 'manual_review')
        json.dumps(assess_import())

    def test_zero_fee_and_unknown_volume_divisor(self):
        self.assertIn('unknown quote: total_fee', normalize(route(total_fee=0), categories=[])['rejected'][0]['reasons'])
        result = normalize(route(v_percent=0, volume_weight_limit=1000), categories=[])
        self.assertIn('unknown constraint: volumetric divisor for volume weight limit', result['rejected'][0]['reasons'])

    def test_source_fields_and_decimal_are_json_safe(self):
        result = normalize(route(shipping_id=Decimal('2.5'), travel_time=Decimal('3.5'),
                                 shipping_desc='description', shipping_tip='tip', mustVacuum=1), categories=[])
        quote = result['quotes'][0]
        self.assertEqual(quote['shipping_id'], '2.5')
        self.assertEqual(quote['carrier_description'], 'description')
        self.assertEqual(quote['carrier_tip'], 'tip')
        self.assertEqual(quote['packaging']['mustVacuum'], 1)
        self.assertIn('special', quote['carrier_flags'])
        self.assertIn('surcharge', quote['source_constraints'])
        json.dumps(result, allow_nan=False)
        with self.assertRaises(ValueError):
            normalize(route(shipping_id=float('nan')), categories=[])

    @patch('china_deals.shipping.urlopen')
    def test_network_json_is_bounded_and_strict(self, urlopen):
        from china_deals.shipping import _post
        for body in (b'{"x":NaN}', b'{"x":Infinity}', b' ' * (2 * 1024 * 1024 + 1)):
            urlopen.return_value.__enter__.return_value = BytesIO(body)
            with self.assertRaises(ValueError):
                _post('x', {}, 1)
        urlopen.return_value.__enter__.return_value = BytesIO(b'{"x":1.5}')
        self.assertEqual(_post('x', {}, 1)['x'], Decimal('1.5'))

    @patch('china_deals.shipping._post', return_value={'code': 0, 'data': []})
    def test_bad_area_shape_is_value_error(self, post):
        with self.assertRaises(ValueError):
            fansbuy_quotes(1000)

    def test_cost_threshold_rounding_and_assumptions(self):
        with self.assertRaises(ValueError):
            estimate_landed_cost('0', '0', '1', '5', '.2')
        with self.assertRaises(ValueError):
            estimate_landed_cost('14999', '0', '1', '5', '.2', domestic_cny='2')
        result = estimate_landed_cost('1.005', '0', '1', '5', '.13', agent_fee_cny='.005')
        lines = sum(Decimal(result[k]) for k in ('customs_value_brl', 'import_duty_brl', 'icms_brl', 'agent_fee_brl'))
        self.assertEqual(lines, Decimal(result['total_brl']))
        self.assertTrue(result['assumptions']['duty_rate']['policy_page_verified'])
        self.assertFalse(result['shipment_eligibility_verified'])
        self.assertIn('source_url', result['assumptions']['rts_limit_usd'])

    def test_specific_reviews_and_ncm(self):
        result = assess_import('used', ['Battery', 'Electric', 'cosmetics', 'food', 'Knives', 'liquid', 'magnetic'], '1234.56.78')
        topics = ' '.join(x['topic'] for x in result['sources'])
        for term in ('used goods', 'dangerous-goods', 'Anatel', 'Anvisa', 'knife'):
            self.assertIn(term, topics)
        self.assertEqual({x['source_type'] for x in result['sources']}, {'government', 'transport', 'carrier'})
        self.assertTrue(all(not x['verified'] and x['checked_at'] is None for x in result['sources']))
        for invalid in ('1234', '1234567a', '12.345.678', ''):
            with self.assertRaises(ValueError):
                assess_import(ncm=invalid)
        self.assertEqual(assess_import(ncm='12345678')['status'], 'manual_review')


if __name__ == '__main__':
    unittest.main()
