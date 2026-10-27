"""Price-observation age, never a claim of live inventory or checkout acceptance."""

from datetime import date, datetime, timezone
from decimal import Decimal

from .models import decimal_value

CACHED_MODES = {'search_index', 'indexed_product_block', 'connector_product_open_cached',
                'category_card', 'proxy_catalog'}
OBSERVED_MODES = {'guest_product_page', 'guest_api', 'listing_content', 'product_detail',
                  'listing', 'detail', 'native_search', 'retailer_product_page', 'user_observation'}


def _clock(value):
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('as_of must be a timezone-aware timestamp') from None
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError('as_of must be a timezone-aware timestamp')
    return value.astimezone(timezone.utc)


def assess_price_freshness(offer, max_age_hours=24, as_of=None):
    """Retain retrieval and crawl labels without treating them as source-price time."""
    if not isinstance(offer, dict):
        raise ValueError('Offer must be an object')
    limit = decimal_value(max_age_hours, 'max_age_hours', positive=True)
    if limit > 8760:
        raise ValueError('max_age_hours must be at most 8760')
    now = _clock(as_of)
    mode = offer.get('source_mode', 'unspecified')
    detail = offer.get('source_detail') or offer.get('detail')
    observation = (detail.get('price_observation') or detail.get('catalog_observation')) if isinstance(detail, dict) else None
    label = observation.get('crawl_age') if isinstance(observation, dict) else None
    result = {'status': 'unknown', 'recent_observation': False, 'age_hours': None,
              'max_age_hours': str(limit), 'as_of': now.isoformat(), 'source_mode': mode,
              'source_price_observed_at': None, 'cache_age_label': label,
              'basis': 'adapter_or_caller_timestamp_assertion; not independent freshness or checkout proof'}
    if mode in CACHED_MODES:
        result.update(status='cached_or_aggregated_source',
                      reason='A retrieval timestamp does not refresh the underlying product price or inventory.')
        return result
    if mode not in OBSERVED_MODES:
        result['reason'] = 'Source observation mode is unknown.'
        return result
    stamp = offer.get('observed_at')
    try:
        if stamp is None:
            raise ValueError
        observed = _clock(stamp)
    except (ValueError, TypeError):
        result['reason'] = 'No valid source price observation timestamp.'
        return result
    result['source_price_observed_at'] = observed.isoformat()
    age = Decimal(str((now - observed).total_seconds())) / Decimal(3600)
    result['age_hours'] = str(age.quantize(Decimal('.01')))
    if age < 0:
        result.update(status='future_timestamp', reason='Source observation timestamp is later than the comparison time.')
    elif age > limit:
        result.update(status='older_than_limit', reason='Source observation is older than the requested limit.')
    else:
        result.update(status='recent_observation', recent_observation=True,
                      reason='Source observation time is within the limit; current stock and checkout remain unverified.')
    return result


def annotate_price_freshness(offer, required=False, max_age_hours=24, as_of=None):
    """Annotate an observation in place; exported required policies survive re-ranking."""
    prior = offer.get('price_freshness_policy')
    if isinstance(prior, dict) and prior.get('required') is True:
        required = True
        max_age_hours = min(decimal_value(max_age_hours, positive=True),
                            decimal_value(prior.get('max_age_hours', max_age_hours), positive=True))
    assessment = assess_price_freshness(offer, max_age_hours, as_of)
    offer['price_freshness'] = assessment
    if required:
        offer['price_freshness_policy'] = {'required': True, 'max_age_hours': assessment['max_age_hours']}
    exclusions = offer.setdefault('ranking_exclusions', [])
    exclusions[:] = [value for value in exclusions if not value.startswith('price_freshness_')]
    if required and not assessment['recent_observation']:
        exclusions.append('price_freshness_' + assessment['status'])
    return offer


def assess_fx_freshness(snapshot, as_of=None, max_age_days=7):
    """Daily reference dates allow weekends; a stale rate remains arithmetic only."""
    now = _clock(as_of)
    result = {'recent_reference': False, 'status': 'unknown', 'max_age_days': max_age_days,
              'rate_date': None, 'age_days': None}
    if not isinstance(snapshot, dict):
        return result
    try:
        stamp = date.fromisoformat(snapshot.get('rate_date', ''))
    except (ValueError, TypeError):
        return result
    age = (now.date() - stamp).days
    result.update(rate_date=stamp.isoformat(), age_days=age)
    result['status'] = 'future_rate_date' if age < 0 else 'older_than_limit' if age > max_age_days else 'recent_reference'
    result['recent_reference'] = result['status'] == 'recent_reference'
    return result
