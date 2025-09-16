"""Property-based tests for troposphere.ec2 validators"""

import re
from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere.validators import boolean, integer, double, network_port, s3_bucket_name, integer_range
from troposphere.validators.ec2 import (
    validate_int_to_str,
    vpn_pre_shared_key,
    vpn_tunnel_inside_cidr,
    validate_networkaclentry_rulenumber,
    validate_clientvpnendpoint_vpnport,
    validate_placement_strategy,
    validate_placement_spread_level,
    validate_elasticinferenceaccelerator_type,
    validate_clientvpnendpoint_selfserviceportal,
    vpc_endpoint_type,
    instance_tenancy
)


# Test 1: validate_int_to_str round-trip property
@given(st.integers())
def test_validate_int_to_str_int_input(n):
    """Property: validate_int_to_str should convert int to str"""
    result = validate_int_to_str(n)
    assert isinstance(result, str)
    assert result == str(n)


@given(st.text())
def test_validate_int_to_str_str_input(s):
    """Property: validate_int_to_str should handle valid numeric strings"""
    try:
        # Only test if string represents a valid integer
        int_val = int(s)
        result = validate_int_to_str(s)
        assert isinstance(result, str)
        assert result == str(int_val)
    except (ValueError, TypeError):
        # Should raise TypeError for non-numeric strings
        with pytest.raises(TypeError):
            validate_int_to_str(s)


@given(st.integers())
def test_validate_int_to_str_round_trip(n):
    """Property: Converting int->str->int should preserve value"""
    str_result = validate_int_to_str(n)
    int_result = validate_int_to_str(str_result)
    assert int(int_result) == n


