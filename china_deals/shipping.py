"""Fansbuy estimates and indicative Brazilian import costs (stdlib only)."""
import json
import math
import re
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from urllib.error import URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .decimal_math import bounded_decimal, monetary_calculation

_API = 'https://fansbuy.com/apiv2/'
_SOURCE = _API + 'estimatesTest'
_FRONTEND = 'https://fansbuy.com/assets/js/EstimatesView.DX2h0m2j.js'
_RFB_MANUAL = 'https://www.gov.br/receitafederal/pt-br/assuntos/aduana-e-comercio-exterior/manuais/remessas-postal-e-expressa'
_TAX_SOURCE = _RFB_MANUAL + '/topicos/tributacao'
_CATEGORIES = {'Electric': 'ischarged', 'Brand': 'isbrand', 'liquid': 'isliquid',
               'bag': 'isbag', 'food': 'isfood', 'shoes': 'isshose',
               'Battery': 'iscell', 'Knives': 'istool', 'powder': 'ispowder',
               'watch': 'iswatch', 'cosmetics': 'iscosmetics',
               'magnetic': 'ismagnetism', 'perfume': 'isperfume'}


def _decimal(value, name, *, positive=False):
    try:
        if isinstance(value, bool):
            raise ValueError
        result = Decimal(str(value))
        if not result.is_finite() or (result <= 0 if positive else result < 0):
            raise ValueError
        return result
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f'{name} must be a finite {"positive" if positive else "non-negative"} number') from None


def _inputs(weight_g, dimensions_cm, categories):
    weight = _decimal(weight_g, 'weight_g', positive=True)
    if dimensions_cm is not None:
        if not isinstance(dimensions_cm, (list, tuple)) or len(dimensions_cm) != 3:
            raise ValueError('dimensions_cm must contain three positive dimensions')
        dimensions_cm = tuple(_decimal(x, 'dimension', positive=True) for x in dimensions_cm)
    if categories is not None and (not isinstance(categories, (list, tuple)) or
                                   any(not isinstance(x, str) or not x for x in categories)):
        raise ValueError('categories must be a list of category names')
    return weight, dimensions_cm, categories


def _field(row, key, reasons, *, empty_zero=False):
    value = row.get(key)
    if empty_zero and value == '':
        return Decimal(0)
    try:
        return _decimal(value, key)
    except ValueError:
        reasons.append(f'unknown constraint: {key}')
        return None


