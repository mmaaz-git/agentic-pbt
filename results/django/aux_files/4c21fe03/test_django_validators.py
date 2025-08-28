"""Property-based tests for django.core.validators."""

from hypothesis import given, strategies as st, assume, settings, example
import django
from django.conf import settings as django_settings
from django.core.exceptions import ValidationError

# Configure Django settings
if not django_settings.configured:
    django_settings.configure(
        SECRET_KEY='test-secret-key',
        SECRET_KEY_FALLBACKS=[]
    )

import django.core.validators as validators


# Test MaxValueValidator and MinValueValidator consistency
@given(
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False),
    st.floats(allow_nan=False, allow_infinity=False)
)
@settings(max_examples=1000)
def test_min_max_validator_consistency(min_val, max_val, test_val):
    """Test that MinValueValidator and MaxValueValidator are consistent."""
    assume(min_val < max_val)
    
    min_validator = validators.MinValueValidator(min_val)
    max_validator = validators.MaxValueValidator(max_val)
    
    if test_val < min_val:
        # Should fail min validation
        try:
            min_validator(test_val)
            assert False, f"MinValueValidator should reject {test_val} < {min_val}"
        except ValidationError:
            pass  # Expected
    
    if test_val > max_val:
        # Should fail max validation
        try:
            max_validator(test_val)
            assert False, f"MaxValueValidator should reject {test_val} > {max_val}"
        except ValidationError:
            pass  # Expected
    
    if min_val <= test_val <= max_val:
        # Should pass both validations
        min_validator(test_val)  # Should not raise
        max_validator(test_val)  # Should not raise


# Test MaxLengthValidator and MinLengthValidator
@given(
    st.integers(min_value=0, max_value=1000),
    st.integers(min_value=0, max_value=1000),
    st.text(max_size=2000)
)
@settings(max_examples=1000)
def test_length_validators(min_len, max_len, text):
    """Test length validators with various strings."""
    assume(min_len <= max_len)
    
    min_validator = validators.MinLengthValidator(min_len)
    max_validator = validators.MaxLengthValidator(max_len)
    
    text_len = len(text)
    
    if text_len < min_len:
        try:
            min_validator(text)
            assert False, f"MinLengthValidator should reject len={text_len} < {min_len}"
        except ValidationError:
            pass
    
    if text_len > max_len:
        try:
            max_validator(text)
            assert False, f"MaxLengthValidator should reject len={text_len} > {max_len}"
        except ValidationError:
            pass
    
    if min_len <= text_len <= max_len:
        min_validator(text)  # Should not raise
        max_validator(text)  # Should not raise


# Test DecimalValidator with edge cases
@given(
    st.integers(min_value=1, max_value=20),
    st.integers(min_value=0, max_value=20),
    st.decimals(allow_nan=False, allow_infinity=False)
)
@settings(max_examples=1000)
def test_decimal_validator(max_digits, decimal_places, value):
    """Test DecimalValidator with various decimal values."""
    assume(decimal_places <= max_digits)
    
    validator = validators.DecimalValidator(max_digits, decimal_places)
    
    # Convert to string to analyze
    import decimal
    dec_value = decimal.Decimal(str(value))
    
    # Get the actual digits and decimal places
    sign, digits, exponent = dec_value.as_tuple()
    
    # Calculate actual number of digits
    num_digits = len(digits)
    num_decimals = max(0, -exponent) if exponent < 0 else 0
    num_integers = num_digits - num_decimals
    
    try:
        validator(value)
        # If it passed, verify it should have passed
        assert num_digits <= max_digits, f"Validator accepted {value} with {num_digits} digits > {max_digits}"
        assert num_decimals <= decimal_places, f"Validator accepted {value} with {num_decimals} decimal places > {decimal_places}"
    except ValidationError:
        # If it failed, verify it should have failed
        # (Either too many total digits or too many decimal places)
        pass


