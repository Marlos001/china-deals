import unittest

from china_deals.products import assess_product
from china_deals.ranking import rank_offers


def row(title, variant):
    return {'marketplace': 'jd', 'sku': '123', 'title': title, 'variant': variant,
            'price': '100', 'url': 'https://item.jd.com/123.html'}


class StructuredProductEvidence(unittest.TestCase):
    def test_selected_model_cannot_disappear_into_variant_dictionary(self):
        for query, title, variant in [
            ('iPhone 17 Pro Max', 'iPhone 17 Pro Max', {'model': '16 Pro Max 256GB'}),
            ('AirPods Max', 'AirPods Max', {'selected_model': 'AirPods Pro 2'}),
            ('ROG Zephyrus G14', 'ROG Zephyrus G14', {'model': 'G16', 'ram_gb': 32}),
            ('AirPods Max', 'AirPods Max with Smart Case', {'selection': 'Smart Case only'}),
        ]:
            with self.subTest(query=query, variant=variant):
                current = row(title, variant)
                for _ in range(3):
                    result = rank_offers([current], query=query)
                    self.assertFalse(result['groups'])
                    current = result['unranked'][0]
                    self.assertIn('product_relevance_mismatch', current['ranking_exclusions'])
                    self.assertEqual(current['variant_evidence'], variant)

    def test_matching_color_capacity_dictionary_can_inherit_named_title(self):
        current = row('iPhone 17 Pro Max 1TB', {'color': 'silver', 'storage': '1TB'})
        for _ in range(3):
            result = rank_offers([current], query='iPhone 17 Pro Max 1TB')
            self.assertEqual(len(result['groups']['CNY']), 1)
            current = result['groups']['CNY'][0]
            self.assertEqual(current['relevance']['status'], 'match')

    def test_additional_selected_observation_cannot_be_trimmed_by_bundle(self):
        current = {'title': 'AirPods Max', 'variant': 'headphones with free case',
                   'selected_variant': 'Smart Case only'}
        self.assertEqual(assess_product(current, 'AirPods Max')['status'], 'mismatch')

    def test_structured_monthly_scope_remains_unpriced(self):
        current = row('iPhone 17 Pro Max', {'payment': 'monthly installment'})
        result = rank_offers([current], query='iPhone 17 Pro Max')
        self.assertFalse(result['groups'])
        self.assertIsNone(result['unranked'][0]['price']['amount'])

    def test_explicit_numeric_units_cannot_inherit_conflicting_title_capacity(self):
        for query, variant, expected in (
            ('iPhone 17 Pro Max 1TB', {'storage_gb': 256}, False),
            ('ROG Zephyrus G16 RAM 32GB SSD 1TB', {'ram_gb': 16, 'storage_gb': 512}, False),
            ('ROG Zephyrus G16 RAM 32GB SSD 1TB', {'ram_gb': 32, 'storage_tb': 1}, True),
            ('RTX 5070 Ti 16GB', {'vram_gb': 12}, False),
            ('RTX 5070 Ti 16GB', {'vram_gb': 16}, True),
        ):
            with self.subTest(query=query, variant=variant):
                current = row(query, variant)
                for iteration in range(3):
                    result = rank_offers([current], query=query if iteration == 0 else None)
                    self.assertEqual(bool(result['groups']), expected)
                    current = ([r for group in result['groups'].values() for r in group] + result['unranked'])[0]
