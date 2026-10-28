"""Bounded arithmetic for indicative monetary calculations."""

from decimal import Context, DecimalException, localcontext
from functools import wraps


def bounded_decimal(value, name):
    """Allow at most 18 integer and 12 meaningful fractional digits."""
    if value.is_zero():
        return value
    digits = value.as_tuple().digits
    exponent = value.as_tuple().exponent
    # Ignore insignificant trailing zeroes without rounding in the caller's context.
    for digit in reversed(digits):
        if digit:
            break
        exponent += 1
    if value.adjusted() >= 18 or exponent < -12:
        raise ValueError(f'{name} exceeds calculation bounds (18 integer, 12 fractional digits)')
    return value

def monetary_calculation(function):
    """Isolate arithmetic from ambient context and translate decimal failures."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            with localcontext(Context(prec=64)):
                return function(*args, **kwargs)
        except DecimalException as exc:
            raise ValueError('monetary calculation exceeds supported precision or range') from exc
    return wrapped
