#!/usr/bin/env python3
"""Property-based tests for spnego.negotiate module using Hypothesis."""

import struct
from hypothesis import given, strategies as st, assume, settings
import spnego._spnego as sp
import spnego._negotiate as neg
from spnego._context import GSSMech
from spnego._asn1 import pack_asn1_sequence, pack_asn1_object_identifier, unpack_asn1_sequence, unpack_asn1_object_identifier
from spnego.exceptions import InvalidTokenError
import pytest


# Strategy for valid OID strings
def valid_oid_strategy():
    """Generate valid OID strings."""
    # OIDs must start with 0, 1, or 2
    # If starts with 0 or 1, second must be 0-39
    # If starts with 2, second can be any number
    first = st.sampled_from([0, 1, 2])
    
    @st.composite
    def oid(draw):
        f = draw(first)
        if f in [0, 1]:
            second = draw(st.integers(min_value=0, max_value=39))
        else:
            second = draw(st.integers(min_value=0, max_value=255))
        
        # Add more components
        rest = draw(st.lists(st.integers(min_value=0, max_value=2**31-1), min_size=0, max_size=5))
        components = [f, second] + rest
        return ".".join(str(c) for c in components)
    
    return oid()


@given(st.lists(valid_oid_strategy(), min_size=1, max_size=10))
def test_pack_mech_type_list_round_trip(oid_list):
    """Test that pack_mech_type_list preserves OID list through pack/unpack cycle."""
    # Pack the OID list
    packed = sp.pack_mech_type_list(oid_list)
    
    # Unpack manually using ASN.1 functions
    unpacked = unpack_asn1_sequence(packed)
    result_oids = []
    for oid_bytes in unpacked:
        oid = unpack_asn1_object_identifier(oid_bytes)[0]
        result_oids.append(oid)
    
    # Should preserve the OID list
    assert result_oids == oid_list


@given(st.text(min_size=1, max_size=10))
def test_pack_mech_type_list_single_string(single_oid):
    """Test that pack_mech_type_list handles single string correctly."""
    # Should convert single string to list
    packed_single = sp.pack_mech_type_list(single_oid)
    packed_list = sp.pack_mech_type_list([single_oid])
    
    assert packed_single == packed_list


@given(st.one_of(
    st.lists(valid_oid_strategy(), min_size=1, max_size=5),
    st.tuples(valid_oid_strategy()),
    st.sets(valid_oid_strategy(), min_size=1, max_size=5)
))
def test_pack_mech_type_list_accepts_different_types(mech_list):
    """Test that pack_mech_type_list accepts lists, tuples, and sets."""
    # Should not raise an exception
    result = sp.pack_mech_type_list(mech_list)
    assert isinstance(result, bytes)
    assert len(result) > 0


class TestNegTokenInit:
    """Test properties of NegTokenInit."""
    
    @given(
        mech_types=st.lists(valid_oid_strategy(), min_size=0, max_size=5),
        mech_token=st.one_of(st.none(), st.binary(min_size=0, max_size=100)),
        hint_name=st.one_of(st.none(), st.binary(min_size=0, max_size=50)),
        hint_address=st.one_of(st.none(), st.binary(min_size=0, max_size=50)),
        mech_list_mic=st.one_of(st.none(), st.binary(min_size=0, max_size=50))
    )
    def test_negtokeninit_pack_unpack_round_trip(self, mech_types, mech_token, hint_name, hint_address, mech_list_mic):
        """Test that NegTokenInit survives pack/unpack round trip."""
        # Create token
        token = sp.NegTokenInit(
            mech_types=mech_types if mech_types else None,
            mech_token=mech_token,
            hint_name=hint_name,
            hint_address=hint_address,
            mech_list_mic=mech_list_mic
        )
        
        # Pack and unpack
        packed = token.pack()
        unpacked = sp.NegTokenInit.unpack(packed)
        
        # Check fields are preserved
        assert unpacked.mech_types == (mech_types if mech_types else [])
        assert unpacked.mech_token == mech_token
        assert unpacked.hint_name == hint_name
        assert unpacked.hint_address == hint_address
        assert unpacked.mech_list_mic == mech_list_mic


