"""More aggressive property-based tests to find edge cases"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/djangorestframework-api-key_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest


# Test for Unicode and special characters
@given(
    left=st.text(min_size=1, alphabet=st.characters(min_codepoint=0, max_codepoint=0x10ffff)).filter(lambda x: '.' not in x),
    right=st.text(min_size=1, alphabet=st.characters(min_codepoint=0, max_codepoint=0x10ffff))
)
@settings(max_examples=500)
def test_unicode_in_concatenate_split(left, right):
    """Test that concatenate/split handles Unicode correctly"""
    from rest_framework_api_key.crypto import concatenate, split
    
    concatenated = concatenate(left, right)
    result_left, result_right = split(concatenated)
    
    assert result_left == left
    assert result_right == right


# Test migration behavior with malformed IDs
@given(st.lists(st.text(min_size=0), min_size=2, max_size=10))
def test_migration_with_multiple_dots(parts):
    """Test migration behavior when ID has multiple dots"""
    api_key_id = ".".join(parts)
    
    # Simulate the migration logic
    prefix, _, hashed_key = api_key_id.partition(".")
    
    # After partition, we should be able to reconstruct the original
    if "." in api_key_id:
        reconstructed = f"{prefix}.{hashed_key}"
        assert reconstructed == api_key_id
    else:
        assert prefix == api_key_id
        assert hashed_key == ""


# Test with empty strings and None-like values
@given(
    use_empty_left=st.booleans(),
    use_empty_right=st.booleans()
)
def test_empty_string_edge_cases(use_empty_left, use_empty_right):
    """Test behavior with empty strings"""
    from rest_framework_api_key.crypto import concatenate, split
    
    left = "" if use_empty_left else "nonempty"
    right = "" if use_empty_right else "nonempty"
    
    # Empty strings should still work
    concatenated = concatenate(left, right)
    result_left, result_right = split(concatenated)
    
    assert result_left == left
    assert result_right == right


# Test extremely long strings
@given(
    left_size=st.integers(min_value=1, max_value=10000),
    right_size=st.integers(min_value=1, max_value=10000)
)
@settings(max_examples=50)
def test_very_long_strings(left_size, right_size):
    """Test with very long strings to check for buffer issues"""
    from rest_framework_api_key.crypto import concatenate, split
    
    left = "a" * left_size
    right = "b" * right_size
    
    concatenated = concatenate(left, right)
    result_left, result_right = split(concatenated)
    
    assert result_left == left
    assert result_right == right
    assert len(result_left) == left_size
    assert len(result_right) == right_size


# Test the actual migration logic more thoroughly
class MockAPIKey:
    """Mock object to simulate Django model in migration"""
    def __init__(self, id_value):
        self.id = id_value
        self.prefix = None
        self.hashed_key = None
        self.saved = False
    
    def save(self):
        self.saved = True


@given(st.text(min_size=0))
def test_migration_populate_prefix_hashed_key_logic(api_key_id):
    """Test the exact logic from the migration"""
    # Create a mock API key
    api_key = MockAPIKey(api_key_id)
    
    # Execute the migration logic
    prefix, _, hashed_key = api_key.id.partition(".")
    api_key.prefix = prefix
    api_key.hashed_key = hashed_key
    
    # Verify the behavior
    if "." not in api_key_id:
        # No dot means everything goes to prefix, hashed_key is empty
        assert api_key.prefix == api_key_id
        assert api_key.hashed_key == ""
    else:
        # With dot, check the split is correct
        expected_prefix = api_key_id.split(".", 1)[0]
        expected_hashed = api_key_id.split(".", 1)[1] if "." in api_key_id else ""
        assert api_key.prefix == expected_prefix
        assert api_key.hashed_key == expected_hashed


# Test what happens with only dots
@given(num_dots=st.integers(min_value=1, max_value=10))
def test_only_dots(num_dots):
    """Test strings that are only dots"""
    from rest_framework_api_key.crypto import split
    
    dot_string = "." * num_dots
    left, right = split(dot_string)
    
    assert left == ""
    if num_dots == 1:
        assert right == ""
    else:
        assert right == "." * (num_dots - 1)


# Test concatenate with dots already in left part (should this be allowed?)
@given(
    st.text(min_size=1).filter(lambda x: '.' in x),
    st.text(min_size=1)
)
def test_concatenate_with_dot_in_left(left_with_dot, right):
    """Test if concatenate allows dots in the left part (potential bug source)"""
    from rest_framework_api_key.crypto import concatenate, split
    
    # Concatenate allows dots in left part, but this breaks the round-trip!
    concatenated = concatenate(left_with_dot, right)
    result_left, result_right = split(concatenated)
    
    # This will fail if left_with_dot contains dots!
    # The split will only take up to the first dot
    if "." in left_with_dot:
        # This is a BUG: round-trip property is violated!
        assert result_left != left_with_dot  # Left will be truncated at first dot
    else:
        assert result_left == left_with_dot