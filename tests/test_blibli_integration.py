import copy
import unittest
from unittest.mock import patch

from china_deals import guest
from china_deals.models import normalize_offer
from china_deals.refresh import refresh_offers
from tests.test_blibli_public import FIXTURE, ITEM_URL, OBSERVED, PRODUCT_URL, html


class BlibliIntegrationTests(unittest.TestCase):
    def setUp(self):
        import json
        self.state = json.loads(FIXTURE.read_text())

    def test_guest_primary_state_reads_one_bound_selected_quote(self):
        with patch('china_deals.guest._fetch', return_value=(html(self.state), PRODUCT_URL)):
            receipt = guest.get_guest_item('blibli', PRODUCT_URL)
        self.assertEqual(receipt['status'], 'ok')
        item = normalize_offer('blibli', receipt['items'][0], receipt['items'][0]['observed_at'])
        self.assertEqual(item['price']['amount'], '8799000')
        self.assertIn('Warna: Midnight', item['variant'])
        self.assertEqual(item['source_detail']['fulfillment_claims']['delivery'], 'UNAVAILABLE')

    def test_selected_pickup_identity_survives_guest_refresh(self):
        url = ITEM_URL + '?pickupPointCode=PP-3460337'
        self.assertEqual(guest._product_url('blibli', url + '&utm_source=test'), url)
        with patch('china_deals.guest._fetch', return_value=(html(self.state), url)):
            result = refresh_offers([{'marketplace': 'blibli', 'url': url}])
        row = result['items'][0]
        self.assertEqual(row['refresh']['status'], 'refreshed')
        self.assertEqual(row['url'], url)
        self.assertEqual(row['price']['amount'], '8799000')
        self.assertIn('Midnight', row['selected_variant'])
        self.assertEqual(str(row['discount_claims']['claims']['original_price']), '8999000')

    def test_conflicting_state_cannot_fallback_to_other_prices(self):
        state = copy.deepcopy(self.state)
        state['productDetail.product/summary']['itemSku'] += '9'
        with patch('china_deals.guest._fetch', return_value=(html(state), PRODUCT_URL)):
            result = guest.get_guest_item('blibli', PRODUCT_URL)
        self.assertEqual(result['status'], 'unavailable')
        self.assertFalse(result['items'])

    def test_parser_replay_uses_original_observation_time(self):
        result = guest._blibli_detail(guest._html(html(self.state)), PRODUCT_URL, OBSERVED)
        self.assertEqual(result[0]['observed_at'], OBSERVED)
        for suffix in ('?pickupPointCode=', '?pickupPointCode=PP-A&pickupPointCode=PP-B'):
            self.assertIsNone(guest._product_url('blibli', ITEM_URL + suffix))
