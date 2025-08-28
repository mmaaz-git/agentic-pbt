"""Property-based tests for fire.completion module using Hypothesis."""

import math
from hypothesis import given, strategies as st, assume, settings
import pytest
from fire import completion

# Use more examples for thorough testing
test_settings = settings(max_examples=1000)


# Test 1: _FormatForCommand preserves tokens starting with underscore
@given(st.text(min_size=1))
def test_format_for_command_underscore_preservation(text):
    """Test that tokens starting with '_' are preserved unchanged."""
    if text.startswith('_'):
        result = completion._FormatForCommand(text)
        assert result == text, f"Token starting with _ should be unchanged: {text} != {result}"


# Test 2: _FormatForCommand replaces underscores with hyphens for non-underscore-starting tokens
@given(st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs")), min_size=1))
def test_format_for_command_hyphen_replacement(text):
    """Test that underscores are replaced with hyphens for tokens not starting with '_'."""
    assume(not text.startswith('_'))
    result = completion._FormatForCommand(text)
    expected = text.replace('_', '-')
    assert result == expected, f"Underscores should be replaced with hyphens: {result} != {expected}"


# Test 3: _FormatForCommand handles non-string inputs
@given(st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.booleans()))
def test_format_for_command_non_string_input(value):
    """Test that non-string inputs are converted to strings before processing."""
    result = completion._FormatForCommand(value)
    str_value = str(value)
    expected = str_value if str_value.startswith('_') else str_value.replace('_', '-')
    assert result == expected, f"Non-string should be converted and processed: {result} != {expected}"


# Test 4: _CompletionsFromArgs prefixes all args with '--'
@given(st.lists(st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters=' '), min_size=1), min_size=0, max_size=20))
def test_completions_from_args_prefix(args):
    """Test that all args are prefixed with '--' and underscores replaced with hyphens."""
    result = completion._CompletionsFromArgs(args)
    assert len(result) == len(args), f"Should have same number of completions as args"
    for i, arg in enumerate(args):
        expected = f"--{arg.replace('_', '-')}"
        assert result[i] == expected, f"Arg should be prefixed and formatted: {result[i]} != {expected}"


# Test 5: Completions for lists/tuples returns correct indices
@given(st.lists(st.integers(), min_size=0, max_size=100))
def test_completions_list_indices(lst):
    """Test that Completions for lists returns string indices from 0 to len-1."""
    result = completion.Completions(lst)
    expected = [str(i) for i in range(len(lst))]
    assert result == expected, f"List completions should be indices: {result} != {expected}"


@given(st.tuples(*[st.integers() for _ in range(10)]))  # Tuples of various sizes
def test_completions_tuple_indices(tup):
    """Test that Completions for tuples returns string indices from 0 to len-1."""
    result = completion.Completions(tup)
    expected = [str(i) for i in range(len(tup))]
    assert result == expected, f"Tuple completions should be indices: {result} != {expected}"


# Test 6: Completions for generators returns empty list
@given(st.integers(min_value=0, max_value=100))
def test_completions_generator_empty(n):
    """Test that Completions for generators always returns empty list."""
    def generator():
        for i in range(n):
            yield i
    
    gen = generator()
    result = completion.Completions(gen)
    assert result == [], f"Generator completions should be empty: {result}"


# Test 7: MemberVisible excludes double underscore members
@given(st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='_'), min_size=1).map(lambda x: '__' + x))
def test_member_visible_double_underscore_exclusion(name):
    """Test that members starting with '__' are never visible."""
    # Create a dummy component and member
    component = object()
    member = object()
    
    # Test both verbose=False and verbose=True
    assert not completion.MemberVisible(component, name, member, verbose=False), \
        f"Member starting with __ should not be visible (verbose=False): {name}"
    assert not completion.MemberVisible(component, name, member, verbose=True), \
        f"Member starting with __ should not be visible (verbose=True): {name}"


