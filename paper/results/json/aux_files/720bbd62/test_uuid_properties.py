import uuid
import math
from hypothesis import given, strategies as st, assume, settings


# Strategy for valid 128-bit integers
valid_int = st.integers(min_value=0, max_value=(1 << 128) - 1)

# Strategy for valid 16-byte sequences
valid_bytes = st.binary(min_size=16, max_size=16)

# Strategy for valid hex strings (32 hex digits)
valid_hex = st.text(alphabet='0123456789abcdefABCDEF', min_size=32, max_size=32)

# Strategy for valid UUID fields tuple
valid_fields = st.tuples(
    st.integers(min_value=0, max_value=(1 << 32) - 1),  # time_low
    st.integers(min_value=0, max_value=(1 << 16) - 1),  # time_mid
    st.integers(min_value=0, max_value=(1 << 16) - 1),  # time_hi_version
    st.integers(min_value=0, max_value=(1 << 8) - 1),   # clock_seq_hi_variant
    st.integers(min_value=0, max_value=(1 << 8) - 1),   # clock_seq_low
    st.integers(min_value=0, max_value=(1 << 48) - 1),  # node
)


# Test 1: Round-trip property for int -> UUID -> int
@given(valid_int)
def test_uuid_int_round_trip(n):
    u = uuid.UUID(int=n)
    assert u.int == n


# Test 2: Round-trip property for bytes -> UUID -> bytes
@given(valid_bytes)
def test_uuid_bytes_round_trip(b):
    u = uuid.UUID(bytes=b)
    assert u.bytes == b


# Test 3: Round-trip property for bytes_le -> UUID -> bytes_le
@given(valid_bytes)
def test_uuid_bytes_le_round_trip(b):
    u = uuid.UUID(bytes_le=b)
    assert u.bytes_le == b


# Test 4: Round-trip property for fields -> UUID -> fields
@given(valid_fields)
def test_uuid_fields_round_trip(f):
    u = uuid.UUID(fields=f)
    assert u.fields == f


# Test 5: Round-trip property for hex -> UUID -> hex (normalized)
@given(valid_hex)
def test_uuid_hex_round_trip(h):
    u = uuid.UUID(hex=h)
    # UUID normalizes hex to lowercase with hyphens
    expected = h.lower()
    expected_formatted = f"{expected[:8]}-{expected[8:12]}-{expected[12:16]}-{expected[16:20]}-{expected[20:]}"
    assert str(u) == expected_formatted


# Test 6: bytes and bytes_le conversion consistency
@given(valid_bytes)
def test_bytes_bytes_le_conversion(b):
    u1 = uuid.UUID(bytes=b)
    u2 = uuid.UUID(bytes_le=u1.bytes_le)
    assert u1.int == u2.int
    assert u1.bytes == u2.bytes


# Test 7: UUID equality is reflexive, symmetric, and transitive
@given(valid_int)
def test_uuid_equality_properties(n):
    u1 = uuid.UUID(int=n)
    u2 = uuid.UUID(int=n)
    u3 = uuid.UUID(bytes=u1.bytes)
    
    # Reflexive
    assert u1 == u1
    
    # Symmetric
    assert u1 == u2
    assert u2 == u1
    
    # Transitive
    assert u1 == u2
    assert u2 == u3
    assert u1 == u3


# Test 8: UUID ordering consistency
@given(valid_int, valid_int)
def test_uuid_ordering_consistency(n1, n2):
    u1 = uuid.UUID(int=n1)
    u2 = uuid.UUID(int=n2)
    
    # Ordering should match integer ordering
    assert (u1 < u2) == (n1 < n2)
    assert (u1 <= u2) == (n1 <= n2)
    assert (u1 > u2) == (n1 > n2)
    assert (u1 >= u2) == (n1 >= n2)


# Test 9: UUID immutability
@given(valid_int)
def test_uuid_immutability(n):
    u = uuid.UUID(int=n)
    try:
        u.int = 42
        assert False, "UUID should be immutable"
    except (AttributeError, TypeError):
        pass  # Expected
    
    try:
        u.bytes = b'x' * 16
        assert False, "UUID should be immutable"
    except (AttributeError, TypeError):
        pass  # Expected


# Test 10: UUID hash consistency
@given(valid_int)
def test_uuid_hash_consistency(n):
    u1 = uuid.UUID(int=n)
    u2 = uuid.UUID(int=n)
    
    # Equal objects must have equal hashes
    assert hash(u1) == hash(u2)
    
    # Hash should be consistent across different construction methods
    u3 = uuid.UUID(bytes=u1.bytes)
    assert hash(u1) == hash(u3)


# Test 11: Version field constraints when version is set
@given(valid_int, st.integers(min_value=1, max_value=5))
def test_uuid_version_field_setting(n, version):
    u = uuid.UUID(int=n, version=version)
    
    # Check that version was set correctly
    assert u.version == version
    
    # Check that variant is RFC_4122
    assert u.variant == uuid.RFC_4122


