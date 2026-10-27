"""Offline implementation capabilities, distinct from live access or procurement."""

from .marketplaces import CHINESE_MARKETPLACES, CURRENCIES, FANSBUY_MARKETPLACES, MARKETPLACES
from .models import marketplace_name


def resolve_markets(value):
    """Expand explicit groups without treating a group as a marketplace ID."""
    result = []
    for part in value.split(','):
        name = part.strip().casefold()
        values = FANSBUY_MARKETPLACES if name == 'fansbuy' else MARKETPLACES if name == 'all' else (marketplace_name(name),)
        result.extend(market for market in values if market not in result)
    return result


def marketplace_capabilities():
    """Describe available command paths; no request or availability check is made."""
    flows = {
        'taobao': ['keyword_recommendations', 'product_link_input', 'procurement_mention'],
        'tmall': ['keyword_recommendations'],
        '1688': ['keyword_recommendations', 'product_link_input', 'procurement_mention'],
        'weidian': ['product_link_input', 'procurement_mention'],
        'jd': ['procurement_mention'],
    }
    items = []
    for market in MARKETPLACES:
        expanded = market in {'tmall', '1688', 'weidian'}
        items.append({
            'marketplace': market, 'currency': CURRENCIES[market],
            'query_language': 'Chinese required' if market in CHINESE_MARKETPLACES else 'Indonesian suggested',
            'fansbuy_named_evidence': flows.get(market, []),
            'guest_search': 'public_api_then_index_discovery' if market == 'blibli' else 'index_discovery',
            'guest_detail': 'bounded_primary_evidence' if expanded else {
                'taobao': 'unavailable_without_validated_schema', 'jd': 'bound_public_json',
                'goofish': 'primary_dom_browser_or_capture', 'blibli': 'bound_selected_product_state',
            }[market],
            'price_contract': 'no_selected_variant_price_contract' if expanded else 'inspect_per_source_price_basis',
            'native_access': 'unavailable_without_validated_adapter' if expanded else 'optional_existing_adapter',
            'native_filters': 'no_verified_mapping' if expanded else 'inspect_filter_plan',
            'refresh_history_coupons_promotions_brazil': 'available_with_existing_evidence_and_cost_requirements',
            'live_access_verified': False,
        })
    return {
        'schema_version': '1', 'marketplaces': items,
        'fansbuy_named_marketplaces': list(FANSBUY_MARKETPLACES),
        'fansbuy_evidence': {
            'basis': 'indexed_first_party_copy', 'retrieved_on': '2026-10-27',
            'source_urls': ['https://fansbuy.com/beginnerGuide', 'https://m.fansbuy.com/user/promo'],
            'scope': 'Union of five explicitly named platforms; not an exhaustive manual-purchase list or live procurement proof.',
        },
        'warnings': [
            'Capabilities describe implemented paths; source pages can still be blocked, masked, unavailable or unpriced.',
            'Index prices and unbound primary-page amounts cannot become ranked exact-variant prices.',
            'Legacy Taobao observations can retain Tmall URLs; separate marketplace searches may overlap.',
            'Fansbuy fill-and-buy and forwarding are manual workflows, not proof of arbitrary automated marketplace support.',
        ],
    }