# Test EmailValidator with various inputs
@given(st.text(max_size=200))
@settings(max_examples=1000)
def test_email_validator_doesnt_crash(text):
    """Test that EmailValidator handles any string input without crashing."""
    validator = validators.EmailValidator()
    
    try:
        validator(text)
        # If it passes, it should look like a valid email
        assert '@' in text, f"EmailValidator accepted '{text}' without @"
    except ValidationError:
        # Expected for invalid emails
        pass


# Test URLValidator with edge cases
@given(st.text(max_size=200))
@settings(max_examples=1000)
def test_url_validator_doesnt_crash(text):
    """Test that URLValidator handles any string input gracefully."""
    validator = validators.URLValidator()
    
    try:
        validator(text)
        # If it passes, should have basic URL structure
        assert '://' in text or text.startswith('//'), f"URLValidator accepted '{text}' without scheme"
    except ValidationError:
        # Expected for invalid URLs
        pass


# Test ProhibitNullCharactersValidator
@given(st.text())
@settings(max_examples=1000)
def test_null_char_validator(text):
    """Test ProhibitNullCharactersValidator."""
    validator = validators.ProhibitNullCharactersValidator()
    
    if '\x00' in text:
        # Should reject strings with null chars
        try:
            validator(text)
            assert False, "Should reject string with null character"
        except ValidationError:
            pass  # Expected
    else:
        # Should accept strings without null chars
        validator(text)  # Should not raise


# Test RegexValidator with inverse_match
@given(
    st.text(alphabet=st.characters(categories=['L', 'N']), min_size=1, max_size=50),
    st.text(max_size=100),
    st.booleans()
)
@settings(max_examples=500)
def test_regex_validator_inverse(pattern, test_string, inverse):
    """Test RegexValidator with inverse_match option."""
    import re
    
    try:
        validator = validators.RegexValidator(
            regex=pattern,
            inverse_match=inverse
        )
    except re.error:
        # Invalid regex pattern
        return
    
    try:
        validator(test_string)
        # Validation passed
        if inverse:
            # With inverse_match, should pass if pattern does NOT match
            assert not re.search(pattern, test_string), f"Inverse validator passed but pattern matches"
        else:
            # Normal mode, should pass if pattern matches
            assert re.search(pattern, test_string), f"Validator passed but pattern doesn't match"
    except ValidationError:
        # Validation failed
        if inverse:
            # With inverse_match, should fail if pattern matches
            assert re.search(pattern, test_string), f"Inverse validator failed but pattern doesn't match"
        else:
            # Normal mode, should fail if pattern doesn't match
            assert not re.search(pattern, test_string), f"Validator failed but pattern matches"


# Test validate_ipv4_address
@given(st.text(max_size=50))
@settings(max_examples=1000)
def test_ipv4_validator(text):
    """Test IPv4 address validation."""
    try:
        validators.validate_ipv4_address(text)
        # If it passes, verify it's a valid IPv4
        parts = text.split('.')
        assert len(parts) == 4, f"IPv4 validator accepted '{text}' with {len(parts)} parts"
        for part in parts:
            assert part.isdigit(), f"IPv4 validator accepted non-digit part: {part}"
            assert 0 <= int(part) <= 255, f"IPv4 validator accepted out-of-range part: {part}"
    except ValidationError:
        # Expected for invalid IPs
        pass


# Test validate_comma_separated_integer_list
@given(st.text(max_size=100))
@settings(max_examples=1000)
def test_comma_separated_integers_validator(text):
    """Test comma-separated integer list validation."""
    try:
        validators.validate_comma_separated_integer_list(text)
        # If it passes, verify it's actually comma-separated integers
        if text:
            parts = text.split(',')
            for part in parts:
                part = part.strip()
                if part:  # Skip empty parts
                    assert part.lstrip('-').isdigit(), f"Accepted non-integer: {part}"
    except ValidationError:
        # Expected for invalid input
        pass