def normalize_fansbuy_quotes(payload, weight_g, dimensions_cm=None, categories=None):
    """Normalize an API response; categories=[] explicitly asserts no special category.

    Captured responses have no trusted observation time; normalized_at is processing time.
    Routes in rejected retain their quote and all known reasons.
    """
    weight, dims, categories = _inputs(weight_g, dimensions_cm, categories)
    if not isinstance(payload, dict) or payload.get('code') != 0 or not isinstance(payload.get('data'), list):
        raise ValueError('invalid or unsuccessful Fansbuy estimates response')
    accepted, rejected = [], []
    for row in payload['data']:
        if not isinstance(row, dict):
            raise ValueError('invalid Fansbuy route')
        reasons = []
        enabled = row.get('enabled')
        if isinstance(enabled, bool) or str(enabled) not in ('0', '1'):
            reasons.append('unknown constraint: enabled')
        elif str(enabled) == '0':
            reasons.append('route disabled')
        if 'is_disable' in row:
            disabled = row['is_disable']
            if isinstance(disabled, bool) or str(disabled) not in ('0', '1'):
                reasons.append('unknown constraint: is_disable')
            elif str(disabled) == '1':
                reasons.append('route disabled by is_disable')
        if categories is None:
            reasons.append('unknown constraint: product categories not supplied')
        else:
            special = row.get('special')
            if isinstance(special, str):
                try:
                    special = json.loads(special)
                except (ValueError, TypeError):
                    special = None
            for category in categories:
                key = _CATEGORIES.get(category)
                if key is None:
                    reasons.append(f'unknown category: {category}')
                elif not isinstance(special, dict) or isinstance(special.get(key), bool) or str(special.get(key)) not in ('0', '1'):
                    reasons.append(f'unknown constraint: {category} ({key})')
                elif str(special[key]) == '0':
                    reasons.append(f'category not accepted: {category}')
        minimum = _field(row, 'min_weight', reasons)
        maximum = _field(row, 'max_weight', reasons)
        side = _field(row, 'max_anySide', reasons)
        side_sum = _field(row, 'max_sumSide', reasons)
        threshold = _field(row, 'sidelength', reasons)
        divisor = _field(row, 'v_percent', reasons, empty_zero=True)
        side_divisor = _field(row, 'side_v_percent', reasons, empty_zero=True)
        volume_limit = _field(row, 'volume_weight_limit', reasons, empty_zero=True)
        if minimum is not None and weight < minimum:
            reasons.append('below minimum weight')
        if maximum is not None and (maximum == 0 or weight > maximum):
            reasons.append('unknown constraint: max_weight' if maximum == 0 else 'above maximum weight')
        if dims is None:
            if any(x is not None and x > 0 for x in (side, side_sum, threshold, divisor, volume_limit)):
                reasons.append('unknown constraint: dimensions required')
        else:
            if side is not None and side > 0 and max(dims) > side:
                reasons.append('maximum side exceeded')
            if side_sum is not None and side_sum > 0 and sum(dims) > side_sum:
                reasons.append('maximum sum of sides exceeded')
            if divisor is not None and threshold is not None:
                active = divisor
                if threshold > 0 and max(dims) > threshold:
                    active = side_divisor
                    if not active:
                        reasons.append('unknown constraint: side volumetric divisor')
                if active:
                    volumetric = dims[0] * dims[1] * dims[2] * 1000 / active
                    if volume_limit is not None and volume_limit > 0 and volumetric > volume_limit:
                        reasons.append('volumetric weight limit exceeded')
                    if maximum is not None and maximum > 0 and volumetric > maximum:
                        reasons.append('volumetric weight exceeds maximum weight')
        if divisor == 0 and volume_limit is not None and volume_limit > 0:
            reasons.append('unknown constraint: volumetric divisor for volume weight limit')
        try:
            fee = _decimal(row.get('total_fee'), 'total_fee', positive=True)
            fee_text = str(fee.quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
        except (ValueError, InvalidOperation):
            fee_text = None
            reasons.append('unknown quote: total_fee')
        quote = {'shipping_area_id': row.get('shipping_area_id'), 'shipping_id': row.get('shipping_id'),
                 'shipping_name': row.get('shipping_name'), 'currency': 'CNY', 'total_fee': fee_text,
                 'travel_time': row.get('travel_time'), 'quote_kind': 'base_estimate',
                 'carrier_description': row.get('shipping_desc'), 'carrier_tip': row.get('shipping_tip'),
                 'carrier_flags': {key: row.get(key) for key in ('enabled', 'is_disable', 'special', 'is_tax', 'is_invoice')},
                 'packaging': {key: row.get(key) for key in ('mustVacuum', 'is_box', 'is_bag', 'mustbox_weight')},
                 'source_constraints': {key: row.get(key) for key in ('min_weight', 'max_weight', 'max_anySide', 'max_sumSide', 'sidelength', 'v_percent', 'side_v_percent', 'volume_weight_limit', 'declaration_limit', 'customslimit', 'surcharge', 'goodsname_limit', 'max_acceptForday')},
                 'discount_display': (str(row['discount_display']) if row.get('discount_display') is not None else None), 'source': _SOURCE,
                 'warnings': ['Discount display is conditional; coupon eligibility is unverified.',
                              'Carrier and customs acceptance require confirmation.'],
                 'reasons': reasons}
        (rejected if reasons else accepted).append(_json_safe(quote))
    return {'source': _SOURCE, 'source_observed_at': None,
            'normalized_at': datetime.now(timezone.utc).isoformat(), 'currency': 'CNY',
            'quotes': accepted, 'rejected': rejected,
            'warnings': ['Quotes are estimates for the supplied package; tax and final eligibility are not verified.']}


def _json_safe(value):
    """Preserve source fields while preventing non-JSON values in public output."""
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError('invalid non-finite Fansbuy response value')
        return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError('invalid non-finite Fansbuy response value')
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return {key: _json_safe(item) for key, item in value.items()}
    raise ValueError('invalid Fansbuy response value')


def _reject_constant(value):
    raise ValueError('invalid JSON constant')


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if fp is not None:
            fp.close()
        raise ValueError('Fansbuy redirect denied')


def _post(path, body, timeout):
    request = Request(_API + path, data=json.dumps(body).encode(),
                      headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}, method='POST')
    try:
        with build_opener(_NoRedirects()).open(request, timeout=timeout) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise ValueError('response too large')
            return json.loads(raw, parse_float=Decimal, parse_constant=_reject_constant)
    except (OSError, URLError, ValueError, UnicodeError) as exc:
        raise ValueError('Fansbuy request failed; check network access and try again') from exc