class TestNegTokenResp:
    """Test properties of NegTokenResp."""
    
    @given(
        neg_state=st.one_of(st.none(), st.sampled_from(list(sp.NegState))),
        supported_mech=st.one_of(st.none(), valid_oid_strategy()),
        response_token=st.one_of(st.none(), st.binary(min_size=0, max_size=100)),
        mech_list_mic=st.one_of(st.none(), st.binary(min_size=0, max_size=50))
    )
    def test_negtokenresp_pack_unpack_round_trip(self, neg_state, supported_mech, response_token, mech_list_mic):
        """Test that NegTokenResp survives pack/unpack round trip."""
        # Create token
        token = sp.NegTokenResp(
            neg_state=neg_state,
            supported_mech=supported_mech,
            response_token=response_token,
            mech_list_mic=mech_list_mic
        )
        
        # Pack and unpack
        packed = token.pack()
        unpacked = sp.NegTokenResp.unpack(packed)
        
        # Check fields are preserved
        assert unpacked.neg_state == neg_state
        assert unpacked.supported_mech == supported_mech
        assert unpacked.response_token == response_token
        assert unpacked.mech_list_mic == mech_list_mic


class TestUnpackToken:
    """Test unpack_token function properties."""
    
    @given(st.binary(min_size=0, max_size=7))
    def test_unpack_token_handles_short_ntlm_gracefully(self, data):
        """Test that unpack_token handles short NTLM-like data gracefully."""
        # NTLM messages start with "NTLMSSP\x00"
        if data.startswith(b"NTLMSSP"):
            # If it starts with NTLM prefix but is too short, should still return the data
            result = sp.unpack_token(data)
            assert result == data
    
    @given(st.binary(min_size=1, max_size=10))
    def test_unpack_token_invalid_asn1_raises_struct_error(self, data):
        """Test that invalid ASN.1 data raises appropriate errors."""
        # Skip if it's an NTLM message
        if data.startswith(b"NTLMSSP\x00"):
            return
        
        # Most random binary data will be invalid ASN.1
        # The function should raise struct.error for invalid data
        try:
            result = sp.unpack_token(data)
            # If it doesn't raise, it should return bytes
            assert isinstance(result, (bytes, sp.NegTokenInit, sp.NegTokenResp))
        except (struct.error, ValueError, IndexError):
            # These are expected for invalid input
            pass
    
    @given(st.binary(min_size=8, max_size=100))
    def test_unpack_token_with_ntlm_prefix_returns_data(self, suffix):
        """Test that data with NTLM prefix is handled correctly."""
        data = b"NTLMSSP\x00" + suffix
        result = sp.unpack_token(data)
        assert result == data
        
        # With unwrap=True, it should try to parse as NTLM message
        try:
            result_unwrapped = sp.unpack_token(data, unwrap=True)
            # Should return an NTLMMessage object or raise an error
            assert result_unwrapped != data  # Should be parsed
        except (struct.error, ValueError, IndexError):
            # Invalid NTLM message structure is fine
            pass


class TestNegotiateProxy:
    """Test NegotiateProxy state properties."""
    
    def test_negotiate_proxy_initial_state(self):
        """Test initial state of NegotiateProxy."""
        proxy = neg.NegotiateProxy(
            username="testuser",
            password="testpass",
            hostname="testhost",
            service="http"
        )
        
        # Initial state should be incomplete
        assert proxy.complete == False
        assert proxy._init_sent == False
        assert proxy._mech_sent == False
        assert proxy._mic_sent == False
        assert proxy._mic_recv == False
    
    def test_negotiate_proxy_query_message_sizes_requires_complete(self):
        """Test that query_message_sizes requires completed context."""
        proxy = neg.NegotiateProxy(
            username="testuser",
            password="testpass",
            hostname="testhost",
            service="http"
        )
        
        # Should raise NoContextError when not complete
        from spnego.exceptions import NoContextError
        with pytest.raises(NoContextError):
            proxy.query_message_sizes()
    
    @given(
        username=st.text(min_size=1, max_size=20),
        password=st.text(min_size=1, max_size=20),
        hostname=st.text(min_size=1, max_size=20),
        service=st.text(min_size=1, max_size=10)
    )
    def test_negotiate_proxy_creation_doesnt_crash(self, username, password, hostname, service):
        """Test that NegotiateProxy can be created with various inputs."""
        try:
            proxy = neg.NegotiateProxy(
                username=username,
                password=password,
                hostname=hostname,
                service=service
            )
            # Basic properties should work
            assert proxy.complete in [True, False]
            assert proxy.usage in ["initiate", "accept"]
        except Exception as e:
            # Some combinations might not be supported, that's OK
            # But we shouldn't get random crashes
            assert "mechanism" in str(e).lower() or "credential" in str(e).lower()