#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

import struct
from hypothesis import given, strategies as st, assume, settings
import spnego
from spnego.channel_bindings import GssChannelBindings, AddressType, _pack_value, _unpack_value
from spnego._context import split_username
from spnego._credential import Password, NTLMHash, KerberosKeytab, KerberosCCache, CredentialCache


# Strategy for valid AddressType enum values
address_type_strategy = st.sampled_from(list(AddressType))

# Strategy for optional bytes
optional_bytes_strategy = st.one_of(st.none(), st.binary(min_size=0, max_size=1000))


@given(
    initiator_addrtype=address_type_strategy,
    initiator_address=optional_bytes_strategy,
    acceptor_addrtype=address_type_strategy,
    acceptor_address=optional_bytes_strategy,
    application_data=optional_bytes_strategy
)
def test_gss_channel_bindings_pack_unpack_round_trip(
    initiator_addrtype, initiator_address, acceptor_addrtype, acceptor_address, application_data
):
    """Test that GssChannelBindings.unpack(pack(x)) == x"""
    # Create original binding
    original = GssChannelBindings(
        initiator_addrtype=initiator_addrtype,
        initiator_address=initiator_address,
        acceptor_addrtype=acceptor_addrtype,
        acceptor_address=acceptor_address,
        application_data=application_data
    )
    
    # Pack and unpack
    packed = original.pack()
    unpacked = GssChannelBindings.unpack(packed)
    
    # Verify round-trip
    assert unpacked.initiator_addrtype == original.initiator_addrtype
    assert unpacked.initiator_address == original.initiator_address
    assert unpacked.acceptor_addrtype == original.acceptor_addrtype
    assert unpacked.acceptor_address == original.acceptor_address
    assert unpacked.application_data == original.application_data
    
    # Also test equality operator
    assert unpacked == original


@given(
    initiator_addrtype=address_type_strategy,
    initiator_address=optional_bytes_strategy,
    acceptor_addrtype=address_type_strategy,
    acceptor_address=optional_bytes_strategy,
    application_data=optional_bytes_strategy
)
def test_gss_channel_bindings_equality_symmetry(
    initiator_addrtype, initiator_address, acceptor_addrtype, acceptor_address, application_data
):
    """Test that GssChannelBindings equality is symmetric with packed bytes"""
    binding = GssChannelBindings(
        initiator_addrtype=initiator_addrtype,
        initiator_address=initiator_address,
        acceptor_addrtype=acceptor_addrtype,
        acceptor_address=acceptor_address,
        application_data=application_data
    )
    
    packed = binding.pack()
    
    # Test equality both ways
    assert binding == packed
    assert binding == binding
    
    # Create another identical binding
    binding2 = GssChannelBindings(
        initiator_addrtype=initiator_addrtype,
        initiator_address=initiator_address,
        acceptor_addrtype=acceptor_addrtype,
        acceptor_address=acceptor_address,
        application_data=application_data
    )
    
    assert binding == binding2


@given(username=st.text(min_size=0, max_size=100))
def test_split_username_without_domain(username):
    """Test split_username for usernames without domain"""
    # Skip usernames that contain backslash
    assume('\\' not in username)
    
    domain, user = split_username(username)
    
    # Without backslash, domain should be None and username should be unchanged
    assert domain is None
    assert user == username


@given(
    domain=st.text(min_size=0, max_size=50).filter(lambda x: '\\' not in x),
    username=st.text(min_size=0, max_size=50).filter(lambda x: '\\' not in x)
)
def test_split_username_with_domain(domain, username):
    """Test split_username for DOMAIN\\username format"""
    full_username = f"{domain}\\{username}"
    
    result_domain, result_user = split_username(full_username)
    
    assert result_domain == domain
    assert result_user == username


