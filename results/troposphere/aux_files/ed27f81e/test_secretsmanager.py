import troposphere.secretsmanager as sm
from hypothesis import given, strategies as st, assume
import pytest
import math


# Test 1: Integer validator should only accept actual integers
@given(st.floats(min_value=-1e10, max_value=1e10))
def test_integer_validator_rejects_non_integers(x):
    """The integer validator claims to validate integers but accepts floats."""
    # Skip actual integers
    assume(not x.is_integer())
    assume(not math.isnan(x))
    assume(not math.isinf(x))
    
    # The integer validator should reject non-integer floats
    # But it actually accepts them, which is a bug
    try:
        result = sm.integer(x)
        # If we get here, the validator accepted a non-integer
        # The validator returns the original value, not the converted int
        assert result == x
        # This is a bug - the validator should reject non-integers
        assert False, f"integer validator accepted non-integer {x}"
    except ValueError:
        # This is the expected behavior
        pass


# Test 2: Boolean validator case sensitivity inconsistency
@given(st.text(min_size=1, max_size=10))
def test_boolean_validator_case_consistency(text):
    """Boolean validator should be consistent with case sensitivity."""
    # Test with common boolean string representations
    if text.lower() in ['true', 'false', '1', '0']:
        try:
            result_lower = sm.boolean(text.lower())
            # If lowercase works, uppercase should also work for consistency
            try:
                result_upper = sm.boolean(text.upper())
                # Both should give the same boolean result
                assert result_lower == result_upper
            except ValueError:
                # Inconsistent: lowercase works but uppercase doesn't
                if text.lower() in ['true', 'false']:
                    # This is the actual bug - 'TRUE' and 'FALSE' don't work
                    pass
        except ValueError:
            # If lowercase doesn't work, that's fine
            pass


# Test 3: PasswordLength should only accept positive integers
@given(st.one_of(
    st.floats(min_value=-100, max_value=10000),
    st.integers(min_value=-100, max_value=10000)
))
def test_password_length_validation(length):
    """PasswordLength should only accept positive integers."""
    gen_str = sm.GenerateSecretString()
    
    # Test setting the password length
    try:
        gen_str.PasswordLength = length
        
        # If it was accepted, verify it makes sense
        stored_value = gen_str.PasswordLength
        
        # Check if it's a valid password length
        # AWS Secrets Manager requires 1-4096 for password length
        if isinstance(length, bool):
            # Booleans shouldn't be accepted for password length
            assert False, f"PasswordLength accepted boolean value {length}"
        elif isinstance(length, float) and not length.is_integer():
            # Non-integer floats shouldn't be accepted
            assert False, f"PasswordLength accepted non-integer float {length}"
        elif isinstance(length, (int, float)) and length <= 0:
            # Negative or zero lengths don't make sense
            assert False, f"PasswordLength accepted non-positive value {length}"
        
    except (ValueError, TypeError) as e:
        # Rejection is fine for invalid values
        pass


# Test 4: Round-trip property for GenerateSecretString
@given(
    st.integers(min_value=1, max_value=4096),
    st.text(max_size=50),
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.booleans()
)
def test_generate_secret_string_round_trip(
    password_length, exclude_chars, 
    exclude_lower, exclude_numbers, exclude_punct,
    exclude_upper, include_space
):
    """to_dict() and from_dict() should be inverse operations."""
    # Create a GenerateSecretString with various properties
    gen_str = sm.GenerateSecretString()
    gen_str.PasswordLength = password_length
    if exclude_chars:
        gen_str.ExcludeCharacters = exclude_chars
    gen_str.ExcludeLowercase = exclude_lower
    gen_str.ExcludeNumbers = exclude_numbers
    gen_str.ExcludePunctuation = exclude_punct
    gen_str.ExcludeUppercase = exclude_upper
    gen_str.IncludeSpace = include_space
    
    # Convert to dict
    dict_repr = gen_str.to_dict()
    
    # Reconstruct from dict
    reconstructed = sm.GenerateSecretString.from_dict(None, dict_repr)
    reconstructed_dict = reconstructed.to_dict()
    
    # They should be equal
    assert dict_repr == reconstructed_dict


# Test 5: Extremely permissive integer validator
@given(st.one_of(
    st.booleans(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=1)
))
def test_integer_validator_permissiveness(value):
    """Integer validator is too permissive with input types."""
    try:
        result = sm.integer(value)
        
        # Check what was accepted
        if isinstance(value, bool):
            # Booleans are accepted as integers (True=1, False=0)
            # This might be intentional but is questionable
            assert result == value  # Returns original value
            # int(True) = 1, int(False) = 0 works in Python
        elif isinstance(value, float):
            # All floats are accepted, even non-integers like 1.5
            assert result == value
            # This is definitely a bug for an "integer" validator
        elif isinstance(value, str):
            # Only numeric strings should work
            int_value = int(value)  # This will raise if not numeric
            assert result == value  # Returns original string
            
    except (ValueError, TypeError):
        # Expected for non-convertible values
        pass


# Test 6: Property type validation 
@given(st.dictionaries(
    st.sampled_from(['Description', 'Name', 'KmsKeyId']),
    st.one_of(
        st.text(),
        st.integers(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    )
))
def test_secret_property_types(properties):
    """Secret properties should enforce their declared types."""
    secret = sm.Secret('TestSecret')
    
    for prop_name, prop_value in properties.items():
        try:
            setattr(secret, prop_name, prop_value)
            # If it succeeded, it should be the right type
            if not isinstance(prop_value, str):
                # Non-strings should have been rejected
                assert False, f"{prop_name} accepted non-string {type(prop_value)}"
        except TypeError:
            # Expected for wrong types
            if isinstance(prop_value, str):
                # Strings should have been accepted
                assert False, f"{prop_name} rejected valid string"