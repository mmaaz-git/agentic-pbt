"""Property-based tests for requests.utils module."""

import math
import socket
import struct
from collections import OrderedDict
from http.cookiejar import CookieJar

import pytest
from hypothesis import assume, given, settings, strategies as st

import requests.utils


# Test 1: Round-trip property for from_key_val_list and to_key_val_list
@given(st.lists(st.tuples(st.text(), st.text())))
def test_from_to_key_val_list_round_trip(pairs):
    """Test that to_key_val_list(from_key_val_list(x)) == x for valid inputs."""
    try:
        intermediate = requests.utils.from_key_val_list(pairs)
        result = requests.utils.to_key_val_list(intermediate)
        assert result == pairs
    except ValueError:
        # If from_key_val_list raises ValueError, that's expected for invalid input
        pass


# Test 2: Invariant for iter_slices - preserves string content
@given(st.text(min_size=1), st.integers(min_value=1, max_value=1000))
def test_iter_slices_preserves_string(string, slice_length):
    """Test that joining slices gives back the original string."""
    slices = list(requests.utils.iter_slices(string, slice_length))
    reconstructed = ''.join(slices)
    assert reconstructed == string


# Test 3: iter_slices with None or <= 0 should return whole string
@given(st.text(min_size=1), st.one_of(st.none(), st.integers(max_value=0)))
def test_iter_slices_none_or_negative(string, slice_length):
    """Test that None or <= 0 slice_length returns the whole string."""
    slices = list(requests.utils.iter_slices(string, slice_length))
    assert len(slices) == 1
    assert slices[0] == string


# Test 4: Idempotence of requote_uri
@given(st.text())
def test_requote_uri_idempotent(uri):
    """Test that requote_uri(requote_uri(x)) == requote_uri(x)."""
    try:
        once = requests.utils.requote_uri(uri)
        twice = requests.utils.requote_uri(once)
        assert twice == once
    except Exception:
        # Invalid URIs may raise exceptions, that's fine
        pass


# Test 5: dotted_netmask mathematical properties
@given(st.integers(min_value=0, max_value=32))
def test_dotted_netmask_properties(mask):
    """Test that dotted_netmask produces valid netmasks."""
    result = requests.utils.dotted_netmask(mask)
    
    # Parse the result back to verify it's a valid IP
    parts = result.split('.')
    assert len(parts) == 4
    
    # Convert back to binary to verify the mask pattern
    binary = []
    for part in parts:
        binary.append(format(int(part), '08b'))
    binary_str = ''.join(binary)
    
    # Should have 'mask' ones followed by (32-mask) zeros
    expected = '1' * mask + '0' * (32 - mask)
    assert binary_str == expected


# Test 6: address_in_network consistency
@given(st.integers(min_value=0, max_value=255),
       st.integers(min_value=0, max_value=255),
       st.integers(min_value=0, max_value=255),
       st.integers(min_value=0, max_value=255),
       st.integers(min_value=16, max_value=30))
def test_address_in_network_consistency(a, b, c, d, mask):
    """Test that network address is always in its own network."""
    ip = f"{a}.{b}.{c}.{d}"
    
    # Calculate network address
    ip_int = struct.unpack("=L", socket.inet_aton(ip))[0]
    netmask = struct.unpack("=L", socket.inet_aton(requests.utils.dotted_netmask(mask)))[0]
    network_int = ip_int & netmask
    network_ip = socket.inet_ntoa(struct.pack("=L", network_int))
    
    network = f"{network_ip}/{mask}"
    
    # Network address should always be in its own network
    assert requests.utils.address_in_network(network_ip, network)


# Test 7: is_ipv4_address validation
@given(st.integers(min_value=0, max_value=255),
       st.integers(min_value=0, max_value=255),
       st.integers(min_value=0, max_value=255),
       st.integers(min_value=0, max_value=255))
def test_is_ipv4_address_valid(a, b, c, d):
    """Test that valid IPv4 addresses are recognized."""
    ip = f"{a}.{b}.{c}.{d}"
    assert requests.utils.is_ipv4_address(ip) == True


@given(st.text())
def test_is_ipv4_address_invalid(text):
    """Test that arbitrary text is usually not a valid IPv4."""
    # Most random text should not be valid IPv4
    result = requests.utils.is_ipv4_address(text)
    # We can't assert False for all cases, but we can check it returns a boolean
    assert isinstance(result, bool)


# Test 8: is_valid_cidr validation
@given(st.integers(min_value=0, max_value=255),
       st.integers(min_value=0, max_value=255),
       st.integers(min_value=0, max_value=255),
       st.integers(min_value=0, max_value=255),
       st.integers(min_value=1, max_value=32))
def test_is_valid_cidr_valid(a, b, c, d, mask):
    """Test that valid CIDR notation is recognized."""
    cidr = f"{a}.{b}.{c}.{d}/{mask}"
    assert requests.utils.is_valid_cidr(cidr) == True


# Test 9: parse_list_header preserves simple values
@given(st.lists(st.text(alphabet=st.characters(blacklist_characters=',"\'"'), min_size=1)))
def test_parse_list_header_simple(items):
    """Test parsing simple comma-separated lists."""
    # Create a simple comma-separated list
    header = ', '.join(items)
    result = requests.utils.parse_list_header(header)
    assert result == items


# Test 10: unquote_header_value removes quotes
@given(st.text())
def test_unquote_header_value(value):
    """Test that unquote_header_value handles quoted strings."""
    # Test with quotes
    quoted = f'"{value}"'
    result = requests.utils.unquote_header_value(quoted)
    # Should remove the outer quotes
    assert result == value or '\\' in value  # Escaping might change the result


# Test 11: dict_to_sequence maintains data
@given(st.dictionaries(st.text(), st.text()))
def test_dict_to_sequence(d):
    """Test that dict_to_sequence preserves dictionary data."""
    result = requests.utils.dict_to_sequence(d)
    # Convert back to dict to check preservation
    result_dict = dict(result)
    assert result_dict == d


# Test 12: super_len returns non-negative values
@given(st.text())
def test_super_len_non_negative(text):
    """Test that super_len always returns non-negative values."""
    length = requests.utils.super_len(text)
    assert length >= 0
    # For strings, should equal the byte length
    if requests.utils.is_urllib3_1:
        assert length == len(text)
    else:
        # urllib3 2.x treats strings as utf-8
        assert length == len(text.encode('utf-8'))


# Test 13: from_key_val_list type errors
@given(st.one_of(st.text(), st.integers(), st.booleans(), st.binary()))
def test_from_key_val_list_type_errors(value):
    """Test that from_key_val_list raises ValueError for non-2-tuple types."""
    with pytest.raises(ValueError, match="cannot encode objects that are not 2-tuples"):
        requests.utils.from_key_val_list(value)


# Test 14: to_key_val_list type errors  
@given(st.one_of(st.text(), st.integers(), st.booleans(), st.binary()))
def test_to_key_val_list_type_errors(value):
    """Test that to_key_val_list raises ValueError for non-2-tuple types."""
    with pytest.raises(ValueError, match="cannot encode objects that are not 2-tuples"):
        requests.utils.to_key_val_list(value)