# Test 8: MemberVisible in verbose mode includes single underscore members
@given(st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters='_'), min_size=1).map(lambda x: '_' + x))
def test_member_visible_single_underscore_verbose(name):
    """Test that members starting with single '_' are visible in verbose mode."""
    # Ensure it's not a double underscore
    assume(not name.startswith('__'))
    
    component = object()
    member = object()
    
    # In verbose mode, single underscore should be visible
    assert completion.MemberVisible(component, name, member, verbose=True), \
        f"Member starting with single _ should be visible in verbose mode: {name}"
    
    # In non-verbose mode, single underscore should not be visible for strings
    assert not completion.MemberVisible(component, name, member, verbose=False), \
        f"Member starting with single _ should not be visible in non-verbose mode: {name}"


# Test 9: _IsOption correctly identifies options
@given(st.text())
def test_is_option_identification(text):
    """Test that _IsOption correctly identifies strings starting with '-'."""
    result = completion._IsOption(text)
    expected = text.startswith('-')
    assert result == expected, f"_IsOption should return {expected} for '{text}'"


# Test 10: Completions handles dict correctly
@given(st.dictionaries(
    st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1, max_size=20),
    st.integers(),
    min_size=0,
    max_size=20
))
def test_completions_dict_keys(d):
    """Test that Completions for dicts returns visible keys formatted correctly."""
    result = completion.Completions(d, verbose=False)
    
    # Filter out keys starting with underscore (not visible in non-verbose mode)
    visible_keys = [k for k in d.keys() if not k.startswith('_')]
    
    # Format keys
    expected = []
    for key in visible_keys:
        formatted = completion._FormatForCommand(key)
        expected.append(formatted)
    
    # Sort both for comparison since dict iteration order might vary
    result_sorted = sorted(result)
    expected_sorted = sorted(expected)
    
    assert result_sorted == expected_sorted, \
        f"Dict completions should be formatted visible keys: {result_sorted} != {expected_sorted}"


# Test 11: Round-trip property for _FormatForCommand
@given(st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1))
def test_format_for_command_idempotent(text):
    """Test that _FormatForCommand is idempotent (applying it twice gives same result as once)."""
    once = completion._FormatForCommand(text)
    twice = completion._FormatForCommand(once)
    assert once == twice, f"_FormatForCommand should be idempotent: {once} != {twice}"


# Test 12: Completions preserves list order
@given(st.lists(st.integers(), min_size=1, max_size=50))
def test_completions_list_order_preserved(lst):
    """Test that Completions for lists preserves index order."""
    result = completion.Completions(lst)
    
    # Check that indices are in ascending order
    for i in range(len(result)):
        assert result[i] == str(i), f"Index {i} should map to string '{i}', got '{result[i]}'"


# Test 13: VisibleMembers respects verbose flag
@given(st.dictionaries(
    st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1, max_size=20),
    st.integers(),
    min_size=5,
    max_size=20
).filter(lambda d: any(k.startswith('_') and not k.startswith('__') for k in d.keys())))
def test_visible_members_verbose_flag(d):
    """Test that VisibleMembers includes/excludes underscore members based on verbose flag."""
    # Get visible members without verbose
    members_normal = completion.VisibleMembers(d, verbose=False)
    normal_names = {name for name, _ in members_normal}
    
    # Get visible members with verbose
    members_verbose = completion.VisibleMembers(d, verbose=True)
    verbose_names = {name for name, _ in members_verbose}
    
    # Check that verbose includes all normal members
    assert normal_names.issubset(verbose_names), \
        "Verbose mode should include all normal members"
    
    # Check that no double underscore members are in either
    for name in verbose_names:
        assert not name.startswith('__'), \
            f"Double underscore member should never be visible: {name}"
    
    # Check that single underscore members are only in verbose
    single_underscore_keys = {k for k in d.keys() if k.startswith('_') and not k.startswith('__')}
    for key in single_underscore_keys:
        assert key not in normal_names, \
            f"Single underscore member should not be in normal mode: {key}"
        assert key in verbose_names, \
            f"Single underscore member should be in verbose mode: {key}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])