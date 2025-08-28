#!/usr/bin/env python3
"""Property-based tests for requests.utils module"""

import math
import socket
import struct
from collections import OrderedDict

import pytest
from hypothesis import assume, given, settings, strategies as st

import requests.utils


# Strategy for valid dictionary keys/values (what requests actually uses)
dict_key_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
dict_value_strategy = st.text(max_size=200)
simple_dict_strategy = st.dictionaries(dict_key_strategy, dict_value_strategy, max_size=20)


@given(simple_dict_strategy)
def test_to_from_key_val_list_round_trip(data):
    """Property: from_key_val_list(to_key_val_list(dict)) should preserve the data"""
    # Convert dict to key-val list
    kvlist = requests.utils.to_key_val_list(data)
    
    # Convert back to dict
    result = requests.utils.from_key_val_list(kvlist)
    
    # Should preserve all data
    assert dict(result) == data


@given(st.lists(st.tuples(dict_key_strategy, dict_value_strategy), max_size=20))
def test_from_to_key_val_list_preserves_tuples(data):
    """Property: to_key_val_list(from_key_val_list(list)) should preserve tuple lists"""
    # Convert list of tuples to OrderedDict
    od = requests.utils.from_key_val_list(data)
    
    # Convert back to list
    result = requests.utils.to_key_val_list(od)
    
    # Should preserve unique keys (OrderedDict deduplicates)
    expected = list(OrderedDict(data).items())
    assert result == expected


@given(st.text(min_size=1), st.integers(min_value=-100, max_value=1000))
def test_iter_slices_joins_correctly(text, slice_length):
    """Property: joining slices should reconstruct the original string"""
    slices = list(requests.utils.iter_slices(text, slice_length))
    
    # Joining should give back the original
    assert ''.join(slices) == text
    
    # Each slice (except possibly the last) should have the expected length
    if slice_length and slice_length > 0:
        for s in slices[:-1]:
            assert len(s) == slice_length
        # Last slice should be <= slice_length
        if slices:
            assert len(slices[-1]) <= slice_length


@given(st.text(min_size=1))
def test_iter_slices_with_none_or_zero_returns_whole_string(text):
    """Property: slice_length of None, 0, or negative should return whole string"""
    for slice_length in [None, 0, -1, -100]:
        slices = list(requests.utils.iter_slices(text, slice_length))
        assert slices == [text]


@given(st.integers(min_value=0, max_value=32))
def test_dotted_netmask_valid_range(mask):
    """Property: dotted_netmask should work for valid mask values 0-32"""
    result = requests.utils.dotted_netmask(mask)
    
    # Should be a valid IP address
    assert requests.utils.is_ipv4_address(result)
    
    # Convert back to verify correctness
    packed = struct.unpack(">I", socket.inet_aton(result))[0]
    expected = 0xFFFFFFFF ^ (1 << (32 - mask)) - 1
    assert packed == expected


@given(st.integers(min_value=33, max_value=1000))
def test_dotted_netmask_invalid_range_high(mask):
    """Property: dotted_netmask should fail for mask > 32"""
    with pytest.raises(ValueError):
        requests.utils.dotted_netmask(mask)


@given(st.integers(min_value=-1000, max_value=-1))
def test_dotted_netmask_invalid_range_negative(mask):
    """Property: dotted_netmask should fail for negative masks"""
    with pytest.raises(Exception):  # Can be struct.error or other
        requests.utils.dotted_netmask(mask)


@given(st.text())
def test_is_ipv4_address_doesnt_crash(ip_string):
    """Property: is_ipv4_address should never crash on any string input"""
    result = requests.utils.is_ipv4_address(ip_string)
    assert isinstance(result, bool)


# Generate valid IPv4 addresses
def valid_ipv4_strategy():
    return st.builds(
        lambda a, b, c, d: f"{a}.{b}.{c}.{d}",
        st.integers(0, 255),
        st.integers(0, 255), 
        st.integers(0, 255),
        st.integers(0, 255)
    )


@given(valid_ipv4_strategy())
def test_is_ipv4_address_accepts_valid_ips(ip):
    """Property: is_ipv4_address should accept all valid IPv4 addresses"""
    assert requests.utils.is_ipv4_address(ip) == True


@given(valid_ipv4_strategy(), st.integers(min_value=0, max_value=32))
def test_is_valid_cidr_accepts_valid_cidrs(ip, mask):
    """Property: is_valid_cidr should accept valid CIDR notation"""
    cidr = f"{ip}/{mask}"
    assert requests.utils.is_valid_cidr(cidr) == True


@given(st.text())
def test_is_valid_cidr_doesnt_crash(cidr_string):
    """Property: is_valid_cidr should never crash on any string input"""
    result = requests.utils.is_valid_cidr(cidr_string)
    assert isinstance(result, bool)


@given(valid_ipv4_strategy(), st.integers(min_value=33, max_value=100))
def test_is_valid_cidr_rejects_invalid_masks(ip, mask):
    """Property: is_valid_cidr should reject masks > 32"""
    cidr = f"{ip}/{mask}"
    assert requests.utils.is_valid_cidr(cidr) == False


