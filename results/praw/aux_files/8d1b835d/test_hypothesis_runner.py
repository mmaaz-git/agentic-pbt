#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, Verbosity
from hypothesis import __version__ as hyp_version
import string

print(f"Using Hypothesis version: {hyp_version}")

from praw.util import camel_to_snake, snake_case_keys

# Test 1: Idempotence property
print("\nTest 1: Testing camel_to_snake idempotence property...")
@given(st.text(alphabet=string.ascii_letters + string.digits, min_size=0, max_size=100))
@settings(max_examples=200, verbosity=Verbosity.verbose)
def test_idempotence(s):
    once = camel_to_snake(s)
    twice = camel_to_snake(once) 
    assert once == twice, f"Failed for input '{s}': once='{once}', twice='{twice}'"

try:
    test_idempotence()
    print("✓ Idempotence test PASSED")
except AssertionError as e:
    print(f"✗ Idempotence test FAILED: {e}")
except Exception as e:
    print(f"✗ Test error: {e}")

# Test 2: Output format (should be lowercase)
print("\nTest 2: Testing output is always lowercase...")
@given(st.text(alphabet=string.ascii_letters + string.digits, min_size=0, max_size=100))
@settings(max_examples=200)
def test_lowercase_output(s):
    result = camel_to_snake(s)
    assert result == result.lower(), f"Output '{result}' is not lowercase for input '{s}'"

try:
    test_lowercase_output()
    print("✓ Lowercase output test PASSED")
except AssertionError as e:
    print(f"✗ Lowercase output test FAILED: {e}")

# Test 3: Dictionary key count preservation
print("\nTest 3: Testing snake_case_keys preserves key count...")
valid_keys = st.text(alphabet=string.ascii_letters, min_size=1, max_size=20)

@given(st.dictionaries(keys=valid_keys, values=st.integers(), min_size=0, max_size=50))
@settings(max_examples=200)
def test_dict_size_preserved(d):
    result = snake_case_keys(d)
    # This might fail if two different keys map to the same snake_case
    # which is actually a bug/limitation
    assert len(result) <= len(d), f"Result has more keys than input!"
    
test_dict_size_preserved()
print("✓ Dictionary size test completed")

# Test 4: Testing for potential collision bug
print("\nTest 4: Looking for key collision scenarios...")
@given(st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10), 
                min_size=2, max_size=5, unique=True))
@settings(max_examples=500)
def test_find_collisions(keys):
    # Create a dict with these keys
    d = {k: i for i, k in enumerate(keys)}
    result = snake_case_keys(d)
    
    # Check if we lost any keys due to collision
    if len(result) < len(d):
        # Found a collision!
        transformed = {k: camel_to_snake(k) for k in keys}
        colliding_keys = []
        for k1 in keys:
            for k2 in keys:
                if k1 != k2 and camel_to_snake(k1) == camel_to_snake(k2):
                    colliding_keys.append((k1, k2, camel_to_snake(k1)))
        
        if colliding_keys:
            print(f"\n  Found collision: {colliding_keys[0]}")
            raise AssertionError(f"Key collision detected: {colliding_keys[0][0]} and {colliding_keys[0][1]} both map to '{colliding_keys[0][2]}'")

try:
    test_find_collisions()
    print("✓ No unexpected collisions found")
except AssertionError as e:
    print(f"⚠ Collision scenario found (this may be expected): {e}")

print("\n" + "="*60)
print("Testing complete!")