@given(username=st.text(min_size=1, max_size=100))
def test_split_username_multiple_backslashes(username):
    """Test that split_username only splits on first backslash"""
    # Create username with multiple backslashes
    assume('\\' not in username)
    
    test_username = f"DOMAIN\\{username}\\extra"
    domain, user = split_username(test_username)
    
    assert domain == "DOMAIN"
    assert user == f"{username}\\extra"


def test_split_username_none():
    """Test split_username with None input"""
    domain, user = split_username(None)
    assert domain is None
    assert user is None


@given(
    addr_type=st.one_of(st.none(), address_type_strategy),
    data=optional_bytes_strategy
)
def test_pack_unpack_value_round_trip(addr_type, data):
    """Test internal _pack_value and _unpack_value functions"""
    packed = _pack_value(addr_type, data)
    
    # For unpacking, we need to handle the address type separately
    # since _unpack_value only unpacks the length and data part
    offset = 0
    if addr_type is not None:
        offset = 4  # Skip the address type bytes
    
    unpacked_data, new_offset = _unpack_value(memoryview(packed), offset)
    
    expected_data = data if data is not None else b""
    assert unpacked_data == expected_data


@given(value=st.sampled_from(list(AddressType)))
def test_address_type_enum_consistency(value):
    """Test that AddressType enum values are preserved correctly"""
    # Test that we can create an AddressType from its value
    recreated = AddressType(value.value)
    assert recreated == value
    assert recreated.value == value.value
    assert recreated.name == value.name


@given(
    username=st.text(min_size=1, max_size=50),
    password=st.text(min_size=0, max_size=50)
)
def test_password_credential_properties(username, password):
    """Test Password credential has correct supported protocols"""
    cred = Password(username=username, password=password)
    
    # According to the code, Password supports these protocols
    assert cred.supported_protocols == ["credssp", "kerberos", "ntlm"]
    assert cred.username == username
    assert cred.password == password


@given(
    username=st.text(min_size=1, max_size=50),
    lm_hash=st.one_of(st.none(), st.from_regex(r'^[0-9A-Fa-f]{32}$', fullmatch=True)),
    nt_hash=st.one_of(st.none(), st.from_regex(r'^[0-9A-Fa-f]{32}$', fullmatch=True))
)
def test_ntlm_hash_credential_properties(username, lm_hash, nt_hash):
    """Test NTLMHash credential has correct supported protocols"""
    cred = NTLMHash(username=username, lm_hash=lm_hash, nt_hash=nt_hash)
    
    # According to the code, NTLMHash only supports ntlm
    assert cred.supported_protocols == ["ntlm"]
    assert cred.username == username
    assert cred.lm_hash == lm_hash
    assert cred.nt_hash == nt_hash


@given(
    keytab=st.text(min_size=1, max_size=100),
    principal=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_kerberos_keytab_credential_properties(keytab, principal):
    """Test KerberosKeytab credential has correct supported protocols"""
    cred = KerberosKeytab(keytab=keytab, principal=principal)
    
    # According to the code, KerberosKeytab only supports kerberos
    assert cred.supported_protocols == ["kerberos"]
    assert cred.keytab == keytab
    assert cred.principal == principal


@given(
    ccache=st.text(min_size=1, max_size=100),
    principal=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_kerberos_ccache_credential_properties(ccache, principal):
    """Test KerberosCCache credential has correct supported protocols"""
    cred = KerberosCCache(ccache=ccache, principal=principal)
    
    # According to the code, KerberosCCache only supports kerberos
    assert cred.supported_protocols == ["kerberos"]
    assert cred.ccache == ccache
    assert cred.principal == principal


@given(username=st.one_of(st.none(), st.text(min_size=1, max_size=50)))
def test_credential_cache_properties(username):
    """Test CredentialCache has correct supported protocols"""
    cred = CredentialCache(username=username)
    
    # According to the code, CredentialCache supports kerberos and ntlm
    assert cred.supported_protocols == ["kerberos", "ntlm"]
    assert cred.username == username


if __name__ == "__main__":
    # Run all tests
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])