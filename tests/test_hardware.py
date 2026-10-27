import copy
import unittest

from china_deals.hardware import COMPARISON_FIELDS, compare_laptops, extract_hardware
from china_deals.models import normalize_offer
from china_deals.ranking import rank_offers

G16_2023 = (
    'ASUS ROG Zephyrus G16 2023 GU603VV i7-13620H RTX 4060 Laptop GPU 8GB '
    'TGP 120W RAM 16GB SSD 512GB 16-inch 1920x1200 IPS 165Hz used'
)
G16_2024 = (
    'ASUS ROG Zephyrus G16 (2024) GU605MI Intel Core Ultra 9 185H '
    'RTX 4070 Laptop GPU 8GB TGP 105W 32GB LPDDR5X 1TB SSD '
    '16-inch 2560x1600 OLED 240Hz brand new'
)
G16_2025 = (
    'ASUS ROG Zephyrus G16 2025 GU605CR Core Ultra 9 285H RTX 5070 Ti '
    'Laptop GPU 12GB TGP 120W RAM 32GB SSD 2TB 16-inch 2560x1600 OLED 240Hz new'
)


def offer(candidate_id, title=G16_2024, price='¥12000', marketplace='jd', **extra):
    row = {'title': title, 'price': price, 'sku': '123', 'url': 'https://item.jd.com/123.html'}
    if marketplace == 'blibli':
        row['url'] = 'https://www.blibli.com/p/example/ps--EXAMPLE'
        row['sku'] = 'EXAMPLE'
    result = normalize_offer(marketplace, row, '2026-10-27T12:00:00Z')
    result.update(candidate_id=candidate_id, source_mode='listing_content')
    result.update(extra)
    return result


class ComparisonWithoutIntentTests(unittest.TestCase):
    def test_selected_accessory_and_chinese_accessory_cannot_win(self):
        for extra in ({'variant': 'charger only'}, {'title': 'ASUS ROG Zephyrus G16 电源适配器', 'description': G16_2024}):
            with self.subTest(extra=extra):
                bad = offer('accessory', price='200', **extra)
                result = compare_laptops([bad, offer('laptop')])
                self.assertEqual(result['groups'][0]['cheapest_candidate_ids'], ['laptop'])
                self.assertEqual(len(result['unranked']), 1)
                self.assertFalse(rank_offers(result['unranked'])['groups'])
        result = compare_laptops([offer('bundle', title=G16_2024 + ' with charger')])
        self.assertEqual(len(result['groups']), 1)

    def test_monthly_scope_cannot_win_without_query(self):
        for extra in ({'title': G16_2024 + ' 月供'}, {'title': G16_2024 + ' monthly payment'},
                      {'variant': 'cicilan bulanan'}, {'variant': '月付 200元'}):
            with self.subTest(extra=extra):
                bad = offer('monthly', price='200', **extra)
                result = compare_laptops([bad, offer('laptop')])
                self.assertEqual(result['groups'][0]['cheapest_candidate_ids'], ['laptop'])
                self.assertEqual(len(result['unranked']), 1)
                self.assertFalse(rank_offers(result['unranked'])['groups'])