def fansbuy_quotes(weight_g, dimensions_cm=None, categories=None, timeout=30):
    weight, dims, categories = _inputs(weight_g, dimensions_cm, categories)
    timeout = float(_decimal(timeout, 'timeout', positive=True))
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout must be a finite positive number')
    areas = _post('web/cart/checkarea', {'serch': 'hot'}, timeout)
    try:
        if areas['code'] != 0:
            raise ValueError
        matches = {str(x['region_id']) for group in areas['data'].values() for x in group
                   if str(x.get('c_code', '')).upper() == 'BR'}
        if len(matches) != 1:
            raise ValueError
        country = matches.pop()
    except (KeyError, TypeError, ValueError, AttributeError):
        raise ValueError('Fansbuy Brazil region could not be resolved uniquely') from None
    volume = dims[0] * dims[1] * dims[2] if dims else Decimal(0)
    # JSON numbers are required by the public endpoint.
    payload = _post('estimatesTest', {'weight': float(weight), 'volume': float(volume),
                                     'currency': 'CNY', 'price': 0, 'country': country}, timeout)
    result = normalize_fansbuy_quotes(payload, weight, dims, categories)
    result['source_observed_at'] = datetime.now(timezone.utc).isoformat()
    return result


@monetary_calculation
def estimate_landed_cost(goods_cny, freight_cny, cny_brl, usd_brl, icms_rate,
                         domestic_cny='0', agent_fee_cny='0', insurance_cny='0',
                         remessa_conforme=False):
    """Estimate using inputs with at most 18 integer and 12 meaningful fractional digits."""
    goods = _decimal(goods_cny, 'goods_cny', positive=True)
    freight = _decimal(freight_cny, 'freight_cny')
    domestic = _decimal(domestic_cny, 'domestic_cny')
    agent = _decimal(agent_fee_cny, 'agent_fee_cny')
    insurance = _decimal(insurance_cny, 'insurance_cny')
    cny = _decimal(cny_brl, 'cny_brl', positive=True)
    usd = _decimal(usd_brl, 'usd_brl', positive=True)
    rate = _decimal(icms_rate, 'icms_rate')
    for name, value in (('goods_cny', goods), ('freight_cny', freight), ('domestic_cny', domestic),
                        ('agent_fee_cny', agent), ('insurance_cny', insurance), ('cny_brl', cny),
                        ('usd_brl', usd), ('icms_rate', rate)):
        bounded_decimal(value, name)
    if rate >= 1:
        raise ValueError('icms_rate must be a fraction from 0 inclusive to 1 exclusive')
    if not isinstance(remessa_conforme, bool):
        raise ValueError('remessa_conforme must be a boolean')
    customs = (goods + freight + domestic + insurance) * cny
    if customs / usd > 3000:
        raise ValueError('customs value exceeds the USD 3000 RTS limit')
    def quantize(value):
        return value.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
    customs_line = quantize(customs)
    duty_rate = Decimal('0.60')
    deduction_usd = Decimal(0)
    if remessa_conforme:
        # Receita's current manual: DIR registered from 2026-05-12, certified site, natural person.
        if customs / usd <= 50:
            duty_rate = Decimal(0)
        else:
            deduction_usd = Decimal(30)
    deduction_brl = quantize(deduction_usd * usd)
    duty = max(Decimal(0), quantize(customs_line * duty_rate) - deduction_brl)
    icms = quantize((customs_line + duty) / (1 - rate) * rate)
    agent_line = quantize(agent * cny)
    total = customs_line + duty + icms + agent_line
    return {'currency': 'BRL', 'customs_value_brl': str(customs_line),
            'customs_value_usd': str(quantize(customs / usd)), 'import_duty_rate': str(duty_rate),
            'import_duty_deduction_usd': str(deduction_usd), 'import_duty_deduction_brl': str(deduction_brl),
            'import_duty_brl': str(duty), 'icms_rate': str(rate), 'icms_brl': str(icms),
            'agent_fee_brl': str(agent_line),
            'total_brl': str(total), 'remessa_conforme': remessa_conforme, 'quote_kind': 'indicative_estimate',
            'shipment_eligibility_verified': False,
            'policy': {'id': 'br-rts-2026-05-12', 'source_url': _TAX_SOURCE, 'checked_on': '2026-10-27',
                       'prc_effective_from': '2026-05-12', 'recipient': 'natural_person' if remessa_conforme else 'unspecified'},
            'assumptions': {
                'recorded_on': '2026-10-27',
                'inputs': {'goods_cny': str(goods), 'freight_cny': str(freight),
                           'domestic_cny': str(domestic), 'agent_fee_cny': str(agent),
                           'insurance_cny': str(insurance), 'cny_brl': str(cny),
                           'usd_brl': str(usd), 'icms_rate': str(rate)},
                'duty_rate': {'value': str(duty_rate), 'source_url': _TAX_SOURCE, 'policy_page_verified': True, 'checked_on': '2026-10-27'},
                'rts_limit_usd': {'value': '3000', 'source_url': _TAX_SOURCE, 'policy_page_verified': True, 'checked_on': '2026-10-27'}},
            'warnings': ['Not an official quote; tax treatment and exchange rates may differ.',
                         'Domestic freight is included in the assumed customs base. Buying agent fee is outside it; actual customs valuation is uncertain.',
                         'RTS eligibility and any exemptions have not been verified for this shipment.',
                         'PRC eligibility is user-supplied when selected; certified retailer, natural-person recipient and DIR registration date are not checked.',
                         'Tax policy is a 2026-10-27 source snapshot; recheck current rules and destination-state ICMS before relying on it.',
                         'Excludes additional fees, storage, currency conversion charges, penalties and other taxes.']}