# Test 12: Hex string with various valid formats
@given(valid_hex)
def test_uuid_hex_format_flexibility(h):
    # Test various formats that should all work
    base_hex = h.lower()
    formatted = f"{base_hex[:8]}-{base_hex[8:12]}-{base_hex[12:16]}-{base_hex[16:20]}-{base_hex[20:]}"
    
    # All these should produce the same UUID
    u1 = uuid.UUID(hex=base_hex)
    u2 = uuid.UUID(hex=formatted)
    u3 = uuid.UUID(hex='{' + formatted + '}')
    u4 = uuid.UUID(hex='urn:uuid:' + formatted)
    
    assert u1.int == u2.int == u3.int == u4.int


# Test 13: Fields to int and back conversion
@given(valid_fields)
def test_fields_to_int_conversion(fields):
    time_low, time_mid, time_hi_version, clock_seq_hi_variant, clock_seq_low, node = fields
    
    # Create UUID from fields
    u = uuid.UUID(fields=fields)
    
    # Manually compute what the int should be
    clock_seq = (clock_seq_hi_variant << 8) | clock_seq_low
    expected_int = ((time_low << 96) | (time_mid << 80) | 
                    (time_hi_version << 64) | (clock_seq << 48) | node)
    
    assert u.int == expected_int


# Test 14: bytes_le endianness property
@given(valid_bytes)
def test_bytes_le_endianness(b):
    u = uuid.UUID(bytes=b)
    
    # bytes_le should swap the endianness of the first three fields
    bytes_le = u.bytes_le
    
    # Check the byte swapping
    assert bytes_le[0:4] == b[3::-1]  # time_low reversed
    assert bytes_le[4:6] == b[5:3:-1]  # time_mid reversed
    assert bytes_le[6:8] == b[7:5:-1]  # time_hi_version reversed
    assert bytes_le[8:] == b[8:]  # rest unchanged


# Test 15: UUID string representation format
@given(valid_int)
def test_uuid_string_format(n):
    u = uuid.UUID(int=n)
    s = str(u)
    
    # Check format: 8-4-4-4-12 hexadecimal digits with hyphens
    parts = s.split('-')
    assert len(parts) == 5
    assert len(parts[0]) == 8
    assert len(parts[1]) == 4
    assert len(parts[2]) == 4
    assert len(parts[3]) == 4
    assert len(parts[4]) == 12
    
    # All characters should be lowercase hex
    assert all(c in '0123456789abcdef-' for c in s)
    
    # Reconstructing from string should give same UUID
    u2 = uuid.UUID(s)
    assert u.int == u2.int


# Test 16: URN format property
@given(valid_int)
def test_uuid_urn_format(n):
    u = uuid.UUID(int=n)
    urn = u.urn
    
    # URN should start with 'urn:uuid:'
    assert urn.startswith('urn:uuid:')
    
    # The rest should be the UUID string
    assert urn[9:] == str(u)
    
    # Should be able to create UUID from URN
    u2 = uuid.UUID(urn)
    assert u.int == u2.int


# Test 17: Individual field accessors consistency
@given(valid_fields)
def test_field_accessors(fields):
    u = uuid.UUID(fields=fields)
    time_low, time_mid, time_hi_version, clock_seq_hi_variant, clock_seq_low, node = fields
    
    assert u.time_low == time_low
    assert u.time_mid == time_mid
    assert u.time_hi_version == time_hi_version
    assert u.clock_seq_hi_variant == clock_seq_hi_variant
    assert u.clock_seq_low == clock_seq_low
    assert u.node == node
    
    # Derived fields
    clock_seq = (clock_seq_hi_variant << 8) | clock_seq_low
    assert u.clock_seq == clock_seq


# Test 18: Zero UUID edge case
def test_zero_uuid():
    u = uuid.UUID(int=0)
    assert u.int == 0
    assert u.bytes == b'\x00' * 16
    assert u.hex == '00000000000000000000000000000000'
    assert str(u) == '00000000-0000-0000-0000-000000000000'


# Test 19: Max UUID edge case
def test_max_uuid():
    max_val = (1 << 128) - 1
    u = uuid.UUID(int=max_val)
    assert u.int == max_val
    assert u.bytes == b'\xff' * 16
    assert u.hex == 'f' * 32
    assert str(u) == 'ffffffff-ffff-ffff-ffff-ffffffffffff'


# Test 20: bytes and int relationship
@given(valid_bytes)
def test_bytes_int_relationship(b):
    u = uuid.UUID(bytes=b)
    # bytes should be big-endian representation of int
    expected_int = int.from_bytes(b, byteorder='big')
    assert u.int == expected_int
    
    # Converting back should give same bytes
    assert u.int.to_bytes(16, byteorder='big') == b


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])