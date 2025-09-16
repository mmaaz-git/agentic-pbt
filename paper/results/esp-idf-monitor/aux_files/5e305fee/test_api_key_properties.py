"""Property-based tests for rest_framework_api_key.migrations"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/djangorestframework-api-key_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
import pytest


# Test 1: Round-trip property for concatenate/split
@given(
    left=st.text(min_size=1).filter(lambda x: '.' not in x),
    right=st.text(min_size=1)
)
def test_concatenate_split_round_trip(left, right):
    """Test that split(concatenate(left, right)) returns (left, right)"""
    from rest_framework_api_key.crypto import concatenate, split
    
    concatenated = concatenate(left, right)
    result_left, result_right = split(concatenated)
    
    assert result_left == left
    assert result_right == right


# Test 2: Multiple dots in concatenated string
@given(
    left=st.text(min_size=1).filter(lambda x: '.' not in x),
    middle=st.text(min_size=1).filter(lambda x: '.' not in x),
    right=st.text(min_size=1)
)
def test_concatenate_split_with_multiple_dots(left, middle, right):
    """Test behavior when the right part contains dots"""
    from rest_framework_api_key.crypto import concatenate, split
    
    # Create a string with dots in the right part
    right_with_dot = "{}.{}".format(middle, right)
    concatenated = concatenate(left, right_with_dot)
    
    # Split should only split on the FIRST dot
    result_left, result_right = split(concatenated)
    
    assert result_left == left
    assert result_right == right_with_dot


# Test 3: Migration partition behavior with edge cases
@given(api_key_id=st.text(min_size=1))
def test_migration_partition_behavior(api_key_id):
    """Test the partition logic used in migration 0004"""
    # This simulates the logic from populate_prefix_hashed_key
    prefix, _, hashed_key = api_key_id.partition(".")
    
    if "." not in api_key_id:
        # When there's no dot, prefix gets everything, hashed_key is empty
        assert prefix == api_key_id
        assert hashed_key == ""
    else:
        # When there's a dot, we get a split
        assert len(prefix) >= 0  # prefix could be empty if id starts with "."
        assert api_key_id == f"{prefix}.{hashed_key}" if hashed_key else prefix


# Test 4: Empty string handling in split
@given(empty_side=st.sampled_from(["left", "right", "both"]))
def test_split_with_empty_parts(empty_side):
    """Test split behavior with empty strings on either side of the dot"""
    from rest_framework_api_key.crypto import split
    
    if empty_side == "left":
        concatenated = ".nonempty"
        left, right = split(concatenated)
        assert left == ""
        assert right == "nonempty"
    elif empty_side == "right":
        concatenated = "nonempty."
        left, right = split(concatenated)
        assert left == "nonempty"
        assert right == ""
    else:  # both
        concatenated = "."
        left, right = split(concatenated)
        assert left == ""
        assert right == ""


# Test 5: No dot in string for split function
@given(text=st.text(min_size=1).filter(lambda x: '.' not in x))
def test_split_without_dot(text):
    """Test split behavior when there's no dot in the input"""
    from rest_framework_api_key.crypto import split
    
    left, right = split(text)
    assert left == text
    assert right == ""


# Test 6: KeyGenerator properties
@given(
    prefix_length=st.integers(min_value=1, max_value=20),
    secret_key_length=st.integers(min_value=1, max_value=50)
)
def test_key_generator_lengths(prefix_length, secret_key_length):
    """Test that KeyGenerator produces keys with correct lengths"""
    from rest_framework_api_key.crypto import KeyGenerator
    
    generator = KeyGenerator(prefix_length=prefix_length, secret_key_length=secret_key_length)
    key, prefix, hashed_key = generator.generate()
    
    # Check the structure
    assert "." in key
    key_prefix, _, key_secret = key.partition(".")
    
    # Check lengths
    assert len(prefix) == prefix_length
    assert len(key_prefix) == prefix_length
    assert prefix == key_prefix
    assert len(key_secret) == secret_key_length
    
    # Check that hashed_key is properly formatted
    assert hashed_key.startswith("sha512$$")


# Test 7: Hash verification round-trip
@given(st.text(min_size=1, max_size=100))
def test_hash_verification_round_trip(secret):
    """Test that hashing and verification work correctly"""
    from rest_framework_api_key.crypto import KeyGenerator
    
    generator = KeyGenerator()
    hashed = generator.hash(secret)
    
    # Verification should succeed for the same secret
    assert generator.verify(secret, hashed)
    
    # Verification should fail for a different secret
    assert not generator.verify(secret + "x", hashed)