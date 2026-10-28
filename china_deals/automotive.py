"""Automotive discovery plans. Search wording never certifies vehicle fitment."""

import re
import unicodedata

from .marketplaces import CHINESE_MARKETPLACES, INTERNATIONAL_MARKETPLACES

# Fixed category translations only. Preserve the caller's complete vehicle,
# engine, trim, date and brand wording alongside each translated search.
_CATEGORIES = (
    ('wheels', r'\bwheels?\b|\brims?\b|\brodas?\b|轮毂', '轮毂 尺寸 孔距 偏距', 'velg ukuran offset'),
    ('grille', r'\bgrill(?:e)?s?\b|\bgrades?\b|中网', '中网', 'grille'),
    ('splitter', r'\bsplitters?\b|\blips?\b|前唇', '前唇', 'front lip'),
    ('spoiler', r'\bspoilers?\b|\baerof[oó]lio\b|尾翼', '尾翼', 'spoiler'),
    ('headlights', r'\bheadlights?\b|\bfar[oó](?:is|l)\b|大灯', '前大灯', 'lampu depan'),
    ('taillights', r'\btail[ -]?lights?\b|\blanternas?\b|尾灯', '尾灯', 'lampu belakang'),
    ('bumper', r'\bbumpers?\b|\bpara[ -]?choques?\b|保险杠', '保险杠', 'bumper'),
    ('intake', r'\bintakes?\b|\badmiss[aã]o\b|进气', '进气', 'intake'),
    ('turbo', r'\bturbos?\b|\bturbochargers?\b|涡轮', '涡轮增压器 发动机代码', 'turbo kode mesin'),
    ('exhaust', r'\bexhausts?\b|\bescap(?:e|amento)s?\b|排气', '排气', 'knalpot'),
    ('intercooler', r'\bintercoolers?\b|中冷', '中冷器 发动机代码', 'intercooler kode mesin'),
)


def parts_query_plan(query):
    """Return a bounded B9 A4 parts discovery plan, or None for other queries.

    Does not infer the caller's engine or bumper. Added terms are research
    prompts, not mandatory purchase specifications or evidence of compatibility.
    Automotive intent deliberately remains unsupported for automatic ranking.
    """
    if not isinstance(query, str):
        raise ValueError('Query must be text')
    text = unicodedata.normalize('NFKC', query)
    if (not re.search(r'\baudi\b|奥迪', text, re.I)
            or not re.search(r'(?<![a-z0-9])a4(?![a-z0-9])', text, re.I)
            or not re.search(r'(?<![a-z0-9])b9(?:\.5)?(?![a-z0-9])', text, re.I)):
        return None
    if not query.strip() or len(query) > 500 or any(ord(c) < 32 for c in query):
        raise ValueError('Query must be 1..500 characters without controls')
    categories = [row for row in _CATEGORIES if re.search(row[1], text, re.I)]
    broad = not categories
    if not categories:
        categories = list(_CATEGORIES)
    chinese = [f'奥迪 {query} {row[2]}' for row in categories]
    indonesian = [f'{query} {row[3]}' for row in categories]
    international = [f'{query} {row[0]}' for row in categories] if broad else [query]
    # Never cut off a requested engine code, exclusion or selected brand to fit
    # transport bounds. Fall back to explicit translation for overlong queries.
    if any(len(value) > 500 for value in chinese + indonesian):
        return None
    return {
        'query': query, 'family': None, 'planning_profile': 'audi-a4-b9-parts',
        'scope': 'discovery_only_not_fitment_certification',
        'categories': [row[0] for row in categories],
        'marketplace_queries': {
            **{market: list(chinese) for market in CHINESE_MARKETPLACES},
            'blibli': indonesian,
            **{market: list(international) for market in INTERNATIONAL_MARKETPLACES}},
        'requires_agent_translation': False,
        'fitment_required': ['VIN/PR codes and production date', 'sedan/Avant/allroad',
                             'standard/S-line bumper and parking/radar/camera equipment',
                             'engine code, output, MAF/MAP, FWD/quattro and transmission',
                             'exact manufacturer part number and selected assembly quantity'],
        'seller_evidence_required': ['exact seller identity and domain',
                                     'rating source, scale, count and observation time',
                                     'recent part-specific reviews and installed photos',
                                     'written fitment/returns/warranty and delivered quote'],
        'warnings': [
            'Search modifiers are discovery prompts, not facts about the vehicle or product.',
            'Automotive offers remain unsupported for automatic product ranking; review each exact part.',
            'B9 category pages can include A5/S4/RS4, B9.5 or incompatible engine parts.',
            'Seller and product ratings are separate; never merge sellers or treat affiliate claims as verification.',
            'Wheel PCD alone does not establish bore, offset, load, bolt-seat or brake clearance.',
            'No search, seller verification, fitment approval or purchase has been executed.'],
    }
