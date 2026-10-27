import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from china_deals import guest
from china_deals.cli import build_parser, run
from china_deals.ranking import rank_offers
from china_deals.refresh import refresh_offers
from tests.test_blibli_public import FIXTURE, ITEM_URL, OBSERVED, PRODUCT_URL, html
from tests.test_refresh import BEFORE, NOW, quote, receipt


class FreshReleaseRegressions(unittest.TestCase):
    def test_refresh_monthly_evidence_cannot_be_ranked_without_product_intent(self):
        for query in (None, 'iPhone 17 Pro Max'):
            source = quote(title='iPhone 17 Pro Max', ranking_exclusions=['possible_deposit_or_installment_price'])
            if query:
                source['intent_query'] = query
            fresh = quote(title='iPhone 17 Pro Max', payment_terms='monthly installment', price_scope='monthly_installment')
            with patch('china_deals.guest.get_guest_item', return_value=receipt(fresh)):
                result = refresh_offers([source], as_of=NOW)
            row = result['items'][0]
            self.assertIsNone(row['price']['amount'])
            self.assertEqual(row['refresh']['status'], 'unpriced')
            self.assertIn('possible_deposit_or_installment_price', row['ranking_exclusions'])
            self.assertFalse(rank_offers([row], query=query, as_of=NOW)['groups'])
            self.assertIsNone(row['price_delta']['amount'])

    def test_all_required_refresh_policies_combine_using_strictest(self):
        for origin in ('envelope', 'original_context', 'returned'):
            policy = {'required': True, 'max_age_hours': '0.25'}
            source = quote(price_freshness_policy={'required': True, 'max_age_hours': '24'})
            payload = {'items': [source]}
            fresh = quote(observed_at=BEFORE)
            if origin == 'envelope':
                payload['price_freshness_policy'] = policy
            elif origin == 'original_context':
                payload['original_context'] = {'price_freshness_policy': policy}
            else:
                fresh['price_freshness_policy'] = policy
            with patch('china_deals.guest.get_guest_item', return_value=receipt(fresh)):
                result = refresh_offers(payload, as_of=NOW)
            row = result['items'][0]
            self.assertEqual(row['price_freshness']['max_age_hours'], '0.25')
            self.assertIsNone(row['price']['amount'])

    def test_state_integration_does_not_erase_script_context_or_overflow(self):
        state = json.loads(FIXTURE.read_text())
        body = html(state)
        for changed in (body.replace('<script>', '<script src="https://example.invalid/x.js">'),
                        body + '<script>window.__PRODUCT_DETAIL_INITIAL_STATE__ = {}'):
            with self.assertRaises(guest._Failure):
                guest._blibli_detail(guest._html(changed), PRODUCT_URL, OBSERVED)

    def test_selected_url_cannot_override_pickup_binding(self):
        state = json.loads(FIXTURE.read_text())
        selected = next(row for row in state['productDetail.product/summary']['options'] if row['selected'])
        selected['url'] = ITEM_URL + '?pickupPointCode=PP-OTHER'
        with self.assertRaises(guest._Failure):
            guest._blibli_detail(guest._html(html(state)), PRODUCT_URL, OBSERVED)

    def test_offline_capture_still_reads_coupon_rules(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'capture.json'
            # Mock capture parsing only; the CLI must still open the requested rules file.
            path.write_text('{}')
            with patch('china_deals.goofish_public.parse_capture', return_value=quote(marketplace='goofish',
                       item_id='123', url='https://www.goofish.com/item?id=123')):
                with self.assertRaises(FileNotFoundError):
                    run(build_parser().parse_args(['detail', 'goofish', '123', '--from-browser-json', str(path),
                        '--coupons-from-json', str(Path(directory) / 'missing.json'), '--currency', 'native']))
