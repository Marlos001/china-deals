import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from china_deals.config import load_config, write_default_config
from china_deals.filters import evaluate_offer, native_plan, validate_filters
from china_deals.fx import annotate_offers, convert_brl, parse_ecb
from china_deals.models import normalize_offer

XML = b'<Envelope><Cube><Cube time="2026-10-26"><Cube currency="BRL" rate="6"/><Cube currency="CNY" rate="8"/><Cube currency="IDR" rate="20000"/><Cube currency="USD" rate="1.2"/></Cube></Cube></Envelope>'


class PreferencesTests(unittest.TestCase):
    def test_guest_and_blibli_product_only_defaults_and_config_override(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'preferences.json'
            write_default_config(path)
            config = load_config(path)
            self.assertTrue(all(value['access'] == 'guest' for value in config['marketplaces'].values()))
            self.assertEqual(config['marketplaces']['blibli']['shipping'], 'excluded')
            with self.assertRaises(FileExistsError):
                write_default_config(path)
            path.write_text(json.dumps({'marketplaces': {'jd': {'shipping': 'manual'}}}))
            self.assertEqual(load_config(path)['marketplaces']['jd']['shipping'], 'manual')
            path.write_text(json.dumps({'marketplaces': {'blibli': {'shipping': 'fansbuy'}}}))
            with self.assertRaises(ValueError):
                load_config(path)

    def test_same_date_ecb_cross_rates_and_blibli_no_freight(self):
        rates = parse_ecb(XML)
        self.assertEqual(convert_brl('100', 'CNY', rates), '75.00')
        self.assertEqual(convert_brl('1000000', 'IDR', rates), '300.00')
        item = normalize_offer('blibli', {'title': 'Laptop', 'price': 'Rp1.000.000', 'url': '/p/test/ps--ABC'})
        with tempfile.TemporaryDirectory() as folder, patch('china_deals.config.config_path', return_value=Path(folder) / 'none'):
            annotate_offers([item], rates, load_config())
        self.assertEqual(item['brl']['product_cost'], '300.00')
        self.assertEqual(item['brl']['shipping_policy'], 'excluded')
        self.assertIsNone(item['brl']['landed_total'])

    def test_incomplete_or_unsafe_fx_data_rejected(self):
        for raw in [XML.replace(b'CNY', b'ABC'), XML.replace(b'rate="8"', b'rate="NaN"'), b'<!DOCTYPE test>'+XML]:
            with self.assertRaises(ValueError):
                parse_ecb(raw)

    def test_filters_distinguish_native_plan_and_local_unknown(self):
        plan = native_plan('goofish', '幻16', {'min_price': '4000', 'city': '深圳', 'condition': 'new'})
        self.assertIn('--min-price', plan['opencli_argv'])
        self.assertEqual(plan['submitted_native_filters'], [])
        self.assertIn('condition', plan['unverified_or_local_filters'])
        offer = normalize_offer('jd', {'title': 'Example', 'sku': '123', 'price': None})
        self.assertEqual(evaluate_offer(offer, {'min_price': '100'})['status'], 'unknown')
        offer['price']['amount'] = '50'
        self.assertEqual(evaluate_offer(offer, {'min_price': '100'})['status'], 'excluded')
        with self.assertRaises(ValueError):
            validate_filters({'min_price': 200, 'max_price': 100})


if __name__ == '__main__':
    unittest.main()
