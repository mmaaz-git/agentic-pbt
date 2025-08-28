"""Property-based tests for isort.sorting module."""

import re
from typing import List, Any
from hypothesis import given, strategies as st, assume, settings
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort import sorting
from isort.settings import Config


# Test 1: Natural sorting preserves elements (set invariant)
@given(st.lists(st.text(min_size=1)))
def test_naturally_preserves_elements(strings):
    """naturally() should preserve all elements - no additions or removals."""
    result = sorting.naturally(strings)
    # Same multiset of elements (allowing duplicates)
    assert sorted(result) == sorted(strings), f"Elements changed: input={strings}, result={result}"


# Test 2: Natural sorting with reverse parameter
@given(st.lists(st.text(min_size=1)))
def test_naturally_reverse(strings):
    """naturally() with reverse=True should produce reversed order."""
    forward = sorting.naturally(strings)
    backward = sorting.naturally(strings, reverse=True)
    # Reversed list should match
    assert list(reversed(forward)) == backward, f"Reverse failed: forward={forward}, backward={backward}"


# Test 3: Natural sorting handles numeric ordering correctly
@given(
    prefix=st.text(alphabet=st.characters(blacklist_categories=("Nd",)), min_size=0, max_size=5),
    nums=st.lists(st.integers(min_value=0, max_value=1000), min_size=2, max_size=10, unique=True)
)
def test_naturally_numeric_ordering(prefix, nums):
    """Natural sorting should order numeric portions numerically, not lexicographically."""
    # Create strings with the same prefix but different numbers
    strings = [f"{prefix}{num}" for num in nums]
    result = sorting.naturally(strings)
    
    # Extract numbers from sorted result and verify they're in numeric order
    result_nums = []
    for s in result:
        if s.startswith(prefix):
            num_str = s[len(prefix):]
            if num_str.isdigit():
                result_nums.append(int(num_str))
    
    # The numbers should be sorted numerically
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
    assume(s.isdigit())  # Extra safety check
    result = sorting._atoi(s)
    assert result == int(s), f"Digit conversion failed: {s} -> {result} (expected {int(s)})"


# Test 5: _natural_keys idempotence and structure
@given(st.text())
def test_natural_keys_structure(text):
    """_natural_keys should split text by digits correctly."""
    result = sorting._natural_keys(text)
    # Result should be a list
    assert isinstance(result, list)
    
    # Every element should be either a string or an int
    for elem in result:
        assert isinstance(elem, (str, int)), f"Unexpected type in natural_keys result: {type(elem)}"
    
    # Integers should only appear where there were digit sequences
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
    # Only test strings without any digits
    strings = [s for s in strings if not any(c.isdigit() for c in s)]
    
    if strings:  # Only test if we have non-empty list after filtering
        natural_sorted = sorting.naturally(strings)
        standard_sorted = sorted(strings)
        assert natural_sorted == standard_sorted, f"Sorts differ without numbers: {strings}"


# Test 7: module_key case sensitivity property
@given(
    module_name=st.text(min_size=1, max_size=20),
    ignore_case=st.booleans()
)
def test_module_key_case_sensitivity(module_name, ignore_case):
    """module_key with ignore_case should treat upper/lower case the same."""
    config = Config(case_sensitive=not ignore_case)
    
    # Skip relative imports for this test
    assume(not module_name.startswith('.'))
    
    if ignore_case and module_name:
        key_lower = sorting.module_key(module_name.lower(), config, ignore_case=ignore_case)
        key_upper = sorting.module_key(module_name.upper(), config, ignore_case=ignore_case)
        # Keys should be the same when ignoring case
        assert key_lower == key_upper, f"Case ignored but keys differ: {module_name}"


# Test 8: module_key relative import handling
@given(
    dots=st.integers(min_value=1, max_value=5),
    module_part=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu")), min_size=0, max_size=10)
)
def test_module_key_relative_imports(dots, module_part):
    """module_key should handle relative imports with dots."""
    module_name = "." * dots + module_part
    config = Config(reverse_relative=False)
    
    key = sorting.module_key(module_name, config)
    # Key should be generated without error
    assert isinstance(key, str)
    
    # With reverse_relative=True, behavior changes
    config_rev = Config(reverse_relative=True)
    key_rev = sorting.module_key(module_name, config_rev)
    assert isinstance(key_rev, str)


# Test 9: Natural sorting edge cases
@given(st.lists(st.one_of(
    st.just(""),
    st.text(alphabet="0123456789", min_size=1, max_size=10),
    st.text(alphabet=st.characters(blacklist_categories=("Nd",)), min_size=1, max_size=5)
)))
def test_naturally_edge_cases(strings):
    """Natural sorting should handle edge cases like empty strings and pure numbers."""
    result = sorting.naturally(strings)
    # Should not crash and should preserve all elements
    assert len(result) == len(strings)
    assert set(result) == set(strings)


# Test 10: Sort function delegation
@given(st.lists(st.text(min_size=1)))
def test_sort_function_delegation(strings):
    """sort() should delegate to config.sorting_function."""
    # Create a config with naturally as the sorting function
    config = Config(sorting_function=sorting.naturally)
    
    result = sorting.sort(config, strings)
    expected = sorting.naturally(strings)
    
    assert result == expected, f"Sort delegation failed: {result} != {expected}"


if __name__ == "__main__":
    import pytest
    import sys
    
    # Run the tests
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))