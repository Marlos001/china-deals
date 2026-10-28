"""Offline, caller-supplied Brazil/import scenarios; never checkout or legal clearance.

``compare_brazil`` returns JSON-compatible ``cases``. Money outputs are decimal
BRL strings rounded per component by fx.convert_brl. ``conditional_math`` is
arithmetic only; ``financial_outcome`` is gated by evidence and decision holds.
Invalid schema raises ValueError; absent evidence stays unknown, never zero.
"""

import copy
import json
import re
from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import urlsplit

from .config import load_config
from .decimal_math import bounded_decimal, monetary_calculation
from .freshness import CACHED_MODES, assess_fx_freshness, assess_price_freshness
from .fx import convert_brl, validate_snapshot
from .marketplaces import MONEY_SCALES
from .models import _offer_unavailable, decimal_value, normalize_offer

IMPORT_COSTS = ('domestic_freight', 'international_freight', 'insurance', 'taxes',
                'agent_fees', 'payment_fees', 'other_fees')
BRAZIL_COSTS = ('delivery', 'fees')
CURRENCIES = set(MONEY_SCALES)
CONDITIONS = {'new', 'used', 'refurbished'}


def _object(value, label):
    if not isinstance(value, dict):
        raise ValueError(f'{label} must be an object')
    return value


def _amount(value, label, positive=False):
    if isinstance(value, bool) or not re.fullmatch(r'(?:0|[1-9][0-9]*)(?:\.[0-9]+)?', str(value)):
        raise ValueError(f'{label} must be a canonical decimal amount')
    return bounded_decimal(decimal_value(value, label, positive=positive), label)


def _money(value, label, snapshot):
    if value is None:
        return None
    _object(value, label)
    amount = _amount(value.get('amount'), label)
    currency = value.get('currency')
    if currency not in CURRENCIES or value.get('basis') not in {'scenario', 'observed'}:
        raise ValueError(f'{label} needs a supported currency and basis scenario/observed')
    return _convert(amount, currency, snapshot)


def _convert(amount, currency, snapshot):
    if amount is None:
        return None
    amount = bounded_decimal(Decimal(amount), 'amount')
    if currency == 'BRL':
        return amount.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    if snapshot is None:
        return None
    if currency not in snapshot['brl_per_unit']:
        return None
    return Decimal(convert_brl(amount, currency, snapshot))


def _fmt(value):
    return None if value is None else format(value.quantize(Decimal('.01'), rounding=ROUND_HALF_UP), '.2f')


def _currency_conflict(row, expected):
    """Do not let normalization precedence hide a second explicit currency."""
    if not isinstance(row, dict):
        return False
    for field in ('currency', 'priceCurrency', 'source_currency'):
        value = row.get(field)
        if value is not None and str(value).upper() != expected:
            return True
    for field in ('price', 'raw', 'structured_offer', 'offers'):
        value = row.get(field)
        if isinstance(value, list):
            if any(_currency_conflict(item, expected) for item in value):
                return True
        elif isinstance(value, dict) and _currency_conflict(value, expected):
            return True
    return False


def _valid_component(value):
    if isinstance(value, str):
        return bool(value.strip()) and value.casefold() not in {'unknown', 'unspecified'}
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return decimal_value(value).is_finite()
    if isinstance(value, dict):
        return bool(value) and all(isinstance(k, str) and k.strip() and _valid_component(v)
                                   for k, v in value.items())
    return False