class ExtractionTests(unittest.TestCase):
    def test_three_generations_are_literal_distinct_hardware(self):
        expected = [
            (G16_2023, 'i7-13620H', 'RTX 4060', 8, 16, 512, 2023, 'GU603VV', 'used'),
            (G16_2024, 'Core Ultra 9 185H', 'RTX 4070', 8, 32, 1024, 2024, 'GU605MI', 'new'),
            (G16_2025, 'Core Ultra 9 285H', 'RTX 5070 TI', 12, 32, 2048, 2025, 'GU605CR', 'new'),
        ]
        for text, cpu, gpu, vram, ram, ssd, year, code, condition in expected:
            with self.subTest(year=year):
                result = extract_hardware(text)
                for field, value in {'cpu': cpu, 'gpu': gpu, 'vram_gb': vram, 'ram_gb': ram,
                                     'ssd_gb': ssd, 'model_year': year, 'model_code': code,
                                     'condition': condition, 'gpu_variant': 'laptop'}.items():
                    self.assertEqual(result[field], value, field)
                self.assertFalse(result['conflicts'])
                self.assertTrue(all(result[field] is not None for field in COMPARISON_FIELDS))
                for records in result['evidence'].values():
                    for record in records:
                        self.assertEqual(text[record['start']:record['end']], record['excerpt'])

    def test_g16_model_codes_and_screen_inches_do_not_establish_memory(self):
        result = extract_hardware('ASUS ROG Zephyrus G16 GU605 16-inch OLED 240Hz')
        for field in ('ram_gb', 'ssd_gb', 'cpu', 'gpu', 'vram_gb', 'model_year'):
            self.assertIsNone(result[field], field)
        self.assertEqual(result['display_size_inches'], 16)
        result = extract_hardware('ROG G16 16GB + 1TB 16 inch')
        self.assertIsNone(result['ram_gb'])
        self.assertIsNone(result['ssd_gb'])

    def test_memory_labels_do_not_swap_ram_ssd_and_vram(self):
        result = extract_hardware('Zephyrus RTX4070 8GB 32GB RAM 1TB SSD')
        self.assertEqual(result['vram_gb'], 8)
        self.assertEqual(result['ram_gb'], 32)
        self.assertEqual(result['ssd_gb'], 1024)
        result = extract_hardware('RAM: 16GB SSD: 2TB VRAM 8GB TGP 105W')
        self.assertEqual(result['ram_gb'], 16)
        self.assertEqual(result['ssd_gb'], 2048)
        self.assertEqual(result['vram_gb'], 8)
        self.assertEqual(result['gpu_tgp_w'], 105)
        result = extract_hardware('RTX4070 32GB RAM 1TB SSD')
        self.assertIsNone(result['vram_gb'])
        result = extract_hardware('Zephyrus RTX4070 8GB RAM 32GB SSD 1TB')
        self.assertIsNone(result['vram_gb'])
        self.assertEqual(result['ram_gb'], 32)
        self.assertEqual(result['ssd_gb'], 1024)
        result = extract_hardware('VRAM 8GB RAM 32GB SSD 1TB')
        self.assertEqual(result['vram_gb'], 8)
        self.assertEqual(result['ram_gb'], 32)
        for text in ('内存32GB 固态1TB', 'RAM32GB SSD1TB'):
            result = extract_hardware(text)
            self.assertEqual(result['ram_gb'], 32)
            self.assertEqual(result['ssd_gb'], 1024)

    def test_alternatives_and_contradictions_are_not_a_selected_variant(self):
        result = extract_hardware('Zephyrus G16 RAM 16GB/32GB SSD 512GB or 1TB RTX4060 / RTX4070')
        for field in ('gpu', 'ram_gb', 'ssd_gb'):
            self.assertIsNone(result[field], field)
            self.assertIn(field, result['conflicts'])
        self.assertEqual(result['conflicts']['ram_gb'], [16, 32])
        self.assertEqual(result['conflicts']['ssd_gb'], [512, 1024])
        result = extract_hardware('RAM 32GB. RAM 16GB. new / used')
        self.assertIsNone(result['ram_gb'])
        self.assertIsNone(result['condition'])
        self.assertEqual(len(result['evidence']['ram_gb']), 2)

    def test_shared_units_and_gpu_prefix_alternatives_stay_conflicting(self):
        result = extract_hardware('Zephyrus RTX4060/4070 RAM 16/32GB SSD 512GB/1TB')
        for field in ('gpu', 'ram_gb', 'ssd_gb'):
            self.assertIsNone(result[field], field)
        self.assertEqual(result['conflicts']['ram_gb'], [16, 32])
        self.assertEqual(result['conflicts']['gpu'], ['RTX 4060', 'RTX 4070'])
        result = extract_hardware('16-32GB RAM')
        self.assertIsNone(result['ram_gb'])

    def test_abbreviated_cpu_power_vram_and_display_alternatives_are_unknown(self):
        cases = [
            ('Core Ultra 9 185H/285H', 'cpu'), ('VRAM 8GB/12GB', 'vram_gb'),
            ('8/12GB VRAM', 'vram_gb'), ('TGP 105W/120W', 'gpu_tgp_w'),
            ('165/240Hz', 'display_refresh_hz'), ('16/18-inch', 'display_size_inches'),
            ('Zephyrus G16 2024/2025', 'model_year'),
        ]
        for text, field in cases:
            with self.subTest(text=text):
                self.assertIsNone(extract_hardware(text)[field])
        result = compare_laptops([offer('alternate', G16_2024.replace('240Hz', '165/240Hz'))])
        self.assertFalse(result['groups'])
        self.assertEqual(len(result['incomplete']), 1)

    def test_unstated_vram_power_and_gpu_scope_stay_unknown(self):
        result = extract_hardware('RTX 5070 Ti RAM 32GB SSD 1TB')
        for field in ('vram_gb', 'gpu_tgp_w', 'gpu_variant'):
            self.assertIsNone(result[field], field)
        result = extract_hardware('Zephyrus G16 with RTX4070 desktop GPU 12GB')
        self.assertEqual(result['gpu_variant'], 'desktop')
        self.assertEqual(result['vram_gb'], 12)

    def test_year_needs_adjacent_product_evidence(self):
        self.assertIsNone(extract_hardware('Updated 2025-10-27. ASUS Zephyrus G16')['model_year'])
        self.assertIsNone(extract_hardware('copyright 2024. GU605MI')['model_year'])
        self.assertIsNone(extract_hardware('GU605MI')['model_code'])
        self.assertEqual(extract_hardware('2025 ASUS Zephyrus G16')['model_year'], 2025)

    def test_negated_numeric_facts_retain_unresolved_spans(self):
        cases = [('TGP 105W', 'gpu_tgp_w'), ('105W TGP', 'gpu_tgp_w'),
                 ('VRAM 8GB', 'vram_gb'), ('8GB VRAM', 'vram_gb'),
                 ('2560x1600', 'display_resolution'), ('2.5K', 'display_resolution'),
                 ('240Hz', 'display_refresh_hz'), ('16-inch', 'display_size_inches')]
        for literal, field in cases:
            for prefix in ('not ', 'without ', '非'):
                text = prefix + literal
                with self.subTest(text=text):
                    result = extract_hardware(text)
                    self.assertIsNone(result[field])
                    self.assertTrue(result['evidence'][field])
                    self.assertTrue(all(r['value'] is None for r in result['evidence'][field]))
                    for record in result['evidence'][field]:
                        self.assertEqual(text[record['start']:record['end']], record['excerpt'])
                        self.assertIn(prefix, record['excerpt'])
        result = extract_hardware('TGP 105W; not TGP 120W')
        self.assertIsNone(result['gpu_tgp_w'])
        self.assertEqual(result['conflicts']['gpu_tgp_w'], [105, None])

    def test_literal_aliases_typography_and_chinese_boundaries(self):
        for text in ('Radeon RX 6700S', 'AMD Radeon RX 6700S', 'RX6700S'):
            self.assertEqual(extract_hardware(text)['gpu'], 'RADEON RX 6700S')
        text = ('华硕ROG幻14GA402RJ笔记本 R9-6900HS RX6700S 8G显存 内存16GB 固态1TB '
                '14-inch 2560x1600 IPS 120Hz')
        result = extract_hardware(text)
        for field, expected in {'cpu': 'Ryzen 9 6900HS', 'gpu': 'RADEON RX 6700S',
                                'vram_gb': 8, 'model_code': 'GA402RJ',
                                'ram_gb': 16, 'ssd_gb': 1024}.items():
            self.assertEqual(result[field], expected, field)
        text = 'ASUS® ROG Zephyrus G14 Intel® Core™ Ultra 9 Processor 386H RTX™ 5060'
        result = extract_hardware(text)
        self.assertEqual(result['cpu'], 'Core Ultra 9 386H')
        self.assertEqual(result['gpu'], 'RTX 5060')
        for records in result['evidence'].values():
            for record in records:
                self.assertEqual(text[record['start']:record['end']], record['excerpt'])

    def test_broader_literal_years_and_bounded_legacy_code(self):
        for family, year in [('G14', 2022), ('G15', 2021), ('M16', 2023), ('S17', 2021)]:
            self.assertEqual(extract_hardware(f'ASUS ROG Zephyrus {family} ({year})')['model_year'], year)
        result = extract_hardware('ASUS ROG Zephyrus M GM501GS')
        self.assertEqual(result['model_code'], 'GM501GS')
        for field in ('cpu', 'gpu', 'ram_gb', 'ssd_gb', 'model_year', 'display_size_inches'):
            self.assertIsNone(result[field])
        self.assertIsNone(extract_hardware('ASUS GM999ZZ')['model_code'])

    def test_parenthetical_alias_is_local_to_explicit_pixels(self):
        text = '2.5K (2560 x 1600, WQXGA)'
        result = extract_hardware(text)
        self.assertEqual(result['display_resolution'], '2560x1600')
        self.assertNotIn('display_resolution', result['conflicts'])
        self.assertTrue(result['evidence']['display_resolution'])
        for record in result['evidence']['display_resolution']:
            self.assertEqual(text[record['start']:record['end']], record['excerpt'])
        self.assertEqual(extract_hardware('2.5K')['display_resolution'], '2.5K')
        for text in ('2.5K 2560x1600', '2.5K (2560x1600) or 1920x1200',
                     '2.5K (2560x1600 or 1920x1200)', 'not 2.5K (2560x1600, WQXGA)'):
            self.assertIsNone(extract_hardware(text)['display_resolution'], text)

    def test_condition_and_negation(self):
        self.assertEqual(extract_hardware('like new Zephyrus G16')['condition'], 'used')
        self.assertIsNone(extract_hardware('new model Zephyrus G16')['condition'])
        self.assertIsNone(extract_hardware('not OLED, no SSD 1TB')['display_technology'])
        self.assertIsNone(extract_hardware('not OLED, no SSD 1TB')['ssd_gb'])
        self.assertEqual(extract_hardware('open box')['condition'], 'open_box')