# Test 2: vpn_pre_shared_key validation
@given(st.text(min_size=8, max_size=64, alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_.")))
def test_vpn_pre_shared_key_valid(key):
    """Property: Valid keys matching the pattern should be accepted"""
    # Keys cannot start with '0'
    assume(not key.startswith('0'))
    result = vpn_pre_shared_key(key)
    assert result == key


@given(st.text())
def test_vpn_pre_shared_key_invalid_patterns(key):
    """Property: Keys not matching the pattern should raise ValueError"""
    # Test various invalid patterns
    is_valid = (
        len(key) >= 8 and 
        len(key) <= 64 and 
        not key.startswith('0') and
        all(c.isalnum() or c in '_.' for c in key)
    )
    
    if is_valid:
        result = vpn_pre_shared_key(key)
        assert result == key
    else:
        with pytest.raises(ValueError):
            vpn_pre_shared_key(key)


# Test 3: vpn_tunnel_inside_cidr validation
@given(st.integers(min_value=0, max_value=255), st.integers(min_value=0, max_value=255))
def test_vpn_tunnel_inside_cidr_valid_format(octet3, octet4):
    """Property: Valid /30 CIDRs in 169.254.0.0/16 should be accepted"""
    cidr = f"169.254.{octet3}.{octet4}/30"
    
    # Check if it's in the reserved list
    reserved_cidrs = [
        "169.254.0.0/30",
        "169.254.1.0/30",
        "169.254.2.0/30",
        "169.254.3.0/30",
        "169.254.4.0/30",
        "169.254.5.0/30",
        "169.254.169.252/30",
    ]
    
    if cidr in reserved_cidrs:
        with pytest.raises(ValueError, match="reserved and cannot be used"):
            vpn_tunnel_inside_cidr(cidr)
    else:
        result = vpn_tunnel_inside_cidr(cidr)
        assert result == cidr


@given(st.text())
def test_vpn_tunnel_inside_cidr_invalid_format(cidr):
    """Property: Invalid CIDR formats should raise ValueError"""
    # Check if it matches the valid pattern
    cidr_match_re = re.compile(
        r"^169\.254\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)"
        r"\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\/30$"
    )
    
    reserved_cidrs = [
        "169.254.0.0/30",
        "169.254.1.0/30",
        "169.254.2.0/30",
        "169.254.3.0/30",
        "169.254.4.0/30",
        "169.254.5.0/30",
        "169.254.169.252/30",
    ]
    
    if cidr_match_re.match(cidr) and cidr not in reserved_cidrs:
        result = vpn_tunnel_inside_cidr(cidr)
        assert result == cidr
    else:
        with pytest.raises(ValueError):
            vpn_tunnel_inside_cidr(cidr)


# Test 4: network_port validation
@given(st.integers())
def test_network_port_range(port):
    """Property: network_port should only accept values between -1 and 65535"""
    if -1 <= port <= 65535:
        result = network_port(port)
        assert result == port
    else:
        with pytest.raises(ValueError, match="must been between 0 and 65535"):
            network_port(port)


# Test 5: boolean conversion
@given(st.sampled_from([True, 1, "1", "true", "True"]))
def test_boolean_true_values(value):
    """Property: These values should all convert to True"""
    assert boolean(value) is True


@given(st.sampled_from([False, 0, "0", "false", "False"]))
def test_boolean_false_values(value):
    """Property: These values should all convert to False"""
    assert boolean(value) is False


@given(st.one_of(st.text(), st.integers(), st.floats(), st.none()))
def test_boolean_invalid_values(value):
    """Property: Invalid values should raise ValueError"""
    valid_true = [True, 1, "1", "true", "True"]
    valid_false = [False, 0, "0", "false", "False"]
    
    if value in valid_true:
        assert boolean(value) is True
    elif value in valid_false:
        assert boolean(value) is False
    else:
        with pytest.raises(ValueError):
            boolean(value)


# Test 6: validate_networkaclentry_rulenumber
@given(st.integers())
def test_networkaclentry_rulenumber_range(n):
    """Property: Rule numbers must be between 1 and 32766"""
    if 1 <= n <= 32766:
        result = validate_networkaclentry_rulenumber(n)
        assert result == n
    else:
        with pytest.raises(ValueError):
            validate_networkaclentry_rulenumber(n)


# Test 7: integer_range factory function
@given(st.integers(), st.integers(), st.integers())
def test_integer_range_validator(min_val, max_val, test_val):
    """Property: integer_range should create validators that check bounds correctly"""
    assume(min_val <= max_val)  # Ensure valid range
    
    validator = integer_range(min_val, max_val)
    
    if min_val <= test_val <= max_val:
        result = validator(test_val)
        assert result == test_val
    else:
        with pytest.raises(ValueError, match="Integer must be between"):
            validator(test_val)


# Test 8: s3_bucket_name validation
@given(st.text())
def test_s3_bucket_name_no_consecutive_periods(name):
    """Property: S3 bucket names cannot have consecutive periods"""
    if ".." in name:
        with pytest.raises(ValueError, match="not a valid s3 bucket name"):
            s3_bucket_name(name)


@given(st.from_regex(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"))
def test_s3_bucket_name_no_ip_addresses(ip_like):
    """Property: S3 bucket names cannot look like IP addresses"""
    with pytest.raises(ValueError, match="not a valid s3 bucket name"):
        s3_bucket_name(ip_like)


@given(st.from_regex(r"^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$"))
def test_s3_bucket_name_valid_pattern(name):
    """Property: Valid S3 bucket names matching the pattern should be accepted"""
    # Must not have consecutive periods or look like IP
    assume(".." not in name)
    assume(not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", name))
    
    result = s3_bucket_name(name)
    assert result == name


# Test 9: Enum-like validators
def test_placement_strategy_enum():
    """Property: placement_strategy should only accept specific values"""
    valid = ["cluster", "partition", "spread"]
    invalid = ["invalid", "random", "", None, 123]
    
    for v in valid:
        assert validate_placement_strategy(v) == v
    
    for v in invalid:
        with pytest.raises((ValueError, AttributeError, TypeError)):
            validate_placement_strategy(v)


def test_vpc_endpoint_type_enum():
    """Property: vpc_endpoint_type should only accept specific values"""
    valid = ["Interface", "Gateway", "GatewayLoadBalancer"]
    invalid = ["interface", "gateway", "Invalid", "", None]
    
    for v in valid:
        assert vpc_endpoint_type(v) == v
    
    for v in invalid:
        with pytest.raises((ValueError, AttributeError, TypeError)):
            vpc_endpoint_type(v)


# Test 10: validate_clientvpnendpoint_vpnport
@given(st.integers())
def test_clientvpnendpoint_vpnport(port):
    """Property: VPN port must be either 443 or 1194"""
    if port in [443, 1194]:
        assert validate_clientvpnendpoint_vpnport(port) == port
    else:
        with pytest.raises(ValueError, match="VpnPort must be one of"):
            validate_clientvpnendpoint_vpnport(port)


# Edge case tests for integer validators
@given(st.sampled_from([float('inf'), float('-inf'), float('nan')]))
def test_integer_validators_with_special_floats(value):
    """Property: Special float values should not be accepted by integer validators"""
    with pytest.raises((ValueError, TypeError, OverflowError)):
        integer(value)
    
    with pytest.raises((ValueError, TypeError, OverflowError)):
        validate_networkaclentry_rulenumber(value)
    
    with pytest.raises((ValueError, TypeError, OverflowError)):
        network_port(value)


# Test for interaction between validators
@given(st.integers(min_value=-100, max_value=100))
def test_network_port_accepts_negative_one(port):
    """Property: network_port specifically allows -1 (for all ports in security groups)"""
    if port == -1:
        result = network_port(port)
        assert result == port
    elif 0 <= port <= 65535:
        result = network_port(port)
        assert result == port
    else:
        with pytest.raises(ValueError):
            network_port(port)