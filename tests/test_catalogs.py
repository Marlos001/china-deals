"""Synthetic literal catalog props; these tests make no marketplace requests."""
import json
import unittest
from unittest.mock import patch

from china_deals import adapters, catalogs, guest
from china_deals.cli import build_parser, run
from china_deals.ranking import rank_offers


def html(items, tail=''):
    chunk = '\n'.join('5e:["$",null,{"item":' + json.dumps(item) + '}]' for item in items)
    return '<script>self.__next_f.push(' + json.dumps([1, chunk]) + ')</script>' + tail


def item(**kwargs):
    return dict({'marketplace': 'taobao', 'id': '123', 'title': 'iPhone 17 Pro Max', 'price': 6138}, **kwargs)


class CatalogTests(unittest.TestCase):
    def test_quote_is_bound_to_item_and_kept_separate_from_rankable_price(self):
        observation, row = catalogs.parse_jadeship(html([item(), item(id='999', price=1)]), '123')
        self.assertEqual(observation['amount'], '6138')
        self.assertEqual(observation['native_url'], 'https://item.taobao.com/item.htm?id=123')
        self.assertIsNone(observation['variant'])
        self.assertIsNone(observation['underlying_fetched_at'])
        self.assertEqual(row['price']['raw'], '6138')
        self.assertIsNone(row['price']['amount'])
        self.assertFalse(rank_offers([row])['groups'])
        self.assertFalse(rank_offers(rank_offers([row])['unranked'])['groups'])

    def test_conflicting_or_missing_item_prices_cannot_supply_quote(self):
        for values in ([item(price=0)], [item(price='6,138')], [item(price=True)], [item(id='999')],
                       [item(), item(price=100)], [item(), item(title='different title')],
                       [item(marketplace='jd')]):
            with self.subTest(values=values), self.assertRaises(adapters._Failure):
                catalogs.parse_jadeship(html(values), '123')

    def test_explicit_currency_conflicts_and_discarded_prices_cannot_establish_uniqueness(self):
        for values in ([item(currency='USD')], [item(priceCurrency='IDR')],
                       [item(), item(price='100-200')], [item(), item(price=None)],
                       [item()] * 100 + [item(price=100)]):
            with self.subTest(values=values[:2]), self.assertRaises(adapters._Failure):
                catalogs.parse_jadeship(html(values), '123')
        observation, _ = catalogs.parse_jadeship(html([item(currency='CNY')]), '123')
        self.assertEqual(observation['currency'], 'CNY')

    def test_whitespace_item_props_cannot_hide_conflicting_price(self):
        chunk = 'x:{"item":' + json.dumps(item()) + '}\ny:{"item" : \n ' + json.dumps(item(price=100)) + '}'
        body = '<script>self.__next_f.push(' + json.dumps([1, chunk]) + ')</script>'
        with self.assertRaises(adapters._Failure):
            catalogs.parse_jadeship(body, '123')

    def test_deduplicates_matching_item_props_but_not_conflicts(self):
        observation, _ = catalogs.parse_jadeship(html([item(), item()]), '123')
        self.assertEqual(observation['amount'], '6138')

    def test_html_price_text_and_executable_payloads_cannot_be_used(self):
        for body in ('<h1>iPhone</h1>¥1', '<script>self.__next_f.push([1, malicious()])</script>',
                     html([item()]).replace('self.__next_f.push(', 'evil(self.__next_f.push(')):
            with self.subTest(body=body), self.assertRaises(adapters._Failure):
                catalogs.parse_jadeship(body, '123')

    def test_input_and_size_constraints_before_fetch(self):
        for value in ('123abc', 'https://item.taobao.com.evil.test/item.htm?id=123',
                      'https://item.taobao.com/item.htm?id=123&id=456'):
            with self.subTest(value=value), patch.object(guest, '_fetch') as fetch:
                with self.assertRaises(ValueError):
                    catalogs.get_catalog_item('taobao', value)
                fetch.assert_not_called()
        with self.assertRaises(ValueError):
            catalogs.parse_jadeship('x' * (guest.MAX_RESPONSE_BYTES + 1), '123')
        with self.assertRaises(ValueError):
            catalogs.get_catalog_item('jd', '123')

    def test_http_identity_redirect_and_challenge(self):
        url = 'https://www.jadeship.com/item/taobao/123'
        with patch.object(guest, '_fetch', return_value=(html([item()]), url)) as fetch:
            result = catalogs.get_catalog_item('taobao', 'https://item.taobao.com/item.htm?id=123')
        self.assertEqual(result['status'], 'catalog_only')
        self.assertEqual(fetch.call_count, 1)
        for body, final, expected in [(html([item()]), url + '/other', 'catalog_url_mismatch'),
                                      ('<title>Just a moment</title>', url, 'challenge')]:
            with patch.object(guest, '_fetch', return_value=(body, final)):
                self.assertEqual(catalogs.get_catalog_item('taobao', '123')['error']['code'], expected)

    def test_cli_converts_catalog_reference_without_changing_marketplace_price(self):
        rates = {'base': 'BRL', 'rate_date': '2026-10-27', 'source': 'synthetic',
                 'brl_per_unit': {'CNY': '0.75', 'IDR': '0.0003', 'USD': '5'}}
        with patch.object(guest, '_fetch', return_value=(html([item()]), 'https://www.jadeship.com/item/taobao/123')), \
             patch('china_deals.fx.fetch_rates', return_value=rates):
            result, code = run(build_parser().parse_args(['catalog', 'taobao', '123']))
        self.assertEqual(code, 0)
        self.assertEqual(result['catalog_observations'][0]['brl_reference']['amount'], '4603.50')
        self.assertIsNone(result['items'][0]['price']['amount'])
        self.assertIsNone(result['items'][0]['brl']['product_cost'])


if __name__ == '__main__':
    unittest.main()
