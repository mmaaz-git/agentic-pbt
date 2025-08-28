# Mock implementation based on the functions described
# For testing purposes only

import re
from decimal import ROUND_HALF_UP, Decimal


def ensure_bytes(s):
    """Convert input to bytes, ensuring UTF-8 encoding"""
    if isinstance(s, bytes):
        return s
    return s.encode('utf-8')


def ensure_unicode(s):
    """Convert input to unicode string, decoding from UTF-8 if needed"""
    if isinstance(s, bytes):
        return s.decode('utf-8')
    return str(s)


def compute_percent(part, total):
    """Calculate percentage by dividing part by total and multiplying by 100"""
    if total == 0:
        return 0.0
    return (part / total) * 100


def total_time_to_temporal_percent(total_time, scale):
    """Convert time measurements to a temporal percentage representation"""
    if scale == 0:
        return 0.0
    return (total_time / scale) * 100


def exclude_undefined_keys(mapping):
    """Remove dictionary entries with None values"""
    return {k: v for k, v in mapping.items() if v is not None}


def round_value(value, precision=0, rounding_method=ROUND_HALF_UP):
    """Round a numeric value to specified precision"""
    return float(Decimal(str(value)).quantize(Decimal(10) ** -precision, rounding=rounding_method))


def pattern_filter(items, whitelist=None, blacklist=None, key=None):
    """Filter list items using regex whitelist/blacklist patterns"""
    if key is None:
        key = lambda x: x
    
    if whitelist:
        items = [item for item in items if any(re.search(pattern, key(item)) for pattern in whitelist)]
    
    if blacklist:
        items = [item for item in items if not any(re.search(pattern, key(item)) for pattern in blacklist)]
    
    return items