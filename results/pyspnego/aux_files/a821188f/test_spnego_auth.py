"""Property-based tests for spnego.auth module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import spnego.auth
from spnego.channel_bindings import GssChannelBindings, AddressType
from spnego._credential import (
    Password, CredentialCache, NTLMHash, KerberosCCache, 
    KerberosKeytab, unify_credentials, Credential
)
from spnego.exceptions import InvalidCredentialError, NoCredentialError


# Strategy for AddressType enum values
address_type_strategy = st.sampled_from(list(AddressType))

# Strategy for optional bytes (including None)
optional_bytes_strategy = st.one_of(st.none(), st.binary(min_size=0, max_size=1000))

# Strategy for GssChannelBindings
@st.composite
def channel_bindings_strategy(draw):
    return GssChannelBindings(
        initiator_addrtype=draw(address_type_strategy),
        initiator_address=draw(optional_bytes_strategy),
        acceptor_addrtype=draw(address_type_strategy),
        acceptor_address=draw(optional_bytes_strategy),
        application_data=draw(optional_bytes_strategy)
    )


# Test 1: GssChannelBindings pack/unpack round-trip
@given(channel_bindings_strategy())
@settings(max_examples=1000)
def test_channel_bindings_pack_unpack_round_trip(bindings):
    """Test that unpacking a packed GssChannelBindings returns the original."""
    packed = bindings.pack()
    unpacked = GssChannelBindings.unpack(packed)
    
    # The unpacked object should be equal to the original
    assert unpacked == bindings
    assert unpacked.initiator_addrtype == bindings.initiator_addrtype
    assert unpacked.initiator_address == bindings.initiator_address
    assert unpacked.acceptor_addrtype == bindings.acceptor_addrtype
    assert unpacked.acceptor_address == bindings.acceptor_address
    assert unpacked.application_data == bindings.application_data


# Test 2: GssChannelBindings pack is deterministic
@given(channel_bindings_strategy())
def test_channel_bindings_pack_deterministic(bindings):
    """Test that packing the same bindings twice gives the same result."""
    pack1 = bindings.pack()
    pack2 = bindings.pack()
    assert pack1 == pack2


# Strategy for valid credential objects
@st.composite
def credential_strategy(draw):
    cred_type = draw(st.sampled_from(['Password', 'CredentialCache', 'NTLMHash', 'KerberosCCache', 'KerberosKeytab']))
    
    if cred_type == 'Password':
        return Password(
            username=draw(st.text(min_size=1, max_size=50)),
            password=draw(st.text(min_size=1, max_size=50))
        )
    elif cred_type == 'CredentialCache':
        username = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
        return CredentialCache(username=username)
    elif cred_type == 'NTLMHash':
        # Generate valid hex strings for hashes
        hex_chars = '0123456789abcdefABCDEF'
        nt_hash = draw(st.text(alphabet=hex_chars, min_size=32, max_size=32))
        lm_hash = draw(st.one_of(st.none(), st.text(alphabet=hex_chars, min_size=32, max_size=32)))
        return NTLMHash(
            username=draw(st.text(min_size=1, max_size=50)),
            nt_hash=nt_hash,
            lm_hash=lm_hash
        )
    elif cred_type == 'KerberosCCache':
        ccache_type = draw(st.sampled_from(['FILE', 'MEMORY', 'DIR']))
        path = draw(st.text(min_size=1, max_size=100))
        ccache = f"{ccache_type}:{path}"
        principal = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
        return KerberosCCache(ccache=ccache, principal=principal)
    else:  # KerberosKeytab
        keytab_type = draw(st.sampled_from(['FILE', 'MEMORY']))
        path = draw(st.text(min_size=1, max_size=100))
        keytab = f"{keytab_type}:{path}"
        principal = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
        return KerberosKeytab(keytab=keytab, principal=principal)


# Test 3: unify_credentials never returns empty list
@given(
    username=st.one_of(
        st.none(),
        st.text(min_size=1),
        credential_strategy(),
        st.lists(credential_strategy(), min_size=0, max_size=10)
    ),
    password=st.one_of(st.none(), st.text())
)
def test_unify_credentials_never_empty(username, password):
    """Test that unify_credentials never returns an empty list."""
    try:
        result = unify_credentials(username, password)
        assert len(result) > 0, "unify_credentials returned empty list"
        assert all(isinstance(cred, (Password, CredentialCache, NTLMHash, KerberosCCache, KerberosKeytab)) 
                   for cred in result), "Invalid credential type in result"
    except (InvalidCredentialError, NoCredentialError):
        # These are expected errors for invalid inputs
        pass


# Test 4: unify_credentials filtering property
@given(st.lists(credential_strategy(), min_size=1, max_size=20))
def test_unify_credentials_filtering(creds_list):
    """Test that unify_credentials filters duplicates as documented."""
    result = unify_credentials(creds_list)
    
    # Result length should be <= input length (filtering removes duplicates)
    assert len(result) <= len(creds_list)
    
    # All results should be valid Credential types
    assert all(isinstance(cred, (Password, CredentialCache, NTLMHash, KerberosCCache, KerberosKeytab)) 
               for cred in result)
    
    # Result should not be empty (since we provided non-empty input)
    assert len(result) > 0


# Test 5: unify_credentials with string username and password creates Password credential
@given(
    username=st.text(min_size=1, max_size=50),
    password=st.text(min_size=1, max_size=50)
)
def test_unify_credentials_string_to_password(username, password):
    """Test that string username + password creates a Password credential."""
    # Skip NTLM hash patterns (32 hex chars separated by colon)
    assume(not (len(password) == 65 and ':' in password and 
                all(c in '0123456789abcdefABCDEF:' for c in password)))
    
    result = unify_credentials(username, password)
    assert len(result) == 1
    assert isinstance(result[0], Password)
    assert result[0].username == username
    assert result[0].password == password


# Test 6: Protocol validation in client function  
@given(
    protocol=st.text(min_size=1, max_size=50),
    username=st.one_of(st.none(), st.text(min_size=1)),
    password=st.one_of(st.none(), st.text())
)
def test_client_protocol_validation(protocol, username, password):
    """Test that invalid protocols raise ValueError as documented."""
    valid_protocols = {'ntlm', 'kerberos', 'negotiate', 'credssp'}
    
    if protocol.lower() not in valid_protocols:
        with pytest.raises(ValueError) as exc_info:
            spnego.auth.client(username=username, password=password, protocol=protocol)
        assert "Invalid protocol specified" in str(exc_info.value)


# Test 7: Server function protocol validation
@given(
    protocol=st.text(min_size=1, max_size=50)
)
def test_server_protocol_validation(protocol):
    """Test that server function validates protocols."""
    valid_protocols = {'ntlm', 'kerberos', 'negotiate', 'credssp'}
    
    if protocol.lower() not in valid_protocols:
        with pytest.raises(ValueError) as exc_info:
            spnego.auth.server(protocol=protocol)
        assert "Invalid protocol specified" in str(exc_info.value)


# Test 8: unify_credentials idempotence for Credential lists
@given(st.lists(credential_strategy(), min_size=1, max_size=10))
def test_unify_credentials_idempotent_for_credentials(creds):
    """Test that running unify_credentials on its output gives the same result."""
    result1 = unify_credentials(creds)
    result2 = unify_credentials(result1)
    
    # Should get the same credential list
    assert len(result1) == len(result2)
    # Note: We can't directly compare the lists because the objects might be different instances
    # but we can check the types and key properties match
    for r1, r2 in zip(result1, result2):
        assert type(r1) == type(r2)
        assert r1.supported_protocols == r2.supported_protocols


# Test 9: Channel bindings equality is reflexive  
@given(channel_bindings_strategy())
def test_channel_bindings_equality_reflexive(bindings):
    """Test that a channel binding equals itself."""
    assert bindings == bindings
    assert bindings == bindings.pack()
    

# Test 10: unify_credentials with required_protocol
@given(
    creds=st.lists(credential_strategy(), min_size=1, max_size=5),
    required_protocol=st.sampled_from(['ntlm', 'kerberos', 'credssp'])
)
def test_unify_credentials_required_protocol(creds, required_protocol):
    """Test that required_protocol validation works correctly."""
    try:
        result = unify_credentials(creds, required_protocol=required_protocol)
        # If successful, at least one credential should support the protocol
        supported_protocols = set()
        for cred in result:
            supported_protocols.update(cred.supported_protocols)
        assert required_protocol in supported_protocols
    except NoCredentialError as e:
        # This is expected if no credential supports the required protocol
        assert f"A credential for {required_protocol} is needed" in str(e)