class ComparisonTests(unittest.TestCase):
    def test_exact_configuration_prices_and_ties_not_universal_scores(self):
        offers = [offer('2024-high', price='¥13000'), offer('2023', G16_2023, '¥6000'),
                  offer('2025', G16_2025, '¥18000'), offer('2024-low'), offer('2024-tie')]
        before = copy.deepcopy(offers)
        result = compare_laptops(offers)
        self.assertEqual(offers, before)
        self.assertEqual(len(result['groups']), 3)
        group = next(g for g in result['groups'] if g['configuration']['gpu'] == 'RTX 4070')
        self.assertEqual(group['cheapest_candidate_ids'], ['2024-low', '2024-tie'])
        self.assertEqual([x['candidate_id'] for x in group['candidates']], ['2024-low', '2024-tie', '2024-high'])
        self.assertEqual(group['candidates'][0]['price']['raw'], '¥12000')
        self.assertEqual(group['candidates'][0]['source_url'], 'https://item.jd.com/123.html')
        self.assertTrue(group['candidates'][0]['hardware']['evidence']['cpu'])
        self.assertNotIn('winner', result)
        self.assertNotIn('score', str(result))

    def test_currency_separation_and_blibli_no_freight(self):
        result = compare_laptops([offer('china'), offer('indonesia', price='Rp20.000.000', marketplace='blibli')])
        self.assertEqual({g['currency'] for g in result['groups']}, {'CNY', 'IDR'})
        self.assertTrue(any('Blibli' in warning and 'freight' in warning for warning in result['warnings']))

    def test_search_route_cannot_bind_a_comparison_price(self):
        result = compare_laptops([offer('search', url='https://search.jd.com/Search?keyword=laptop')])
        self.assertFalse(result['groups'])
        self.assertEqual(len(result['unranked']), 1)

    def test_search_index_and_missing_provenance_never_win(self):
        result = compare_laptops([offer('actual'), offer('index', price='¥1', source_mode='search_index'),
                                  offer('unspecified', price='¥2', source_mode=None)])
        self.assertEqual(result['groups'][0]['cheapest_candidate_ids'], ['actual'])
        self.assertEqual([x['candidate_id'] for x in result['discoveries']], ['index', 'unspecified'])
        self.assertFalse(compare_laptops([offer('index', source_mode='search_index')])['groups'])

    def test_identically_unknown_candidates_are_not_grouped(self):
        title = G16_2024.replace('TGP 105W ', '')
        result = compare_laptops([offer('one', title), offer('two', title, '¥1')])
        self.assertFalse(result['groups'])
        self.assertEqual(len(result['incomplete']), 2)
        self.assertIn('unknown_or_conflicting:gpu_tgp_w', result['incomplete'][0]['reasons'])

    def test_description_conflicts_and_nonhardware_conflicts_retained(self):
        result = compare_laptops([offer('conflict', description='RAM 16GB')])
        self.assertFalse(result['groups'])
        hardware = result['incomplete'][0]['hardware']
        self.assertIsNone(hardware['ram_gb'])
        self.assertEqual(hardware['conflicts']['ram_gb'], [32, 16])
        self.assertEqual(hardware['evidence']['ram_gb'][1]['source'], 'description')
        result = compare_laptops([offer('years', description='2025 ASUS Zephyrus G16')])
        self.assertFalse(result['groups'])

    def test_all_requirement_outcomes_are_explicit(self):
        required = {'min_ram_gb': 32, 'min_ssd_gb': 1024, 'cpu': 'Intel Core Ultra 9 185H',
                    'gpu': 'RTX4070', 'display_technology': 'oled', 'new_only': True}
        result = compare_laptops([offer('yes'), offer('no', G16_2023),
                                  offer('unknown', G16_2024.replace('32GB LPDDR5X ', ''))], required)
        self.assertEqual(result['groups'][0]['cheapest_candidate_ids'], ['yes'])
        self.assertEqual(result['filtered'][0]['candidate_id'], 'no')
        unknown = result['requirement_unknown'][0]
        self.assertEqual(unknown['candidate_id'], 'unknown')
        self.assertEqual(unknown['requirement_check']['unknown'], ['min_ram_gb'])
        self.assertIn('new_only', result['filtered'][0]['requirement_check']['failed'])

    def test_unverified_structured_values_cannot_fill_missing_specs(self):
        title = G16_2024.replace('32GB LPDDR5X ', '')
        for hardware in ({'ram_gb': 32}, {'verified': True, 'ram_gb': 32},
                         {'verified': True, 'evidence': None}, {'verified': True, 'evidence': []},
                         {'verified': False, 'evidence': {'ram_gb': [{'excerpt': 'RAM 32GB'}]}}):
            result = compare_laptops([offer('missing', title, hardware=hardware)])
            self.assertFalse(result['groups'])
        hardware = {'verified': True, 'ram_gb': 32, 'evidence': {'ram_gb': [{'excerpt': 'RAM 32GB'}]}}
        result = compare_laptops([offer('supported', title, hardware=hardware)])
        self.assertEqual(result['groups'][0]['configuration']['ram_gb'], 32)
        self.assertEqual(result['groups'][0]['candidates'][0]['hardware']['evidence']['ram_gb'][0]['source'],
                         'hardware.evidence.ram_gb.0')
        hardware['evidence']['ram_gb'][0]['excerpt'] = 'RAM 16GB/32GB'
        self.assertFalse(compare_laptops([offer('ambiguous', title, hardware=hardware)])['groups'])

    def test_different_vram_tgp_condition_and_display_never_merge(self):
        variants = [G16_2024, G16_2024.replace('105W', '120W'), G16_2024.replace('8GB', '12GB'),
                    G16_2024.replace('brand new', 'used'), G16_2024.replace('240Hz', '165Hz')]
        result = compare_laptops([offer(str(i), title) for i, title in enumerate(variants)])
        self.assertEqual(len(result['groups']), 5)

    def test_desktop_gpu_and_invalid_prices_excluded(self):
        desktop = G16_2024.replace('Laptop GPU', 'desktop GPU')
        cases = [offer('desktop', desktop), offer('range', price='¥100-200'),
                 offer('minimum', price='¥100', price_basis='page_minimum'),
                 offer('unsafe', url='https://evil.test/item')]
        cases[2]['price']['basis'] = 'page_minimum'
        bad_amount = offer('tampered')
        bad_amount['price']['amount'] = '1'
        cases.append(bad_amount)
        cases.append(offer('deposit', G16_2024 + ' deposit'))
        result = compare_laptops(cases)
        self.assertFalse(result['groups'])
        self.assertEqual(len(result['unranked']), 6)

    def test_explicit_families_chassis_and_identifiers_partition_groups(self):
        titles = ['ROG Zephyrus G16', 'ROG Strix G16', 'ROG Flow X16', 'ASUS TUF Gaming F16']
        specs = G16_2024[G16_2024.index('Intel'):]
        rows = [offer(str(i), title + ' ' + specs) for i, title in enumerate(titles)]
        result = compare_laptops(rows)
        self.assertEqual(len(result['groups']), 4)
        self.assertTrue(all(len(g['candidates']) == 1 for g in result['groups']))
        self.assertTrue(all(g['product_identity']['product_family'] for g in result['groups']))
        rows = [offer('base'), offer('different-code', G16_2024.replace('GU605MI', 'GU605CR')),
                offer('unknown-code', G16_2024.replace('GU605MI ', '')),
                offer('different-year', G16_2024.replace('(2024)', '(2025)'))]
        self.assertEqual(len(compare_laptops(rows)['groups']), 4)
        result = compare_laptops([offer('generic-1', specs), offer('generic-2', specs),
                                  offer('family-only', 'Zephyrus ' + specs)])
        self.assertFalse(result['groups'])
        self.assertEqual(len(result['incomplete']), 3)

    def test_duo_and_unbound_multiple_displays_stay_incomplete(self):
        for text in (G16_2024.replace('G16', 'Duo 16'),
                     G16_2024 + ' dual-screen', G16_2024 + ' secondary display 14-inch'):
            result = compare_laptops([offer('one', text), offer('two', text)])
            self.assertFalse(result['groups'])
            self.assertEqual(len(result['incomplete']), 2)
            self.assertIn('multi_display_binding_unresolved', result['incomplete'][0]['reasons'])

    def test_accessory_with_copied_hardware_and_root_exclusions_never_group(self):
        result = compare_laptops([offer('charger', 'Replacement charger compatible with ' + G16_2024)])
        self.assertFalse(result['groups'])
        self.assertEqual(len(result['unranked']), 1)
        result = compare_laptops([offer('laptop', G16_2024 + ' with charger and backlit keyboard')])
        self.assertEqual(len(result['groups']), 1)
        result = compare_laptops([offer('blocked', ranking_exclusions=['requested_family_mismatch'])])
        self.assertFalse(result['groups'])
        self.assertEqual(result['unranked'][0]['reasons'], ['requested_family_mismatch'])

    def test_amd_aliases_merge_but_negated_specs_do_not(self):
        title = G16_2024.replace('RTX 4070', 'Radeon RX 6700S')
        result = compare_laptops([offer('plain', title), offer('vendor', title.replace('Radeon', 'AMD Radeon'))])
        self.assertEqual(len(result['groups']), 1)
        for before, after in [('TGP 105W', 'not TGP 105W'), ('8GB', 'not VRAM 8GB'),
                              ('2560x1600', 'not 2560x1600'), ('240Hz', 'not 240Hz'),
                              ('16-inch', 'not 16-inch')]:
            result = compare_laptops([offer('negative', G16_2024.replace(before, after))])
            self.assertFalse(result['groups'], after)
            self.assertEqual(len(result['incomplete']), 1)

    def test_inputs_validated(self):
        for bad in (None, {}, [None]):
            with self.assertRaises(ValueError):
                compare_laptops(bad)
        for bad in ({'min_ram_gb': True}, {'min_ssd_gb': float('nan')}, {'gpu': ''},
                    {'new_only': 'true'}, {'performance_score': 10}):
            with self.assertRaises(ValueError):
                compare_laptops([], bad)


if __name__ == '__main__':
    unittest.main()
