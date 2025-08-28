"""Focused bug hunting tests for troposphere.s3"""

from hypothesis import given, strategies as st, assume, settings, example
import troposphere.s3 as s3
import troposphere
import json
import re
from troposphere.validators import s3_bucket_name


# Test for potential unicode handling issues in bucket names
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789.-\u0301\u0308', min_size=3, max_size=63))
def test_bucket_name_unicode_handling(name):
    """Test that bucket names with unicode combining characters are handled correctly"""
    # S3 bucket names should only contain ASCII characters
    # If the validator accepts unicode, that's a bug
    
    has_non_ascii = any(ord(c) > 127 for c in name)
    
    if has_non_ascii:
        # Should be rejected
        try:
            result = s3_bucket_name(name)
            # This is a BUG - unicode should not be accepted
            assert False, f"Validator accepted non-ASCII name: {name!r}"
        except (ValueError, UnicodeError):
            pass  # Expected
    else:
        # Regular ASCII validation rules apply
        try:
            result = s3_bucket_name(name)
            # Should match the pattern if accepted
            assert re.match(r'^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$', name)
            assert '..' not in name
        except ValueError:
            # Should violate one of the rules
            pass


# Test for potential regex bypass with special characters
@given(st.text(min_size=3, max_size=63))
def test_bucket_name_special_chars(name):
    """Test that special characters don't bypass validation"""
    # Only lowercase letters, digits, hyphens, and dots should be allowed
    allowed_chars = set('abcdefghijklmnopqrstuvwxyz0123456789.-')
    
    has_invalid_chars = any(c not in allowed_chars for c in name)
    
    if has_invalid_chars:
        # Should be rejected
        try:
            result = s3_bucket_name(name)
            # This would be a bug - invalid chars accepted
            assert False, f"Validator accepted name with invalid chars: {name!r}"
        except ValueError:
            pass  # Expected


# Test boundary between valid and invalid IP addresses
@given(
    st.integers(min_value=0, max_value=999),
    st.integers(min_value=0, max_value=999),
    st.integers(min_value=0, max_value=999),
    st.integers(min_value=0, max_value=999)
)
def test_ip_validation_edge_cases(a, b, c, d):
    """Test IP address validation with edge cases"""
    name = f"{a}.{b}.{c}.{d}"
    
    # Check if it matches the IP pattern used in validation
    is_ip_pattern = bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', name))
    
    if is_ip_pattern:
        # Should always be rejected as an IP
        try:
            result = s3_bucket_name(name)
            # BUG: IP pattern was accepted
            assert False, f"IP address pattern {name} was accepted"
        except ValueError as e:
            assert name in str(e)
    else:
        # Numbers might be too large (4+ digits)
        # These should be rejected for different reasons
        if len(name) > 63:
            try:
                s3_bucket_name(name)
                assert False, f"Name longer than 63 chars accepted: {name}"
            except ValueError:
                pass


# Test for off-by-one errors in length validation
@given(st.integers(min_value=0, max_value=100))
def test_length_validation_boundaries(length):
    """Test exact boundaries of length validation"""
    if length == 0:
        return  # Can't create empty string bucket name
    
    # Create name of exact length with valid characters
    if length == 1:
        name = 'a'
    elif length == 2:
        name = 'ab'
    else:
        # Make sure first and last are alphanumeric
        name = 'a' + 'b' * (length - 2) + 'c'
    
    if length < 3:
        # Should be rejected - too short
        try:
            result = s3_bucket_name(name)
            assert False, f"Name with length {length} was accepted: {name}"
        except ValueError as e:
            assert name in str(e)
    elif length > 63:
        # Should be rejected - too long
        try:
            result = s3_bucket_name(name)
            assert False, f"Name with length {length} was accepted: {name}"
        except ValueError as e:
            assert name in str(e)
    else:
        # Should be accepted (3-63 chars)
        result = s3_bucket_name(name)
        assert result == name


# Test consecutive dots more thoroughly
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789.-', min_size=3, max_size=63))
def test_consecutive_dots_detection(name):
    """Test that all consecutive dot patterns are caught"""
    # Count consecutive dots
    max_consecutive_dots = 0
    current_dots = 0
    for char in name:
        if char == '.':
            current_dots += 1
            max_consecutive_dots = max(max_consecutive_dots, current_dots)
        else:
            current_dots = 0
    
    has_consecutive_dots = max_consecutive_dots >= 2
    
    if has_consecutive_dots:
        # Should always be rejected
        try:
            result = s3_bucket_name(name)
            # BUG: Name with consecutive dots was accepted
            assert False, f"Name with {max_consecutive_dots} consecutive dots accepted: {name}"
        except ValueError as e:
            assert name in str(e)


# Test Tags edge cases
@given(st.dictionaries(
    st.text(min_size=0, max_size=5),  # Include empty string as key
    st.text(min_size=0, max_size=100),
    min_size=0,
    max_size=5
))
def test_tags_empty_keys(tag_dict):
    """Test how Tags handles empty or whitespace keys"""
    tags = troposphere.Tags(**tag_dict)
    result = tags.to_dict()
    
    # Check all keys are preserved, even empty ones
    result_keys = {item['Key'] for item in result}
    assert result_keys == set(tag_dict.keys())
    
    # Verify empty keys are handled
    for item in result:
        if item['Key'] == '':
            # Empty key should be preserved
            assert item['Value'] == tag_dict['']


# Test potential issues with very long tag values
@given(st.dictionaries(
    st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10),
    st.text(min_size=0, max_size=10000),  # Very long values
    min_size=1,
    max_size=3
))
def test_tags_long_values(tag_dict):
    """Test Tags with very long values"""
    tags = troposphere.Tags(**tag_dict)
    result = tags.to_dict()
    
    # All values should be preserved completely
    for item in result:
        assert item['Value'] == tag_dict[item['Key']]
        # No truncation should occur
        assert len(item['Value']) == len(tag_dict[item['Key']])


# Test object creation with invalid property types to find type confusion
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False),
    st.booleans(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text())
))
def test_bucket_property_type_validation(value):
    """Test that Bucket properties validate types correctly"""
    bucket = s3.Bucket('TestBucket')
    
    # Try setting BucketName to non-string value
    if not isinstance(value, str):
        try:
            bucket.BucketName = value
            # If it accepts non-string, the validator should catch it
            if hasattr(bucket, 'to_dict'):
                result = bucket.to_dict()
                # Check if the value was coerced or stored as-is
                stored_value = result.get('Properties', {}).get('BucketName')
                if stored_value is not None:
                    # If it got here, type checking might be weak
                    assert isinstance(stored_value, str), f"Non-string value {value!r} not converted to string"
        except (TypeError, ValueError, AttributeError):
            pass  # Expected - type validation working