#!/usr/bin/env python3
"""Direct inline testing of trino.client properties."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

# Import and execute tests inline
exec("""
import base64
import urllib.parse
from trino.client import (
    InlineSegment, 
    get_header_values,
    get_session_property_values,
    _DelayExponential,
    _parse_retry_after_header,
    TrinoRequest,
    ClientSession
)

print("Testing InlineSegment base64 handling...")

# Test 1: Check InlineSegment with edge cases
data = b"\\x00\\x01\\x02\\xff"  # Binary data with null and high bytes
encoded = base64.b64encode(data).decode('utf-8')
segment_data = {
    "type": "inline",
    "data": encoded,
    "metadata": {"segmentSize": str(len(data))}
}
segment = InlineSegment(segment_data)
result = segment.data
print(f"Binary data test: {data == result}")
assert data == result

print("\\nTesting header parsing edge cases...")

# Test 2: Empty header values
headers = {'X-Test': ''}
try:
    parsed = get_header_values(headers, 'X-Test')
    print(f"Empty header parsed as: {parsed}")
    # Check what happens with empty string
    if parsed != ['']:
        print(f"UNEXPECTED: Empty header should parse to [''], got {parsed}")
except Exception as e:
    print(f"ERROR parsing empty header: {e}")

# Test 3: Header with only commas
headers = {'X-Test': ',,,'}
try:
    parsed = get_header_values(headers, 'X-Test')
    print(f"Comma-only header parsed as: {parsed}")
    # This might produce empty strings
except Exception as e:
    print(f"ERROR parsing comma-only header: {e}")

# Test 4: Session properties with empty key or value
headers = {'X-Session': '=value'}  # Empty key
try:
    parsed = get_session_property_values(headers, 'X-Session')
    print(f"Empty key session property: {parsed}")
except Exception as e:
    print(f"ERROR parsing empty key: {e}")

headers = {'X-Session': 'key='}  # Empty value
try:
    parsed = get_session_property_values(headers, 'X-Session')
    print(f"Empty value session property: {parsed}")
    # Should be [('key', '')]
except Exception as e:
    print(f"ERROR parsing empty value: {e}")

# Test 5: Session property without equals sign
headers = {'X-Session': 'keyonly'}
try:
    parsed = get_session_property_values(headers, 'X-Session')
    print(f"No-equals session property: {parsed}")
except Exception as e:
    print(f"ERROR parsing no-equals property: {e}")
    import traceback
    traceback.print_exc()

print("\\nTesting exponential backoff edge cases...")

# Test 6: Exponential backoff with zero base
try:
    calc = _DelayExponential(base=0, exponent=2, jitter=False)
    delay = calc(5)
    print(f"Zero base delay: {delay}")
    assert delay == 0, "Zero base should always give zero delay"
except Exception as e:
    print(f"ERROR with zero base: {e}")

# Test 7: Exponential backoff with negative attempt
try:
    calc = _DelayExponential(base=0.1, exponent=2, jitter=False)
    delay = calc(-1)
    print(f"Negative attempt delay: {delay}")
    # 0.1 * 2^(-1) = 0.05
except Exception as e:
    print(f"ERROR with negative attempt: {e}")

print("\\nTesting parse_retry_after_header edge cases...")

# Test 8: Parse retry-after with float
try:
    result = _parse_retry_after_header(3.14)
    print(f"Float retry-after: {result}")
except Exception as e:
    print(f"ERROR parsing float retry-after: {e}")

# Test 9: Parse retry-after with negative
try:
    result = _parse_retry_after_header(-5)
    print(f"Negative retry-after: {result}")
except Exception as e:
    print(f"ERROR parsing negative retry-after: {e}")

print("\\nTesting role formatting edge cases...")

# Test 10: Role formatting with empty string
try:
    formatted = ClientSession._format_roles("")
    print(f"Empty role formatted as: {formatted}")
except Exception as e:
    print(f"ERROR formatting empty role: {e}")

# Test 11: Role formatting with special characters
try:
    formatted = ClientSession._format_roles({"catalog": "role-with-dash"})
    print(f"Role with dash: {formatted}")
    assert formatted["catalog"] == "ROLE{role-with-dash}"
except Exception as e:
    print(f"ERROR formatting role with dash: {e}")

print("\\nTesting extra credential validation...")

# Test 12: Credential with empty key
try:
    TrinoRequest._verify_extra_credential(("", "value"))
    print("ERROR: Empty key should be rejected!")
except ValueError as e:
    print(f"Empty key correctly rejected: {e}")

# Test 13: Credential with just whitespace key
try:
    TrinoRequest._verify_extra_credential(("   ", "value"))
    print("ERROR: Whitespace-only key should be rejected!")
except ValueError as e:
    print(f"Whitespace key correctly rejected: {e}")

print("\\n" + "="*60)
print("Inline tests completed!")
""")