import copy
import json
import unittest

from china_deals.models import normalize_offer
from china_deals.ranking import rank_offers


def source_row(**fields):
    return {'marketplace': 'jd', 'sku': '123', 'title': 'Sony WH-1000XM6',
            'url': 'https://item.jd.com/123.html', 'price': '100',
            'source_mode': 'guest_product_page', **fields}


def ranked_row(row):
    result = rank_offers([row])
    rows = result['unranked'] + [item for group in result['groups'].values() for item in group]
    assert len(rows) == 1
    return rows[0]


class SelectedProvenanceTests(unittest.TestCase):
    def roundtrips(self, row):
        for _ in range(4):
            row = normalize_offer('jd', row)
            yield row
            row = ranked_row(json.loads(json.dumps(row)))
            yield row

    def test_all_independent_selected_observations_survive_roundtrips(self):
        row = source_row(variant={'color': 'black'}, selected_variant={'storage': '1TB'},
                         variant_evidence={'model': 'WH-1000XM5'})
        original = copy.deepcopy(row)
        expected = [json.dumps(row[key], ensure_ascii=False, sort_keys=True)
                    for key in ('variant', 'selected_variant', 'variant_evidence')]
        for current in self.roundtrips(row):
            self.assertEqual(current['variant_observations'], sorted(expected))
            self.assertEqual(current['variant_evidence'], row['variant_evidence'])
            self.assertEqual(current['selected_variant'], expected[1])
        self.assertEqual(row, original)

    def test_each_reported_loss_survives_normalization_and_ranking(self):
        for fields in ({'selected_variant': 'WH-1000XM5'},
                       {'variant': {'color': 'black'}, 'variant_evidence': {'model': 'WH-1000XM5'}},
                       {'variant_evidence': 'WH-1000XM5'},
                       {'variant': {'color': 'black'}, 'variant_evidence': 'WH-1000XM5'}):
            with self.subTest(fields=fields):
                first = None
                for current in self.roundtrips(source_row(**fields)):
                    texts = current['variant_observations']
                    self.assertTrue(any('WH-1000XM5' in text for text in texts))
                    if first is None:
                        first = texts
                    self.assertEqual(texts, first)

    def test_dictionary_variant_legacy_evidence_and_spec_fallback_are_stable(self):
        variant = {'storage': '1TB', 'color': '银色'}
        for current in self.roundtrips(source_row(variant=variant, spec='selected silver')):
            self.assertEqual(current['variant_evidence'], variant)
            self.assertEqual(current['variant'], 'selected silver')
            self.assertEqual(current['variant_observations'],
                             sorted([json.dumps(variant, ensure_ascii=False, sort_keys=True), 'selected silver']))

    def test_conflicting_selection_stays_withheld_after_export_and_reranking(self):
        for fields in ({'selected_variant': 'WH-1000XM5'},
                       {'variant': {'color': 'black'}, 'variant_evidence': {'model': 'WH-1000XM5'}},
                       {'variant_evidence': 'WH-1000XM5'}):
            with self.subTest(fields=fields):
                current = source_row(**fields)
                for index in range(4):
                    result = rank_offers([current], query='Sony WH-1000XM6' if index == 0 else None)
                    self.assertFalse(result['groups'])
                    self.assertEqual(len(result['unranked']), 1)
                    current = json.loads(json.dumps(result['unranked'][0]))
                    self.assertIn('product_relevance_mismatch', current['ranking_exclusions'])
                    self.assertTrue(any('WH-1000XM5' in text for text in current['variant_observations']))

    def test_observations_are_bounded_deduplicated_and_flat(self):
        row = source_row(variant='black', selected_variant='black', variant_evidence='black',
                         variant_observations=['black', 'black', '', None, {'ignored': True},
                                               'x' * 9000, 'y' * 7999 + ' tail',
                                               *[f'option {i}' for i in range(30)]])
        first = None
        for current in self.roundtrips(row):
            texts = current['variant_observations']
            self.assertEqual(len(texts), 20)
            self.assertEqual(len(texts), len(set(texts)))
            self.assertTrue(all(isinstance(text, str) and 0 < len(text) <= 8000 for text in texts))
            self.assertIn('x' * 8000, texts)
            self.assertIn('y' * 7999, texts)
            if first is None:
                first = texts
            self.assertEqual(texts, first)

    def test_price_display_raw_scope_and_type_survive_roundtrips(self):
        for scope in ({'scope': 'monthly installment'}, {'type': 'rental'},
                      {'scope': 'monthly installment', 'type': 'rental'}):
            with self.subTest(scope=scope):
                raw = {'priceDisplay': '100', **scope}
                for current in self.roundtrips(source_row(price=raw)):
                    self.assertEqual(current['price']['raw'], raw)
                    self.assertNotIn('raw', current['price']['raw'])

    def test_unverified_source_prices_are_never_promoted(self):
        for mode in ('search_index', 'proxy_catalog', 'category_card', 'indexed_product_block'):
            with self.subTest(mode=mode):
                raw = {'priceDisplay': '100', 'scope': 'monthly installment', 'type': 'rental'}
                for current in self.roundtrips(source_row(price=raw, source_mode=mode)):
                    self.assertEqual(current['price']['raw'], raw)
                    self.assertIsNone(current['price']['amount'])
                    self.assertNotEqual(current['price']['basis'], 'displayed')

    def test_existing_transaction_hold_is_not_promoted_by_raw_amount(self):
        raw = {'priceDisplay': '100', 'scope': 'monthly installment'}
        row = source_row(price={'raw': raw, 'amount': None, 'basis': 'transaction_scope_unverified'})
        for current in self.roundtrips(row):
            self.assertEqual(current['price']['raw'], raw)
            self.assertIsNone(current['price']['amount'])
            self.assertNotEqual(current['price']['basis'], 'displayed')


if __name__ == '__main__':
    unittest.main()
