#!/usr/bin/env python3
"""Find bugs in trino.client using Hypothesis property tests."""

import sys
import os

# Set up path
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')
os.chdir('/root/hypothesis-llm/worker_/3')

# Direct execution of property tests
exec("""
from hypothesis import given, strategies as st, settings, example
from hypothesis.strategies import composite
import urllib.parse
import base64
import traceback

# Import modules to test
from trino.client import (
    get_session_property_values,
    get_header_values,
    _parse_retry_after_header,
    InlineSegment,
    _DelayExponential,
    TrinoRequest,
    ClientSession
)

print("Starting property-based bug hunt...")
print("=" * 60)

# Bug Hunt 1: Session property parsing with edge cases
print("\\nTesting session property parsing...")

def check_session_parsing(key_value_pairs):
    # Create header value
    try:
        header_value = ",".join(f"{k}={urllib.parse.quote_plus(v)}" for k, v in key_value_pairs)
        headers = {'X-Test': header_value}
        parsed = get_session_property_values(headers, 'X-Test')
        
        # Check round-trip
        for i, (k, v) in enumerate(key_value_pairs):
            if i >= len(parsed) or parsed[i] != (k, v):
                return False, f"Mismatch at index {i}: expected {(k,v)}, got {parsed[i] if i < len(parsed) else 'nothing'}"
        return True, None
    except Exception as e:
        return False, f"Exception: {e}"

# Test specific cases that might break
test_cases = [
    [("", "value")],  # empty key
    [("key", "")],    # empty value  
    [("key_only",)],  # tuple with only key (might cause unpacking error)
    [],               # empty list
    [("=", "value")], # key is equals sign
    [("key", "=")],   # value is equals sign
]

for case in test_cases:
    try:
        if len(case) > 0 and len(case[0]) == 1:
            # Skip single-element tuples
            continue
        success, error = check_session_parsing(case)
        if not success:
            print(f"  POTENTIAL BUG with {case}: {error}")
        else:
            print(f"  OK: {case}")
    except Exception as e:
        print(f"  ERROR with {case}: {e}")
        traceback.print_exc()

# Bug Hunt 2: Header parsing with malformed input
print("\\nTesting header value parsing...")

malformed_headers = [
    "",           # empty
    ",",          # single comma
    ",,",         # multiple commas
    " , , ",      # commas with spaces
    "value,",     # trailing comma
    ",value",     # leading comma
]

for header_val in malformed_headers:
    try:
        headers = {'X-Test': header_val}
        result = get_header_values(headers, 'X-Test')
        print(f"  '{header_val}' -> {result}")
        
        # Check for unexpected empty strings
        if '' in result and header_val.strip() != '':
            print(f"    NOTE: Empty string in result for non-empty input")
    except Exception as e:
        print(f"  ERROR with '{header_val}': {e}")

# Bug Hunt 3: Session properties without equals
print("\\nTesting session properties without equals...")

no_equals_cases = [
    "keyonly",
    "key1,key2", 
    "key=value,keyonly",
    "keyonly,key=value"
]

for case in no_equals_cases:
    try:
        headers = {'X-Session': case}
        result = get_session_property_values(headers, 'X-Session')
        print(f"  '{case}' -> {result}")
    except ValueError as e:
        if "not enough values to unpack" in str(e):
            print(f"  BUG FOUND: '{case}' causes unpacking error!")
            print(f"    Error: {e}")
        else:
            print(f"  ERROR: {e}")
    except Exception as e:
        print(f"  ERROR with '{case}': {e}")

# Bug Hunt 4: Parse retry-after with unusual values
print("\\nTesting _parse_retry_after_header with edge cases...")

unusual_values = [
    0,            # zero
    -1,           # negative
    "0",          # string zero
    "-1",         # string negative
    "not_a_number",  # non-numeric string
    "",           # empty string
    None,         # None (if accepted)
    float('inf'), # infinity
    float('nan'), # NaN
]

for val in unusual_values:
    try:
        if val is None:
            continue  # Skip None as it likely isn't meant to be handled
        result = _parse_retry_after_header(val)
        print(f"  {val} ({type(val).__name__}) -> {result}")
        
        # Check for weird results
        if isinstance(result, float):
            import math
            if math.isnan(result):
                print(f"    WARNING: NaN result!")
            elif math.isinf(result):
                print(f"    WARNING: Infinite result!")
    except Exception as e:
        print(f"  ERROR with {val}: {e}")

# Bug Hunt 5: Exponential backoff with extreme values
print("\\nTesting exponential backoff with extreme values...")

extreme_cases = [
    (0, 2),        # zero base
    (1, 0),        # zero exponent
    (1, 1),        # exponent of 1 (linear)
    (0.00001, 10), # tiny base, large exponent
    (1000, 10),    # large base and exponent
    (-1, 2),       # negative base (if accepted)
    (1, -2),       # negative exponent (if accepted)
]

for base, exp in extreme_cases:
    try:
        if base < 0 or exp < 0:
            # Skip negatives which likely aren't meant to be supported
            continue
        calc = _DelayExponential(base=base, exponent=exp, jitter=False, max_delay=1000000)
        
        # Test a few attempts
        for attempt in [0, 1, 10, 100]:
            delay = calc(attempt)
            expected = base * (exp ** attempt)
            if abs(delay - min(expected, 1000000)) > 0.0001:
                print(f"  MISMATCH: base={base}, exp={exp}, attempt={attempt}")
                print(f"    Expected: {expected}, Got: {delay}")
    except Exception as e:
        print(f"  ERROR with base={base}, exp={exp}: {e}")

# Bug Hunt 6: InlineSegment with malformed data
print("\\nTesting InlineSegment with edge cases...")

# Test with invalid base64
try:
    segment_data = {
        "type": "inline",
        "data": "not-valid-base64!@#",  # Invalid base64
        "metadata": {"segmentSize": "10"}
    }
    segment = InlineSegment(segment_data)
    data = segment.data
    print(f"  Invalid base64 handled: got {len(data)} bytes")
except Exception as e:
    print(f"  BUG: Invalid base64 causes error: {e}")

# Test with metadata mismatch
try:
    real_data = b"test"
    encoded = base64.b64encode(real_data).decode('utf-8')
    segment_data = {
        "type": "inline",
        "data": encoded,
        "metadata": {"segmentSize": "999"}  # Wrong size
    }
    segment = InlineSegment(segment_data)
    data = segment.data
    if len(data) != 999:
        print(f"  Metadata size mismatch ignored: claimed 999, got {len(data)} bytes")
except Exception as e:
    print(f"  ERROR with size mismatch: {e}")

print("\\n" + "=" * 60)
print("Bug hunt completed!")
""")