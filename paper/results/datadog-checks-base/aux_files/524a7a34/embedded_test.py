#!/usr/bin/env python3
"""Run tests by importing in subprocess"""

import subprocess
import sys

test_code = """
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/datadog-checks-base_env/lib/python3.13/site-packages')

import traceback
import math
import re
from hypothesis import given, strategies as st, settings

# Import the functions we want to test
from datadog_checks.base.utils.common import (
    ensure_bytes, ensure_unicode,
    compute_percent, round_value, pattern_filter
)
from datadog_checks.base.checks.base import AgentCheck
from datadog_checks.base.utils.format import json

print("Testing ensure_bytes/ensure_unicode round-trip...")
@given(st.text())
@settings(max_examples=50)
def test_ensure_bytes_unicode_round_trip(text):
    bytes_result = ensure_bytes(text)
    unicode_result = ensure_unicode(bytes_result)
    assert unicode_result == text

try:
    test_ensure_bytes_unicode_round_trip()
    print("✓ Round-trip test passed")
except Exception as e:
    print(f"✗ Round-trip test failed: {e}")
    traceback.print_exc()

print("\\nTesting compute_percent...")
@given(
    st.floats(min_value=0, max_value=1e10, allow_nan=False, allow_infinity=False),
    st.floats(min_value=1e-10, max_value=1e10, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=50)
def test_compute_percent_range(part, total):
    result = compute_percent(part, total)
    if part <= total:
        assert 0 <= result <= 100
    assert result >= 0

try:
    test_compute_percent_range()
    print("✓ compute_percent range test passed")
except Exception as e:
    print(f"✗ compute_percent range test failed: {e}")
    traceback.print_exc()

print("\\nTesting pattern_filter subset property...")
@given(
    st.lists(st.text(min_size=1), min_size=0, max_size=10),
    st.one_of(st.none(), st.lists(st.text(min_size=1), min_size=1, max_size=3))
)
@settings(max_examples=50)
def test_pattern_filter_subset(items, whitelist):
    if whitelist:
        whitelist = [re.escape(w) for w in whitelist]
    result = pattern_filter(items, whitelist=whitelist)
    assert set(result) <= set(items)

try:
    test_pattern_filter_subset()
    print("✓ pattern_filter subset test passed")
except Exception as e:
    print(f"✗ pattern_filter subset test failed: {e}")
    traceback.print_exc()

print("\\nTesting normalize idempotence...")
@given(st.text())
@settings(max_examples=50)
def test_normalize_idempotent(text):
    check = AgentCheck(name='test', init_config={}, instances=[{}])
    result1 = check.normalize(text, fix_case=False)
    result2 = check.normalize(result1, fix_case=False)
    assert result1 == result2

try:
    test_normalize_idempotent()
    print("✓ normalize idempotence test passed")
except Exception as e:
    print(f"✗ normalize idempotence test failed: {e}")
    traceback.print_exc()

print("\\nTesting JSON round-trip...")
@given(
    st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-1e10, max_value=1e10),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text()
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=5),
            st.dictionaries(st.text(), children, max_size=5)
        ),
        max_leaves=20
    )
)
@settings(max_examples=50)
def test_json_round_trip(obj):
    encoded = json.encode(obj)
    decoded = json.decode(encoded)
    assert decoded == obj

try:
    test_json_round_trip()
    print("✓ JSON round-trip test passed")
except Exception as e:
    print(f"✗ JSON round-trip test failed: {e}")
    traceback.print_exc()

print("\\n" + "="*60)
print("Testing complete!")
"""

# Run the test code using the venv python
result = subprocess.run(
    ['/root/hypothesis-llm/envs/datadog-checks-base_env/bin/python3', '-c', test_code],
    capture_output=True,
    text=True
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)

sys.exit(result.returncode)