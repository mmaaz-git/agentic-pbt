import os
import sys

# Add the virtual environment's site-packages to the path FIRST
sys.path.insert(0, '/root/hypothesis-llm/envs/djangorestframework-api-key_env/lib/python3.13/site-packages')

import django
from django.conf import settings

# Configure Django settings before importing any models
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'rest_framework_api_key',
        ],
        USE_TZ=True,
        SECRET_KEY='test-secret-key',
    )
    django.setup()

import hashlib
from hypothesis import given, strategies as st, assume, settings as hypo_settings
import pytest

from rest_framework_api_key.crypto import concatenate, split, Sha512ApiKeyHasher, KeyGenerator


# Test 1: concatenate/split round-trip property
@given(
    left=st.text(min_size=1, max_size=100).filter(lambda x: '.' not in x),
    right=st.text(min_size=1, max_size=100)
)
def test_concatenate_split_round_trip(left, right):
    """split(concatenate(left, right)) should return (left, right)"""
    concatenated = concatenate(left, right)
    result_left, result_right = split(concatenated)
    assert result_left == left
    assert result_right == right


# Test 2: KeyGenerator hash verification property
@given(
    prefix_length=st.integers(min_value=1, max_value=50),
    secret_key_length=st.integers(min_value=1, max_value=100)
)
def test_key_generator_verify_generated_key(prefix_length, secret_key_length):
    """A generated key should always be verifiable with its hash"""
    generator = KeyGenerator(prefix_length=prefix_length, secret_key_length=secret_key_length)
    key, prefix, hashed_key = generator.generate()
    
    # The generated key should verify against its hash
    assert generator.verify(key, hashed_key) == True
    
    # The key should have the expected format
    assert '.' in key
    left, right = split(key)
    assert len(left) == prefix_length
    assert len(right) == secret_key_length
    assert left == prefix


# Test 3: Hash determinism
@given(
    password=st.text(min_size=1, max_size=200)
)
def test_sha512_hasher_determinism(password):
    """Hashing the same password twice should produce the same result"""
    hasher = Sha512ApiKeyHasher()
    hash1 = hasher.encode(password, "")
    hash2 = hasher.encode(password, "")
    assert hash1 == hash2
    
    # Also verify that the hash verifies correctly
    assert hasher.verify(password, hash1) == True


# Test 4: Invalid salt should raise ValueError
@given(
    password=st.text(min_size=1, max_size=200),
    salt=st.text(min_size=1, max_size=50)
)
def test_sha512_hasher_rejects_salt(password, salt):
    """Sha512ApiKeyHasher should reject any non-empty salt"""
    hasher = Sha512ApiKeyHasher()
    with pytest.raises(ValueError, match="salt is unnecessary"):
        hasher.encode(password, salt)


# Test 5: Generated keys have correct structure
@given(
    prefix_length=st.integers(min_value=1, max_value=50),
    secret_key_length=st.integers(min_value=1, max_value=100)
)
def test_key_structure_invariants(prefix_length, secret_key_length):
    """Generated keys should maintain structural invariants"""
    generator = KeyGenerator(prefix_length=prefix_length, secret_key_length=secret_key_length)
    key, prefix, hashed_key = generator.generate()
    
    # Check hashed key format
    assert hashed_key.startswith("sha512$$")
    
    # Check that the hash part is hex
    hash_part = hashed_key.split("$$")[1]
    assert all(c in '0123456789abcdef' for c in hash_part)
    
    # SHA-512 produces 128 hex characters (512 bits / 4 bits per hex char)
    assert len(hash_part) == 128


# Test 6: Different keys produce different hashes
@given(
    st.lists(st.text(min_size=1, max_size=50), min_size=2, max_size=10, unique=True)
)
def test_hash_uniqueness(passwords):
    """Different passwords should produce different hashes"""
    hasher = Sha512ApiKeyHasher()
    hashes = [hasher.encode(pwd, "") for pwd in passwords]
    # All hashes should be unique for unique inputs
    assert len(set(hashes)) == len(passwords)


# Test 7: Hash format consistency
@given(
    password=st.text(min_size=1, max_size=200)
)
def test_hash_format_consistency(password):
    """Hash should always have consistent format"""
    hasher = Sha512ApiKeyHasher()
    hashed = hasher.encode(password, "")
    
    # Should have exactly one $$
    assert hashed.count("$$") == 1
    
    # Should start with algorithm name
    assert hashed.startswith("sha512$$")
    
    # Hash part should be valid hex
    parts = hashed.split("$$")
    assert len(parts) == 2
    assert parts[0] == "sha512"
    assert len(parts[1]) == 128  # SHA-512 produces 128 hex chars


# Test 8: Concatenate with dots in the right part
@given(
    left=st.text(min_size=1, max_size=100).filter(lambda x: '.' not in x),
    right=st.text(min_size=1, max_size=100)
)
def test_concatenate_split_with_dots_in_right(left, right):
    """split should handle dots in the right part correctly"""
    concatenated = concatenate(left, right)
    result_left, result_right = split(concatenated)
    
    # left should be everything before the first dot
    # right should be everything after the first dot (including other dots)
    assert result_left == left
    assert result_right == right
    
    # Verify the concatenated string structure
    assert concatenated == f"{left}.{right}"


# Test 9: Empty string edge cases
@given(
    use_empty_left=st.booleans(),
    use_empty_right=st.booleans(),
    left=st.text(min_size=0, max_size=100).filter(lambda x: '.' not in x),
    right=st.text(min_size=0, max_size=100)
)
def test_concatenate_split_empty_strings(use_empty_left, use_empty_right, left, right):
    """Test concatenate/split with empty strings"""
    if use_empty_left:
        left = ""
    if use_empty_right:
        right = ""
    
    concatenated = concatenate(left, right)
    result_left, result_right = split(concatenated)
    
    assert result_left == left
    assert result_right == right


# Test 10: Verify returns False for incorrect keys
@given(
    prefix_length=st.integers(min_value=1, max_value=20),
    secret_key_length=st.integers(min_value=1, max_value=50),
    wrong_key=st.text(min_size=1, max_size=100)
)
def test_verify_rejects_wrong_keys(prefix_length, secret_key_length, wrong_key):
    """verify() should return False for incorrect keys"""
    generator = KeyGenerator(prefix_length=prefix_length, secret_key_length=secret_key_length)
    key, prefix, hashed_key = generator.generate()
    
    # Make sure wrong_key is actually different from the real key
    assume(wrong_key != key)
    
    # Verification should fail for wrong key
    assert generator.verify(wrong_key, hashed_key) == False


if __name__ == "__main__":
    # Run all the tests
    import sys
    
    test_functions = [
        test_concatenate_split_round_trip,
        test_key_generator_verify_generated_key,
        test_sha512_hasher_determinism,
        test_sha512_hasher_rejects_salt,
        test_key_structure_invariants,
        test_hash_uniqueness,
        test_hash_format_consistency,
        test_concatenate_split_with_dots_in_right,
        test_concatenate_split_empty_strings,
        test_verify_rejects_wrong_keys,
    ]
    
    failed_tests = []
    
    for test_func in test_functions:
        print(f"Running {test_func.__name__}...")
        try:
            test_func()
            print(f"  ✓ Passed")
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            failed_tests.append((test_func.__name__, e))
    
    if failed_tests:
        print(f"\n{len(failed_tests)} test(s) failed:")
        for name, error in failed_tests:
            print(f"  - {name}: {error}")
        sys.exit(1)
    else:
        print(f"\nAll {len(test_functions)} tests passed!")
        sys.exit(0)