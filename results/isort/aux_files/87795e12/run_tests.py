#!/usr/bin/env python3
"""Run the property-based tests for isort.sorting."""

import sys
import traceback
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from isort import sorting
from isort.settings import Config


def run_test(test_func, test_name):
    """Run a single test and report results."""
    print(f"\nTesting: {test_name}")
    print("-" * 50)
    try:
        test_func()
        print(f"✓ {test_name} PASSED")
        return True
    except AssertionError as e:
        print(f"✗ {test_name} FAILED")
        print(f"  Assertion Error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ {test_name} ERRORED")
        print(f"  Error: {e}")
        traceback.print_exc()
        return False


# Test 1: Natural sorting preserves elements
@given(st.lists(st.text(min_size=1)))
def test_naturally_preserves_elements(strings):
    """naturally() should preserve all elements - no additions or removals."""
    result = sorting.naturally(strings)
    assert sorted(result) == sorted(strings), f"Elements changed: input={strings}, result={result}"


# Test 2: Natural sorting with reverse parameter
@given(st.lists(st.text(min_size=1)))
def test_naturally_reverse(strings):
    """naturally() with reverse=True should produce reversed order."""
    forward = sorting.naturally(strings)
    backward = sorting.naturally(strings, reverse=True)
    assert list(reversed(forward)) == backward, f"Reverse failed: forward={forward}, backward={backward}"


# Test 3: Natural sorting handles numeric ordering correctly
@given(
    prefix=st.text(alphabet=st.characters(blacklist_categories=("Nd",)), min_size=0, max_size=5),
    nums=st.lists(st.integers(min_value=0, max_value=1000), min_size=2, max_size=10, unique=True)
)
def test_naturally_numeric_ordering(prefix, nums):
    """Natural sorting should order numeric portions numerically, not lexicographically."""
    strings = [f"{prefix}{num}" for num in nums]
    result = sorting.naturally(strings)
    
    result_nums = []
    for s in result:
        if s.startswith(prefix):
            num_str = s[len(prefix):]
            if num_str.isdigit():
                result_nums.append(int(num_str))
    
    assert result_nums == sorted(result_nums), f"Numbers not naturally sorted: {strings} -> {result}"


# Test 4: _atoi function properties
@given(st.text())
def test_atoi_preserves_non_digits(s):
    """_atoi should return the original string if it's not all digits."""
    result = sorting._atoi(s)
    if not s.isdigit():
        assert result == s, f"Non-digit string changed: {s} -> {result}"


@given(st.text(alphabet=st.characters(whitelist_categories=("Nd",)), min_size=1))
def test_atoi_converts_digits(s):
    """_atoi should convert digit strings to integers."""
    assume(s.isdigit())
    result = sorting._atoi(s)
    assert result == int(s), f"Digit conversion failed: {s} -> {result}"


# Test 5: _natural_keys structure
@given(st.text())
def test_natural_keys_structure(text):
    """_natural_keys should split text by digits correctly."""
    result = sorting._natural_keys(text)
    assert isinstance(result, list)
    
    for elem in result:
        assert isinstance(elem, (str, int)), f"Unexpected type in natural_keys result: {type(elem)}"
    
    reconstructed = ""
    for elem in result:
        if isinstance(elem, int):
            reconstructed += str(elem)
        else:
            reconstructed += elem
    assert reconstructed == text, f"Reconstruction failed: {text} -> {result} -> {reconstructed}"


# Test 6: Natural sorting comparison with standard sorting  
@given(st.lists(st.text(alphabet=st.characters(blacklist_categories=("Nd",)), min_size=1, max_size=5)))
def test_naturally_without_numbers_matches_standard_sort(strings):
    """When there are no numbers, natural sort should match standard sort."""
    strings = [s for s in strings if not any(c.isdigit() for c in s)]
    
    if strings:
        natural_sorted = sorting.naturally(strings)
        standard_sorted = sorted(strings)
        assert natural_sorted == standard_sorted, f"Sorts differ without numbers: {strings}"


# Test 7: module_key case sensitivity
@given(
    module_name=st.text(min_size=1, max_size=20),
    ignore_case=st.booleans()
)
def test_module_key_case_sensitivity(module_name, ignore_case):
    """module_key with ignore_case should treat upper/lower case the same."""
    config = Config(case_sensitive=not ignore_case)
    
    assume(not module_name.startswith('.'))
    
    if ignore_case and module_name:
        key_lower = sorting.module_key(module_name.lower(), config, ignore_case=ignore_case)
        key_upper = sorting.module_key(module_name.upper(), config, ignore_case=ignore_case)
        assert key_lower == key_upper, f"Case ignored but keys differ: {module_name}"


# Test 8: Edge cases
@given(st.lists(st.one_of(
    st.just(""),
    st.text(alphabet="0123456789", min_size=1, max_size=10),
    st.text(alphabet=st.characters(blacklist_categories=("Nd",)), min_size=1, max_size=5)
)))
def test_naturally_edge_cases(strings):
    """Natural sorting should handle edge cases like empty strings and pure numbers."""
    result = sorting.naturally(strings)
    assert len(result) == len(strings)
    assert set(result) == set(strings)


# Main execution
if __name__ == "__main__":
    print("=" * 60)
    print("Running Property-Based Tests for isort.sorting")
    print("=" * 60)
    
    tests = [
        (test_naturally_preserves_elements, "Natural sorting preserves elements"),
        (test_naturally_reverse, "Natural sorting reverse parameter"),
        (test_naturally_numeric_ordering, "Natural sorting numeric ordering"),
        (test_atoi_preserves_non_digits, "_atoi preserves non-digits"),
        (test_atoi_converts_digits, "_atoi converts digits"),
        (test_natural_keys_structure, "_natural_keys structure"),
        (test_naturally_without_numbers_matches_standard_sort, "Natural sort matches standard sort without numbers"),
        (test_module_key_case_sensitivity, "module_key case sensitivity"),
        (test_naturally_edge_cases, "Natural sorting edge cases"),
    ]
    
    passed = 0
    failed = 0
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    sys.exit(0 if failed == 0 else 1)