def _same(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def _identity(imported, brazil, equivalence):
    identities = [side.get('identity') for side in (imported, brazil)]
    reasons = []
    for label, side, identity in zip(('imported', 'brazil'), (imported, brazil), identities):
        if not isinstance(identity, dict):
            reasons.append(f'{label}.identity_missing')
            continue
        if (not isinstance(identity.get('model'), str) or not _valid_component(identity['model'])
                or identity.get('condition') not in CONDITIONS
                or not isinstance(identity.get('variant'), dict) or not _valid_component(identity['variant'])):
            reasons.append(f'{label}.identity_incomplete')
        offer = side['offer']
        for field in ('model', 'condition'):
            explicit = offer.get(field)
            if explicit is not None and explicit != 'unknown' and explicit != identity.get(field):
                reasons.append(f'{label}.offer_{field}_conflict')
        for field in ('variant', 'variant_evidence', 'hardware'):
            explicit = offer.get(field)
            variant = identity.get('variant')
            if isinstance(explicit, dict) and isinstance(variant, dict):
                for key in explicit.keys() & variant.keys():
                    if not _same(explicit[key], variant[key]):
                        reasons.append(f'{label}.offer_{key}_conflict')
        # Textual selections are independent evidence, not proof that the
        # asserted structured identity covers every material attribute. This
        # also applies to product families without a relevance profile.
        from .products import selected_variant_texts
        if any(isinstance(offer.get(key), str) and offer[key].strip()
               for key in ('variant', 'selected_variant', 'variant_evidence')) or offer.get('variant_observations'):
            if selected_variant_texts(offer):
                reasons.append(f'{label}.textual_variant_unverified')
        # Explicit configurations in a title also require review; never infer
        # an equivalence from unlabeled capacities or a product-family guess.
        title = offer.get('title')
        if isinstance(title, str) and re.search(
                r'\b(?:ram|memory|ssd|storage|rtx|gtx)\s*[:\-]?\s*\d|'
                r'\b\d+(?:\.\d+)?\s*(?:gb|tb)\b', title, re.I):
            reasons.append(f'{label}.textual_configuration_unverified')
    if all(isinstance(x, dict) for x in identities):
        for field in ('model', 'condition', 'variant'):
            if not _same(identities[0].get(field), identities[1].get(field)):
                reasons.append(f'identity_{field}_mismatch')
    if equivalence.get('status') != 'confirmed':
        reasons.append('equivalence_not_confirmed')
    return {'matches': not reasons, 'reasons': reasons, 'imported': copy.deepcopy(identities[0]),
            'brazil': copy.deepcopy(identities[1]), 'equivalence': copy.deepcopy(equivalence)}


def _brazil_price(offer):
    price = offer.get('price')
    reasons = []
    if not isinstance(price, dict) or price.get('currency') != 'BRL' or price.get('basis') != 'displayed':
        return None, ['brazil_price_requires_displayed_BRL_total']
    try:
        amount = decimal_value(price.get('amount'), 'Brazil price', positive=True)
        if not re.fullmatch(r'(?:0|[1-9][0-9]*)(?:\.[0-9]+)?', str(price.get('amount'))):
            raise ValueError('Brazil price must be a canonical decimal amount')
    except ValueError:
        return None, ['brazil_price_not_a_positive_single_amount']
    bounded_decimal(amount, 'Brazil price')
    # An explicit transaction qualifier cannot be overridden by a numeric field.
    if _transaction_risk(offer):
        reasons.append('brazil_installment_or_deposit_price')
    if _offer_unavailable(offer):
        reasons.append('brazil_offer_unavailable')
    return (None if reasons else amount), reasons


def _transaction_risk(offer):
    price = offer.get('price')
    qualifiers = ' '.join(str(offer.get(k, '')) for k in ('title', 'variant', 'variant_evidence', 'payment_method', 'price_basis', 'transaction_evidence'))
    if isinstance(price, dict):
        qualifiers += ' ' + ' '.join(str(price.get(k, '')) for k in ('raw', 'type', 'scope'))
    from .products import transaction_scope_warnings
    return bool(transaction_scope_warnings(offer) or re.search(
        r'(?i)(?:\bentrada\b|\bsinal\b|\bparcela\w*\b)', qualifiers))


def _costs(side, fields, snapshot):
    raw = _object(side.get('costs', {}), 'costs')
    if set(raw) - set(fields):
        raise ValueError('Unknown cost components: ' + ', '.join(sorted(set(raw) - set(fields))))
    values, missing, details = {}, [], {}
    for name in fields:
        value = _money(raw.get(name), name, snapshot)
        values[name] = value
        if value is None:
            missing.append(name)
        details[name] = {'status': 'known' if value is not None else 'unknown',
                         'input': copy.deepcopy(raw.get(name)), 'amount_brl': _fmt(value)}
    return values, missing, details


def _math(import_total, brazil_total):
    if import_total is None or brazil_total is None or brazil_total <= 0:
        return None
    savings = brazil_total - import_total
    return {'import_total_brl': _fmt(import_total), 'brazil_total_brl': _fmt(brazil_total),
            'savings_amount_brl': _fmt(savings), 'savings_percent': _fmt(savings / brazil_total * 100),
            'outcome': 'import_cheaper' if savings > 0 else 'brazil_cheaper' if savings < 0 else 'equal'}


@monetary_calculation
def compare_brazil(payload, fx_snapshot=None, config=None, as_of=None, max_age_hours=24):
    """Compare explicit scenarios without fetching prices, rates, freight or taxes.

    Arguments override payload.fx and payload.as_of. Config is a load_config()
    result (loaded locally when omitted). Missing FX keeps foreign amounts unknown.
    Eligibility other than confirmed always holds the decision, even with complete
    arithmetic. Confirmation is a caller assertion, never legal clearance.
    """
    _object(payload, 'payload')
    if not isinstance(payload.get('cases'), list):
        raise ValueError('payload.cases must be an array')
    snapshot = fx_snapshot if fx_snapshot is not None else payload.get('fx')
    if snapshot is not None:
        validate_snapshot(snapshot)
    config = load_config() if config is None else _object(config, 'config')
    clock = assess_price_freshness({}, max_age_hours=max_age_hours,
                                   as_of=as_of if as_of is not None else payload.get('as_of'))['as_of']
    fx_freshness = assess_fx_freshness(snapshot, clock)
    results, ids = [], set()
    for case in payload['cases']:
        _object(case, 'case')
        case_id = case.get('id')
        if not isinstance(case_id, str) or not case_id.strip() or case_id in ids:
            raise ValueError('Each case needs a unique nonempty string id')
        ids.add(case_id)
        imported = _object(case.get('imported'), 'imported')
        brazil = _object(case.get('brazil'), 'brazil')
        foreign = _object(imported.get('offer'), 'imported.offer')
        local = _object(brazil.get('offer'), 'brazil.offer')
        offer = normalize_offer(foreign.get('marketplace'), foreign, foreign.get('observed_at'))
        offer['payment_method'] = copy.deepcopy(foreign.get('payment_method'))
        equivalence = _object(case.get('equivalence', {'status': 'unknown'}), 'equivalence')
        eligibility = _object(case.get('import_eligibility', {'status': 'unknown'}), 'import_eligibility')
        if equivalence.get('status') not in {'confirmed', 'unknown', 'mismatch'}:
            raise ValueError('Invalid equivalence status')
        if eligibility.get('status') not in {'confirmed', 'unknown', 'manual_review', 'restricted'}:
            raise ValueError('Invalid import_eligibility status')
        identity = _identity(imported, brazil, equivalence)
        shipping = config['marketplaces'][offer['marketplace']]['shipping']
        if shipping not in {'fansbuy', 'manual', 'excluded'} or (shipping == 'fansbuy' and offer['marketplace'] == 'blibli'):
            raise ValueError('Invalid shipping policy for marketplace')
        excluded = ['international_freight'] if shipping == 'excluded' else []
        costs, missing, cost_details = _costs(imported, IMPORT_COSTS, snapshot)
        br_costs, br_missing, br_details = _costs(brazil, BRAZIL_COSTS, snapshot)
        currency = offer['price']['currency']
        product = _convert(offer['price']['amount'], currency, snapshot)
        reasons = list(identity['reasons'])
        if _offer_unavailable(foreign):
            product = None
            if offer['availability'] not in {'delisted', 'sold'}:
                offer['availability'] = 'unavailable'
            reasons.append('imported_offer_unavailable')
        from .guest import _product_url
        from .products import assess_product
        for label, row, side in (('imported', foreign, imported), ('brazil', local, brazil)):
            model = (side.get('identity') or {}).get('model', '')
            assessment = assess_product(row, model)
            if assessment['price_scope_warnings']:
                reasons.append(label + '_transaction_price_scope_unverified')
                if label == 'imported':
                    product = None
            if _transaction_risk(row) or row.get('ranking_exclusions'):
                reasons.append(label + '_transaction_or_exclusion_hold')
                if label == 'imported':
                    product = None
            if assessment['family'] and assessment['status'] != 'match':
                reasons.append(label + '_product_relevance_' + assessment['status'])
        if offer['url'] and not _product_url(offer['marketplace'], offer['url']):
            product = None
            reasons.append('foreign_product_route_unverified')
        if any(cost.get('currency') not in {None, 'BRL'} for side in (imported, brazil)
               for cost in side.get('costs', {}).values() if isinstance(cost, dict)) or currency != 'BRL':
            if not fx_freshness['recent_reference']:
                reasons.append('fx_' + fx_freshness['status'])
        for label, side in (('imported', imported), ('brazil', brazil)):
            for name, cost in side.get('costs', {}).items():
                if not isinstance(cost, dict) or cost.get('basis') != 'observed':
                    continue
                age = assess_price_freshness({'source_mode': 'guest_api', 'observed_at': cost.get('observed_at')}, max_age_hours, clock)
                if not age['recent_observation']:
                    reasons.append(f'{label}.{name}_observation_{age["status"]}')
                if cost.get('expires_at') is not None:
                    from .freshness import _clock
                    try:
                        if _clock(cost['expires_at']) < _clock(clock):
                            reasons.append(f'{label}.{name}_quote_expired')
                    except ValueError:
                        reasons.append(f'{label}.{name}_expiry_unknown')
        if _currency_conflict(foreign, currency):
            product = None
            offer['price']['amount'] = None
            reasons.append('foreign_explicit_currency_conflict')
        if product is not None and product <= 0:
            product = None
            reasons.append('foreign_price_below_brl_precision')
        if 'possible_deposit' in offer['signals'] or foreign.get('ranking_exclusions'):
            product = None
            reasons.append('foreign_price_scope_unverified')
        conditional_product, conditional_basis = product, 'displayed_price'
        detail = offer.get('source_detail') or {}
        observation = detail.get('price_observation') or detail.get('catalog_observation')
        if offer['source_mode'] in CACHED_MODES and isinstance(observation, dict):
            if observation.get('currency') == currency:
                try:
                    conditional_product = _convert(_amount(observation.get('amount'), 'catalog amount', True), currency, snapshot)
                    conditional_basis = 'unverified_source_observation'
                except ValueError:
                    pass
        br_amount, br_reasons = _brazil_price(local)
        reasons.extend(br_reasons)
        br_product = _convert(br_amount, 'BRL', snapshot)
        if _currency_conflict(local, 'BRL'):
            br_product = None
            reasons.append('brazil_explicit_currency_conflict')
        if br_product is not None and br_product <= 0:
            br_product = None
            reasons.append('brazil_price_below_brl_precision')
        known_costs = sum((x for x in costs.values() if x is not None), Decimal(0))
        br_known_costs = sum((x for x in br_costs.values() if x is not None), Decimal(0))
        if product is None:
            missing.insert(0, 'product_price')
        if br_product is None:
            br_missing.insert(0, 'product_price')
        known = known_costs + (product or Decimal(0))
        br_known = br_known_costs + (br_product or Decimal(0))
        total = known if not missing else None
        br_total = br_known if not br_missing else None
        conditional_total = (known_costs + conditional_product
                             if conditional_product is not None and not any(x != 'product_price' for x in missing) else None)
        conditional_math = _math(conditional_total, br_total)
        def effective_age(row):
            policy = row.get('price_freshness_policy')
            if isinstance(policy, dict) and policy.get('required') is True:
                return min(decimal_value(max_age_hours, positive=True), decimal_value(policy.get('max_age_hours'), positive=True))
            return max_age_hours
        fresh = assess_price_freshness(offer, effective_age(offer), clock)
        br_fresh = assess_price_freshness(local, effective_age(local), clock)
        for label, freshness in (('imported', fresh), ('brazil', br_fresh)):
            if not freshness['recent_observation']:
                reasons.append(f'{label}_price_{freshness["status"]}')
        if missing:
            reasons.append('import_costs_incomplete')
        if br_missing:
            reasons.append('brazil_costs_incomplete')
        if not offer['url']:
            reasons.append('foreign_product_url_missing')
        try:
            url = urlsplit(local.get('url') or '')
            valid_url = url.scheme == 'https' and bool(url.hostname) and not url.username and not url.password
        except ValueError:
            valid_url = False
        if not valid_url or not isinstance(local.get('title'), str) or not local['title'].strip():
            reasons.append('brazil_product_reference_incomplete')
        holds = [] if eligibility['status'] == 'confirmed' else ['import_eligibility_' + eligibility['status']]
        reasons.extend(holds)
        comparable = not reasons and total is not None and br_total is not None
        financial = _math(total, br_total) if comparable else None
        budget = br_total - known if br_total is not None and missing else None
        results.append({
            'id': case_id, 'status': 'comparable' if comparable else 'needs_review',
            'financial_outcome': financial['outcome'] if financial else 'needs_review',
            'savings_amount_brl': financial['savings_amount_brl'] if financial else None,
            'savings_percent': financial['savings_percent'] if financial else None,
            'reasons': list(dict.fromkeys(reasons)), 'identity': identity,
            'import_eligibility': copy.deepcopy(eligibility), 'decision_hold': bool(holds), 'decision_holds': holds,
            'imported': {'offer': offer, 'price_basis': offer['price']['basis'], 'freshness': fresh,
                         'shipping_policy': shipping, 'excluded_costs': [name for name in excluded if name in missing], 'costs': cost_details,
                         'product_price_brl': _fmt(product), 'known_subtotal_brl': _fmt(known),
                         'landed_total_brl': _fmt(total), 'missing_costs': missing},
            'brazil': {'offer': copy.deepcopy(local), 'freshness': br_fresh, 'costs': br_details,
                       'product_price_brl': _fmt(br_product), 'known_subtotal_brl': _fmt(br_known),
                       'complete_total_brl': _fmt(br_total), 'missing_costs': br_missing},
            'missing_costs': {'imported': missing, 'brazil': br_missing},
            'break_even_remaining_cost_budget_brl': _fmt(budget),
            'break_even_scope': 'Budget for ALL missing import components; not a winner or eligibility finding.',
            'conditional_math': dict(conditional_math, basis=conditional_basis,
                                     scope='Arithmetic only; all review reasons and decision holds still apply.') if conditional_math else None,
        })
    return {'schema_version': 1, 'as_of': clock, 'max_age_hours': str(max_age_hours),
            'fx': copy.deepcopy(snapshot), 'fx_freshness': fx_freshness, 'cases': results,
            'scope': 'Caller-supplied scenario; not checkout, inventory verification, customs assessment or legal clearance.',
            'warnings': ['All applicable costs must be explicit; an excluded carrier policy does not imply free freight.',
                         'Potential coupons and cashback are never applied. Payment labels are retained without verifying eligibility.',
                         'FX uses the supplied reference snapshot; spreads, IOF and taxes must be supplied as costs.',
                         'Conditional math and break-even budgets do not establish fresh comparable offers.']}