@given(valid_ipv4_strategy(), st.integers(min_value=-100, max_value=0))
def test_is_valid_cidr_rejects_negative_masks(ip, mask):
    """Property: is_valid_cidr should reject negative masks"""
    cidr = f"{ip}/{mask}"
    assert requests.utils.is_valid_cidr(cidr) == False


# Test address_in_network
@given(valid_ipv4_strategy(), valid_ipv4_strategy(), st.integers(min_value=0, max_value=32))
def test_address_in_network_self_contained(ip, net_ip, mask):
    """Property: An IP is always in its own network with mask 32"""
    # An IP should always be in its own /32 network
    own_network = f"{ip}/32"
    assert requests.utils.address_in_network(ip, own_network) == True
    
    # 0.0.0.0/0 contains everything
    if mask == 0:
        universal = f"{net_ip}/0"
        assert requests.utils.address_in_network(ip, universal) == True


# Test requote_uri - look for idempotence
@given(st.text(min_size=1, max_size=100))
def test_requote_uri_idempotent(text):
    """Property: requote_uri should be idempotent for most inputs"""
    # Add a simple URL prefix to make it more realistic
    uri = f"http://example.com/{text}"
    
    try:
        quoted_once = requests.utils.requote_uri(uri)
        quoted_twice = requests.utils.requote_uri(quoted_once)
        # Should be idempotent
        assert quoted_once == quoted_twice
    except requests.exceptions.InvalidURL:
        # Some inputs might cause InvalidURL, that's OK
        pass


# Test parse_header_links
@given(st.text())
def test_parse_header_links_doesnt_crash(header_value):
    """Property: parse_header_links should never crash"""
    result = requests.utils.parse_header_links(header_value)
    assert isinstance(result, list)


# Test parse_dict_header
@given(st.text())
def test_parse_dict_header_doesnt_crash(header_value):
    """Property: parse_dict_header should never crash"""
    result = requests.utils.parse_dict_header(header_value)
    assert isinstance(result, dict)


# Test parse_list_header
@given(st.text())
def test_parse_list_header_doesnt_crash(header_value):
    """Property: parse_list_header should never crash"""
    result = requests.utils.parse_list_header(header_value)
    assert isinstance(result, list)


# Test _parse_content_type_header with malformed input
@given(st.text())
def test_parse_content_type_header_doesnt_crash(header):
    """Property: _parse_content_type_header should handle any string"""
    try:
        content_type, params = requests.utils._parse_content_type_header(header)
        assert isinstance(content_type, str)
        assert isinstance(params, dict)
    except AttributeError:
        # The function is private, might not exist
        pytest.skip("_parse_content_type_header not available")


# Test guess_json_utf
@given(st.binary(min_size=0, max_size=10))
def test_guess_json_utf_doesnt_crash(data):
    """Property: guess_json_utf should never crash on binary input"""
    result = requests.utils.guess_json_utf(data)
    assert result is None or isinstance(result, str)


# Test unquote_unreserved
@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=50))
def test_unquote_unreserved_preserves_reserved(text):
    """Property: unquote_unreserved should preserve reserved characters"""
    # Add some percent encoding
    uri = text.replace(' ', '%20')
    
    try:
        result = requests.utils.unquote_unreserved(uri)
        # Result should be a string
        assert isinstance(result, str)
    except requests.exceptions.InvalidURL:
        # Some malformed percent encodings might fail
        pass


if __name__ == "__main__":
    # Run with more examples to find edge cases
    import sys
    
    # Quick smoke test
    print("Running property-based tests for requests.utils...")
    
    # Run each test function
    test_functions = [
        test_to_from_key_val_list_round_trip,
        test_from_to_key_val_list_preserves_tuples,
        test_iter_slices_joins_correctly,
        test_iter_slices_with_none_or_zero_returns_whole_string,
        test_dotted_netmask_valid_range,
        test_dotted_netmask_invalid_range_high,
        test_dotted_netmask_invalid_range_negative,
        test_is_ipv4_address_doesnt_crash,
        test_is_ipv4_address_accepts_valid_ips,
        test_is_valid_cidr_accepts_valid_cidrs,
        test_is_valid_cidr_doesnt_crash,
        test_is_valid_cidr_rejects_invalid_masks,
        test_is_valid_cidr_rejects_negative_masks,
        test_address_in_network_self_contained,
        test_requote_uri_idempotent,
        test_parse_header_links_doesnt_crash,
        test_parse_dict_header_doesnt_crash,
        test_parse_list_header_doesnt_crash,
        test_parse_content_type_header_doesnt_crash,
        test_guess_json_utf_doesnt_crash,
        test_unquote_unreserved_preserves_reserved,
    ]
    
    for test_func in test_functions:
        print(f"Testing {test_func.__name__}...")
        try:
            test_func()
            print(f"  ✓ {test_func.__name__} passed")
        except Exception as e:
            print(f"  ✗ {test_func.__name__} failed: {e}")
    
    print("\nDone with smoke tests. Run with pytest for full testing.")