def assess_import(condition='unknown', categories=None, ncm=None):
    if not isinstance(condition, str) or not condition.strip():
        raise ValueError('condition must be a nonempty string')
    if categories is not None and (not isinstance(categories, (list, tuple)) or any(not isinstance(c, str) or not c.strip() for c in categories)):
        raise ValueError('categories must be a list of strings')
    if ncm is not None and (not isinstance(ncm, str) or not re.fullmatch(r'(?:[0-9]{8}|[0-9]{4}\.[0-9]{2}\.[0-9]{2})', ncm)):
        raise ValueError('ncm must have eight digits, optionally formatted as 0000.00.00')
    topics = []
    def add(topic, source_type, url):
        topics.append({'topic': topic, 'source_type': source_type, 'source_url': url,
                       'verified': False, 'checked_at': None})
    add('Verify classification, customs treatment and any required approvals for this specific shipment.', 'government',
        _RFB_MANUAL + '/topicos/restricoes-proibicoes')
    if condition.strip().lower() in ('used', 'secondhand', 'second-hand', 'usado', 'usada'):
        add('Review import restrictions and possible exceptions for used goods with Receita Federal and MDIC.', 'government',
            _RFB_MANUAL + '/topicos/restricoes-proibicoes')
    names = {c.casefold() for c in categories or []}
    if names & {'battery', 'liquid', 'magnetic', 'perfume'}:
        add('Review dangerous-goods classification, packaging, documentation and carrier acceptance for air transport.', 'transport',
            'https://www.iata.org/en/programs/cargo/dgr/')
        add('Confirm the selected carrier accepts the specific contents and route.', 'carrier', 'https://fansbuy.com/')
    if 'electric' in names:
        add('If the product uses telecommunications or radio, review whether Anatel certification is required.', 'government',
            'https://www.gov.br/anatel/pt-br/regulado/certificacao-de-produtos')
    if names & {'cosmetics', 'food', 'perfume'}:
        add('Review applicable Anvisa health and import requirements for the specific product.', 'government',
            'https://www.gov.br/anvisa/pt-br/assuntos/importacao')
    if 'knives' in names:
        add('Review classification, controlled-item restrictions and carrier acceptance for the specific knife.', 'government',
            'https://www.gov.br/receitafederal/pt-br/assuntos/aduana-e-comercio-exterior/remessas-internacionais')
    return {'status': 'manual_review', 'condition': condition, 'categories': list(categories) if categories is not None else None,
            'ncm': ncm, 'reasons': [item['topic'] for item in topics], 'sources': topics,
            'warnings': ['This assessment is not legal or customs clearance.',
                         'Sea transport does not cure an import prohibition; batteries are not universally sea-only.']}
