#!/usr/bin/env python3
import sys
import struct
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings
import spnego.channel_bindings as cb


# Strategy for valid AddressType values
address_type_strategy = st.sampled_from(list(cb.AddressType))

# Strategy for optional bytes
optional_bytes_strategy = st.one_of(st.none(), st.binary(max_size=1024))

# Strategy for creating GssChannelBindings objects
gss_channel_bindings_strategy = st.builds(
    cb.GssChannelBindings,
    initiator_addrtype=address_type_strategy,
    initiator_address=optional_bytes_strategy,
    acceptor_addrtype=address_type_strategy,
    acceptor_address=optional_bytes_strategy,
    application_data=optional_bytes_strategy,
)


@given(gss_channel_bindings_strategy)
def test_pack_unpack_round_trip(obj):
    """Test that pack and unpack are inverse operations."""
    packed = obj.pack()
    unpacked = cb.GssChannelBindings.unpack(packed)
    
    # Check that all fields are preserved
    assert unpacked.initiator_addrtype == obj.initiator_addrtype
    assert unpacked.initiator_address == obj.initiator_address
    assert unpacked.acceptor_addrtype == obj.acceptor_addrtype
    assert unpacked.acceptor_address == obj.acceptor_address
    assert unpacked.application_data == obj.application_data
    
    # Check that the packed representation is the same
    assert unpacked.pack() == packed


@given(gss_channel_bindings_strategy)
def test_equality_with_packed_bytes(obj):
    """Test that an object equals its packed representation."""
    packed = obj.pack()
    assert obj == packed
    assert obj == obj  # Self-equality


@given(gss_channel_bindings_strategy, gss_channel_bindings_strategy)
def test_equality_transitivity(obj1, obj2):
    """Test transitivity of equality."""
    if obj1 == obj2:
        # If two objects are equal, their packed representations should be equal
        assert obj1.pack() == obj2.pack()
        
        # Create a third object from obj1's packed representation
        obj3 = cb.GssChannelBindings.unpack(obj1.pack())
        assert obj1 == obj3
        assert obj2 == obj3  # Transitivity


@given(
    addr_type=st.one_of(st.none(), address_type_strategy),
    data=optional_bytes_strategy
)
def test_pack_unpack_value_round_trip(addr_type, data):
    """Test that _pack_value and _unpack_value are inverse operations."""
    packed = cb._pack_value(addr_type, data)
    
    # Calculate expected offset after unpacking
    if addr_type is not None:
        # When addr_type is provided, we have 4 bytes for type + 4 bytes for length + data
        offset = 4
    else:
        # When addr_type is None, we only have 4 bytes for length + data
        offset = 0
    
    # Create a memoryview from the packed data
    b_mem = memoryview(packed)
    
    # Unpack the value (skip the addr_type part if present)
    unpacked_data, new_offset = cb._unpack_value(b_mem, offset)
    
    # Check that the data is preserved
    expected_data = data if data is not None else b""
    assert unpacked_data == expected_data
    
    # Check that the new offset is correct
    expected_offset = offset + 4 + len(expected_data)
    assert new_offset == expected_offset


@given(gss_channel_bindings_strategy)
def test_repr_and_str_dont_crash(obj):
    """Test that repr and str methods don't crash."""
    repr_str = repr(obj)
    str_str = str(obj)
    assert isinstance(repr_str, str)
    assert isinstance(str_str, str)
    assert len(repr_str) > 0
    assert len(str_str) > 0


@given(st.integers(min_value=0, max_value=255))
def test_address_type_construction(value):
    """Test that AddressType can be constructed from valid integer values."""
    try:
        addr_type = cb.AddressType(value)
        # If construction succeeds, the value should be preserved
        assert int(addr_type) == value
    except ValueError:
        # Some values might not be valid AddressType enum values
        # Check that invalid values are not in the enum
        assert value not in [e.value for e in cb.AddressType]


@given(gss_channel_bindings_strategy)
def test_pack_deterministic(obj):
    """Test that pack() is deterministic - same object always packs to same bytes."""
    packed1 = obj.pack()
    packed2 = obj.pack()
    assert packed1 == packed2


@given(st.binary(min_size=20))
def test_unpack_pack_round_trip_from_bytes(packed_bytes):
    """Test unpacking arbitrary valid-sized byte strings and repacking them."""
    # We need at least 20 bytes for a minimal structure:
    # 4 (initiator_addrtype) + 4 (initiator_address length) + 
    # 4 (acceptor_addrtype) + 4 (acceptor_address length) + 
    # 4 (application_data length)
    
    try:
        obj = cb.GssChannelBindings.unpack(packed_bytes)
        repacked = obj.pack()
        
        # The repacked version might be different if the original had padding
        # But unpacking the repacked version should give the same object
        obj2 = cb.GssChannelBindings.unpack(repacked)
        assert obj == obj2
    except (struct.error, IndexError, ValueError):
        # Some byte strings might not be valid channel bindings structures
        pass


if __name__ == "__main__":
    # Run tests with pytest
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])