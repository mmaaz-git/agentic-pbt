"""Property-based tests for troposphere.s3 module"""

import re
from hypothesis import given, strategies as st, assume, settings
import troposphere.s3 as s3
import troposphere
from troposphere.validators import s3_bucket_name


# Strategy for valid S3 bucket names based on the regex pattern
# Must be 3-63 chars, start/end with lowercase letter or digit
# Can contain lowercase letters, digits, hyphens, and dots (but not consecutive dots)
def valid_s3_bucket_name_strategy():
    # Generate parts that can be joined with single dots
    part = st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz0123456789-',
        min_size=1,
        max_size=10
    ).filter(lambda s: not s.startswith('-') and not s.endswith('-'))
    
    # Generate 1-6 parts to stay within 63 char limit
    parts = st.lists(part, min_size=1, max_size=6)
    
    return parts.map(lambda p: '.'.join(p)).filter(
        lambda s: 3 <= len(s) <= 63 and 
        s[0] in 'abcdefghijklmnopqrstuvwxyz0123456789' and
        s[-1] in 'abcdefghijklmnopqrstuvwxyz0123456789'
    )


@given(valid_s3_bucket_name_strategy())
def test_valid_bucket_names_accepted(name):
    """Test that valid S3 bucket names are accepted by validator"""
    # The validator should return the name unchanged for valid names
    result = s3_bucket_name(name)
    assert result == name


@given(st.text(min_size=3, max_size=63))
def test_invalid_bucket_names_rejected(name):
    """Test that invalid patterns are properly rejected"""
    # Check if name contains invalid patterns
    has_consecutive_dots = '..' in name
    is_ip_address = bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', name))
    matches_valid_pattern = bool(re.match(r'^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$', name))
    
    should_be_invalid = has_consecutive_dots or is_ip_address or not matches_valid_pattern
    
    try:
        result = s3_bucket_name(name)
        # If we get here, validator accepted the name
        assert not should_be_invalid, f"Validator accepted invalid name: {name}"
    except ValueError as e:
        # Validator rejected the name
        assert should_be_invalid, f"Validator rejected valid name: {name}"
        assert name in str(e), "Error message should contain the invalid bucket name"


@given(st.text(alphabet='0123456789.', min_size=7, max_size=15))
def test_ip_address_like_strings_rejected(text):
    """Test that IP address patterns are consistently rejected"""
    # If it looks like an IP address, it should be rejected
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', text):
        try:
            s3_bucket_name(text)
            assert False, f"IP address pattern {text} should be rejected"
        except ValueError as e:
            assert text in str(e)


@given(st.dictionaries(
    st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=20),
    st.text(min_size=0, max_size=50),
    min_size=0,
    max_size=10
))
def test_tags_to_dict_preserves_all_keys(tag_dict):
    """Test that Tags.to_dict preserves all key-value pairs"""
    tags = troposphere.Tags(**tag_dict)
    result = tags.to_dict()
    
    # Result should be a list of dicts with Key and Value
    assert isinstance(result, list)
    assert len(result) == len(tag_dict)
    
    # All original keys and values should be present
    result_dict = {item['Key']: item['Value'] for item in result}
    assert result_dict == tag_dict


@given(valid_s3_bucket_name_strategy())
def test_bucket_to_dict_preserves_bucket_name(bucket_name):
    """Test that Bucket.to_dict preserves the BucketName property"""
    bucket = s3.Bucket('TestBucket')
    bucket.BucketName = bucket_name
    
    result = bucket.to_dict()
    
    # Check structure
    assert 'Type' in result
    assert result['Type'] == 'AWS::S3::Bucket'
    assert 'Properties' in result
    assert 'BucketName' in result['Properties']
    assert result['Properties']['BucketName'] == bucket_name


@given(
    st.dictionaries(
        st.sampled_from(['AccelerateConfiguration', 'AccessControl', 'BucketName']),
        st.one_of(
            valid_s3_bucket_name_strategy(),
            st.sampled_from(['Private', 'PublicRead', 'PublicReadWrite', 'AuthenticatedRead'])
        ),
        max_size=3
    )
)
def test_bucket_multiple_properties_preserved(properties):
    """Test that multiple Bucket properties are preserved in to_dict"""
    bucket = s3.Bucket('TestBucket')
    
    # Set properties dynamically
    for key, value in properties.items():
        if key == 'BucketName' and not re.match(r'^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$', value):
            # Skip invalid bucket names for this test
            continue
        setattr(bucket, key, value)
    
    result = bucket.to_dict()
    
    # All set properties should appear in the result
    if hasattr(bucket, 'BucketName') and bucket.BucketName:
        assert result['Properties'].get('BucketName') == bucket.BucketName
    if hasattr(bucket, 'AccessControl') and bucket.AccessControl:
        assert result['Properties'].get('AccessControl') == bucket.AccessControl


# Test for potential case sensitivity issues
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=3, max_size=63))
def test_bucket_name_lowercase_only(name):
    """Test that bucket names with uppercase are properly rejected"""
    # Make some characters uppercase
    if name:
        mixed_case = ''.join(c.upper() if i % 3 == 0 else c for i, c in enumerate(name))
        if mixed_case != mixed_case.lower():
            # Should be rejected due to uppercase
            try:
                s3_bucket_name(mixed_case)
                assert False, f"Bucket name with uppercase {mixed_case} should be rejected"
            except ValueError:
                pass  # Expected


# Test edge cases around length limits
@given(st.integers(min_value=1, max_value=100))
def test_bucket_name_length_boundaries(length):
    """Test bucket name validation at length boundaries"""
    if length < 3 or length > 63:
        # Should be rejected
        name = 'a' * length
        try:
            s3_bucket_name(name)
            assert False, f"Bucket name of length {length} should be rejected"
        except ValueError as e:
            assert name in str(e)
    else:
        # Could be valid if it follows other rules
        name = 'a' + 'b' * (length - 2) + 'c'
        result = s3_bucket_name(name)
        assert result == name