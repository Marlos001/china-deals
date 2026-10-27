import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from china_deals.cli import main


class CouponCliTests(unittest.TestCase):
    def invoke(self, argv):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(argv)
        return code, json.loads(output.getvalue())

    def test_listing_sale_not_double_discounted_and_context_stays_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            offers = root / 'offers.json'
            offers.write_text(json.dumps([{'marketplace': 'blibli', 'title': 'Laptop',
                'price': '38023030', 'url': 'https://www.blibli.com/p/laptop/ps--ABC',
                'source_mode': 'user_observation'}]))
            rules = root / 'rules.json'
            rules.write_text(json.dumps({'campaigns': [{'id': 'unverified-bank', 'currency': 'IDR',
                'discount': {'percent': 10}, 'cap': 75000, 'marketplace': 'blibli',
                'requires': {'payment_method': 'specified_bank'}}]}))
            code, result = self.invoke(['coupons', str(offers), '--rules', str(rules), '--currency', 'native'])
            self.assertEqual(code, 0)
            item = result['offers'][0]
            self.assertEqual(item['price']['amount'], '38023030')
            self.assertIsNone(item['coupon_estimates']['best_eligible'])
            campaign = item['coupon_estimates']['campaigns'][0]
            self.assertEqual(campaign['status'], 'potential')
            self.assertEqual(campaign['discount_amount'], '75000')
            self.assertEqual(campaign['amount_due'], '37948030')

    @patch('china_deals.cli.read_json')
    def test_rank_coupon_annotation_and_brl_scope(self, reader):
        rules = {'as_of': '2026-10-27', 'campaigns': [{'id': 'example', 'currency': 'CNY',
            'discount': {'amount': 10}, 'confirmed': True, 'eligibility': 'confirmed',
            'source_url': 'https://example.org/synthetic', 'observed_at': '2026-10-27'}]}
        reader.side_effect = [
            [{'marketplace': 'jd', 'title': 'Laptop', 'sku': '123', 'price': '100'}], rules,
            {'base': 'BRL', 'rate_date': '2026-10-26', 'brl_per_unit': {'CNY': '0.8', 'IDR': '0.0003', 'USD': '5'}}]
        code, result = self.invoke(['rank', 'offers', '--coupons-from-json', 'rules', '--fx-from-json', 'fx'])
        self.assertEqual(code, 0)
        item = result['groups']['CNY'][0]
        self.assertEqual(item['price']['amount'], '100')
        self.assertEqual(item['brl']['product_cost'], '80.00')
        self.assertEqual(item['coupon_estimates']['campaigns'][0]['amount_due_brl'], '72.00')
        self.assertFalse(item['coupon_estimates']['independently_verified'])

    @patch('china_deals.cli.read_json')
    def test_mismatched_native_blibli_id_cannot_grant_coupon(self, reader):
        reader.side_effect = [
            [{'marketplace': 'blibli', 'title': 'Laptop', 'item_id': 'RIGHT-123',
              'price': '100000', 'url': 'https://www.blibli.com/p/laptop/ps--OTHER-456'}],
            {'campaigns': [{'currency': 'IDR', 'marketplace': 'blibli', 'product_ids': ['RIGHT-123'],
              'discount': {'amount': 10000}, 'confirmed': True, 'eligibility': 'confirmed',
              'source_url': 'https://example.org/synthetic', 'observed_at': '2026-10-27'}]}]
        code, result = self.invoke(['coupons', 'offers', '--rules', 'rules', '--currency', 'native'])
        self.assertEqual(code, 0)
        self.assertIsNone(result['offers'][0]['price']['amount'])
        self.assertIsNone(result['offers'][0]['coupon_estimates']['best_eligible'])

    def test_schema_advertises_offline_coupons(self):
        _, result = self.invoke(['schema'])
        self.assertIn('coupons', result['commands'])


if __name__ == '__main__':
    unittest.main()
