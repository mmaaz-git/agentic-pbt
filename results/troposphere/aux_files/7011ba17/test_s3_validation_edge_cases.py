"""Edge case tests for S3 bucket name validation"""

import re
from hypothesis import given, strategies as st, assume, settings, example
import troposphere.s3 as s3
from troposphere.validators import s3_bucket_name


# Test the regex pattern edge cases more carefully
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789.-', min_size=3, max_size=63))
def test_bucket_name_validation_consistency(name):
    """Test that validation is consistent with its own rules"""
    
    # These are the rules from the source code:
    # 1. No consecutive dots
    # 2. Not an IP address
    # 3. Must match ^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$
    
    has_consecutive_dots = '..' in name
    is_ip = bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', name))
    matches_pattern = bool(re.match(r'^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$', name))
    
    should_be_valid = not has_consecutive_dots and not is_ip and matches_pattern
    
    try:
        result = s3_bucket_name(name)
        # Accepted - should be valid
        assert should_be_valid, f"Accepted invalid name: {name} (dots={has_consecutive_dots}, ip={is_ip}, pattern={matches_pattern})"
        assert result == name, f"Validator modified valid name: {name} -> {result}"
    except ValueError as e:
        # Rejected - should be invalid
        assert not should_be_valid, f"Rejected valid name: {name} (dots={has_consecutive_dots}, ip={is_ip}, pattern={matches_pattern})"


# Test specific patterns that might be edge cases
@given(st.text(alphabet='0123456789.-', min_size=3, max_size=63))
def test_numeric_bucket_names(name):
    """Test bucket names that are mostly numbers"""
    try:
        result = s3_bucket_name(name)
        # If accepted, verify it actually matches the pattern
        assert re.match(r'^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$', name)
        assert '..' not in name
        assert not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', name)
    except ValueError:
        # If rejected, at least one rule must be violated
        violates_rule = (
            '..' in name or
            re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', name) or
            not re.match(r'^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$', name)
        )
        assert violates_rule


# Test boundary cases for IP detection
@given(st.lists(st.integers(min_value=0, max_value=999), min_size=4, max_size=4))
def test_ip_pattern_detection(parts):
    """Test IP address pattern detection with various numeric ranges"""
    name = '.'.join(str(p) for p in parts)
    
    # Check if it looks like an IP
    looks_like_ip = bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', name))
    
    if looks_like_ip:
        # Should be rejected as IP
        try:
            s3_bucket_name(name)
            # Some "IPs" might be too long (>63 chars) or violate other rules
            assert len(name) > 63 or any(p > 999 for p in parts), f"IP pattern {name} was accepted"
        except ValueError as e:
            assert name in str(e)
    

# Test strings that are almost IPs
@given(st.text(alphabet='0123456789.a', min_size=7, max_size=15))
def test_almost_ip_patterns(text):
    """Test strings that are close to IP addresses"""
    # If it's exactly an IP pattern, should be rejected
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', text):
        try:
            s3_bucket_name(text)
            assert False, f"IP address {text} should be rejected"
        except ValueError:
            pass
    # If it has a letter mixed in, might be valid if other rules pass
    elif 'a' in text and text[0] in 'a0123456789' and text[-1] in 'a0123456789':
        if '..' not in text and 3 <= len(text) <= 63:
            # Might be valid
            try:
                result = s3_bucket_name(text)
                # Verify it really matches the pattern
                assert re.match(r'^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$', text)
            except ValueError:
                # Must violate the regex pattern somehow
                pass


# Test edge cases with dots at boundaries
@given(st.one_of(
    st.just('a.'),
    st.just('.a'),
    st.just('a.b'),
    st.just('a..b'),
    st.just('123.456.789.012'),  # IP-like
    st.just('1.2.3.4'),  # Valid IP
    st.just('1.2.3.4a'),  # IP with letter
    st.just('a1.2.3.4'),  # IP with letter at start
))
def test_specific_edge_cases(name):
    """Test specific edge case patterns"""
    try:
        result = s3_bucket_name(name)
        # If accepted, verify all rules
        assert '..' not in name, f"Accepted name with consecutive dots: {name}"
        assert not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', name), f"Accepted IP: {name}"
        assert re.match(r'^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$', name), f"Accepted non-matching: {name}"
        assert 3 <= len(name) <= 63
    except ValueError:
        # Should violate at least one rule
        pass


# Focus on the regex boundary conditions
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=1, max_size=2))
def test_very_short_names(name):
    """Test names shorter than 3 characters"""
    # Should always be rejected (min length is 3)
    try:
        s3_bucket_name(name)
        assert False, f"Name shorter than 3 chars was accepted: {name}"
    except ValueError as e:
        assert name in str(e)


@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789', min_size=64, max_size=100))
def test_very_long_names(name):
    """Test names longer than 63 characters"""
    # Should always be rejected (max length is 63)
    try:
        s3_bucket_name(name)
        assert False, f"Name longer than 63 chars was accepted: {name} (len={len(name)})"
    except ValueError as e:
        assert name in str(e)


# Test exact length boundaries
def test_exact_length_boundaries():
    """Test names at exact length boundaries"""
    # 2 chars - should fail
    try:
        s3_bucket_name('ab')
        assert False, "2-char name should be rejected"
    except ValueError:
        pass
    
    # 3 chars - should pass if valid pattern
    result = s3_bucket_name('abc')
    assert result == 'abc'
    
    # 63 chars - should pass if valid pattern
    name_63 = 'a' + 'b' * 61 + 'c'
    assert len(name_63) == 63
    result = s3_bucket_name(name_63)
    assert result == name_63
    
    # 64 chars - should fail
    name_64 = 'a' + 'b' * 62 + 'c'
    assert len(name_64) == 64
    try:
        s3_bucket_name(name_64)
        assert False, "64-char name should be rejected"
    except ValueError:
        pass