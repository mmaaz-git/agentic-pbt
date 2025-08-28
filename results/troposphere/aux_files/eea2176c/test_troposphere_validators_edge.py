#!/usr/bin/env python3
"""Edge case tests for troposphere validators"""

import sys
from hypothesis import given, strategies as st, assume, settings, example
import pytest

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

# Test edge cases for integer validator
@given(st.text())
@example("1.0")  # Float-like string that's actually an integer
@example("1e10")  # Scientific notation
@example("0x10")  # Hexadecimal
@example("0o10")  # Octal
@example("0b10")  # Binary
@example(" 10 ")  # Whitespace
@example("+10")   # Explicit positive
@example("10L")   # Old Python long notation
@example("١٠")    # Arabic numerals
def test_integer_validator_string_edge_cases(value):
    """Test integer validator with various string representations"""
    try:
        result = validators.integer(value)
        # If it passes, verify we can convert to int
        converted = int(result)
        
        # Also verify the original string could be converted
        # (This catches cases where validator might be too permissive)
        try:
            int(value)
        except ValueError:
            # Validator accepted something Python's int() wouldn't
            print(f"Validator accepted non-standard integer format: {repr(value)}")
            
    except ValueError as e:
        # If validator rejects, check if Python's int() would accept
        try:
            int_val = int(value)
            # Python accepts it but validator doesn't - potential bug
            print(f"Validator rejected valid Python integer: {repr(value)} -> {int_val}")
        except:
            pass  # Both reject, consistent behavior

# Test byte-like inputs for integer validator
@given(st.binary())
def test_integer_validator_bytes(value):
    """Test if integer validator handles bytes properly"""
    try:
        result = validators.integer(value)
        # Bytes might be accepted - let's see what happens
        int(result)
        print(f"Integer validator accepted bytes: {repr(value)}")
    except (ValueError, TypeError):
        pass  # Expected

# Test positive_integer with boundary values
@given(st.sampled_from([0, -0, 0.0, -0.0, "0", "-0", "+0"]))
def test_positive_integer_zero_variants(value):
    """Test positive_integer validator with various representations of zero"""
    try:
        result = validators.positive_integer(value)
        # Zero should be accepted (it's non-negative)
        assert int(result) == 0
    except ValueError as e:
        # If it rejects zero, that's a bug
        pytest.fail(f"positive_integer rejected zero variant {repr(value)}: {e}")

# Test double validator with integer-like floats
@given(st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x.is_integer()))
def test_double_validator_integer_floats(value):
    """Test double validator with floats that are exactly integers"""
    result = validators.double(value)
    assert float(result) == value

# Test network_port validator boundaries
@given(st.integers())
def test_network_port_boundaries(value):
    """Test network_port validator accepts correct range"""
    try:
        result = validators.network_port(value)
        port = int(result)
        # Should be between -1 and 65535 inclusive
        assert -1 <= port <= 65535, f"network_port accepted out-of-range: {port}"
    except ValueError:
        # Should only reject if outside range
        assert value < -1 or value > 65535, f"network_port rejected valid port: {value}"

# Test integer_range factory function
@given(
    min_val=st.integers(min_value=-1000, max_value=1000),
    max_val=st.integers(min_value=-1000, max_value=1000),
    test_val=st.integers(min_value=-2000, max_value=2000)
)
def test_integer_range_validator(min_val, max_val, test_val):
    """Test integer_range validator factory"""
    assume(min_val <= max_val)  # Valid range
    
    validator = validators.integer_range(min_val, max_val)
    
    try:
        result = validator(test_val)
        # Should be in range
        assert min_val <= int(result) <= max_val
    except ValueError:
        # Should be out of range
        assert test_val < min_val or test_val > max_val

# Test boolean validator with numeric strings
@given(st.text(alphabet="01", min_size=1, max_size=10))
def test_boolean_numeric_strings(value):
    """Test boolean validator with strings of 0s and 1s"""
    try:
        result = validators.boolean(value)
        # Should only accept exactly "0" or "1"
        if value == "0":
            assert result is False
        elif value == "1":
            assert result is True
        else:
            pytest.fail(f"Boolean validator accepted multi-digit string: {value}")
    except ValueError:
        # Should reject anything other than "0" or "1"
        assert value not in ["0", "1"]

# Test s3_bucket_name validator
@given(st.text(min_size=1, max_size=100))
@example("192.168.1.1")  # IP address - should reject
@example("bucket..name")  # Consecutive dots - should reject
@example("BucketName")    # Uppercase - should reject
@example("bucket-name")   # Valid
@example("bucket.name")   # Valid
@example("my-bucket-123") # Valid
def test_s3_bucket_name_validator(name):
    """Test S3 bucket name validation rules"""
    try:
        result = validators.s3_bucket_name(name)
        # If accepted, verify it follows S3 rules:
        # - 3-63 characters
        # - lowercase letters, numbers, dots, hyphens
        # - starts and ends with letter or number
        # - no consecutive dots
        # - not an IP address
        
        assert 2 <= len(result) <= 63, f"Invalid length: {len(result)}"
        assert result[0].isalnum(), f"Must start with alphanumeric: {result[0]}"
        assert result[-1].isalnum(), f"Must end with alphanumeric: {result[-1]}"
        assert ".." not in result, "Contains consecutive dots"
        assert result == result.lower(), "Contains uppercase"
        
        # Check not an IP
        parts = result.split(".")
        if len(parts) == 4:
            try:
                if all(0 <= int(p) <= 255 for p in parts):
                    pytest.fail(f"Accepted IP address as bucket name: {result}")
            except ValueError:
                pass  # Not all numeric, so not an IP
                
    except ValueError:
        # Validator rejected - verify it should have
        is_valid = (
            2 <= len(name) <= 63 and
            name[0].isalnum() and name[0].islower() and
            name[-1].isalnum() and name[-1].islower() and
            ".." not in name and
            all(c.isalnum() or c in ".-" for c in name) and
            name == name.lower()
        )
        
        # Check if it's an IP
        parts = name.split(".")
        if len(parts) == 4:
            try:
                if all(0 <= int(p) <= 255 for p in parts):
                    is_valid = False  # IPs are invalid
            except ValueError:
                pass
                
        if is_valid:
            print(f"Validator incorrectly rejected valid bucket name: {name}")

# Test elb_name validator
@given(st.text(min_size=1, max_size=50))
@example("my-load-balancer")     # Valid
@example("LoadBalancer123")       # Valid
@example("-invalid")              # Invalid - starts with hyphen
@example("invalid-")              # Invalid - ends with hyphen
@example("my--load--balancer")   # Valid - consecutive hyphens allowed in middle
def test_elb_name_validator(name):
    """Test ELB name validation rules"""
    try:
        result = validators.elb_name(name)
        # Must be 1-32 chars, alphanumeric and hyphens
        # Must start and end with alphanumeric
        assert 1 <= len(result) <= 32
        assert result[0].isalnum()
        assert result[-1].isalnum()
        assert all(c.isalnum() or c == "-" for c in result)
    except ValueError:
        # Should have been invalid
        is_valid = (
            1 <= len(name) <= 32 and
            len(name) > 0 and
            name[0].isalnum() and
            (len(name) == 1 or name[-1].isalnum()) and
            all(c.isalnum() or c == "-" for c in name)
        )
        if is_valid:
            print(f"Validator incorrectly rejected valid ELB name: {name}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])