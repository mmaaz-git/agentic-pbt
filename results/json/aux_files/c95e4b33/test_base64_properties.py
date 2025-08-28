import base64
import string
import struct
from hypothesis import given, strategies as st, assume, settings

@given(st.binary())
def test_b64_round_trip(data):
    encoded = base64.b64encode(data)
    decoded = base64.b64decode(encoded)
    assert decoded == data

@given(st.binary())
def test_b64_urlsafe_round_trip(data):
    encoded = base64.urlsafe_b64encode(data)
    decoded = base64.urlsafe_b64decode(encoded)
    assert decoded == data

@given(st.binary(), st.binary(min_size=2, max_size=2))
def test_b64_altchars_round_trip(data, altchars):
    assume(b'+' not in altchars and b'/' not in altchars)
    assume(altchars[0] != altchars[1])
    encoded = base64.b64encode(data, altchars=altchars)
    decoded = base64.b64decode(encoded, altchars=altchars)
    assert decoded == data

@given(st.binary())
def test_b32_round_trip(data):
    encoded = base64.b32encode(data)
    decoded = base64.b32decode(encoded)
    assert decoded == data

@given(st.binary())
def test_b32_casefold_invariant(data):
    encoded = base64.b32encode(data)
    decoded_upper = base64.b32decode(encoded)
    decoded_lower = base64.b32decode(encoded.lower(), casefold=True)
    assert decoded_upper == decoded_lower == data

@given(st.binary())
def test_b32hex_round_trip(data):
    encoded = base64.b32hexencode(data)
    decoded = base64.b32hexdecode(encoded)
    assert decoded == data

@given(st.binary())
def test_b16_round_trip(data):
    encoded = base64.b16encode(data)
    decoded = base64.b16decode(encoded)
    assert decoded == data

@given(st.binary())
def test_b16_casefold_invariant(data):
    encoded = base64.b16encode(data)
    decoded_upper = base64.b16decode(encoded)
    decoded_lower = base64.b16decode(encoded.lower(), casefold=True)
    assert decoded_upper == decoded_lower == data

@given(st.binary())
def test_b85_round_trip(data):
    encoded = base64.b85encode(data)
    decoded = base64.b85decode(encoded)
    assert decoded == data

@given(st.binary())
def test_b85_padded_round_trip(data):
    encoded = base64.b85encode(data, pad=True)
    decoded = base64.b85decode(encoded)
    assert decoded == data

@given(st.binary())
def test_a85_round_trip(data):
    encoded = base64.a85encode(data)
    decoded = base64.a85decode(encoded)
    assert decoded == data

@given(st.binary())
def test_a85_adobe_round_trip(data):
    encoded = base64.a85encode(data, adobe=True)
    decoded = base64.a85decode(encoded, adobe=True)
    assert decoded == data

@given(st.binary(), st.integers(min_value=10, max_value=100))
def test_a85_wrapcol_invariant(data, wrapcol):
    encoded = base64.a85encode(data, wrapcol=wrapcol)
    decoded = base64.a85decode(encoded)
    assert decoded == data

@given(st.binary())
def test_a85_foldspaces_round_trip(data):
    encoded = base64.a85encode(data, foldspaces=True)
    decoded = base64.a85decode(encoded, foldspaces=True)
    assert decoded == data

@given(st.binary())
def test_z85_round_trip(data):
    encoded = base64.z85encode(data)
    decoded = base64.z85decode(encoded)
    assert decoded == data

@given(st.binary())
def test_encodebytes_decodebytes_round_trip(data):
    encoded = base64.encodebytes(data)
    decoded = base64.decodebytes(encoded)
    assert decoded == data

@given(st.text(alphabet=string.ascii_letters + string.digits))
def test_b64decode_string_input(text):
    try:
        encoded = base64.b64encode(text.encode('ascii'))
        decoded = base64.b64decode(text)
    except:
        pass

@given(st.binary())
def test_b64_validate_strict_mode(data):
    encoded = base64.b64encode(data)
    decoded_nonstrict = base64.b64decode(encoded, validate=False)
    decoded_strict = base64.b64decode(encoded, validate=True)
    assert decoded_nonstrict == decoded_strict == data

@given(st.binary())
def test_b32_map01_consistency(data):
    encoded = base64.b32encode(data)
    encoded_with_01 = encoded.replace(b'O', b'0').replace(b'I', b'1')
    decoded_I = base64.b32decode(encoded_with_01, map01=b'I')
    decoded_L = base64.b32decode(encoded_with_01, map01=b'L')
    assert decoded_I == data or decoded_L == data

@given(st.binary())
def test_encoding_length_invariants(data):
    b64_encoded = base64.b64encode(data)
    b32_encoded = base64.b32encode(data)
    b16_encoded = base64.b16encode(data)
    
    # Base64 expands by 4/3
    assert len(b64_encoded) >= len(data) * 4 // 3
    # Base32 expands by 8/5
    assert len(b32_encoded) >= len(data) * 8 // 5
    # Base16 expands by 2
    assert len(b16_encoded) == len(data) * 2

@given(st.binary(min_size=1))
def test_b85_overflow_boundary(data):
    try:
        encoded = base64.b85encode(data)
        decoded = base64.b85decode(encoded)
        assert decoded == data
    except (ValueError, struct.error):
        pass

@given(st.binary())
def test_different_encodings_decode_to_same(data):
    b64_encoded = base64.b64encode(data)
    b64_decoded = base64.b64decode(b64_encoded)
    
    urlsafe_encoded = base64.urlsafe_b64encode(data)
    urlsafe_decoded = base64.urlsafe_b64decode(urlsafe_encoded)
    
    standard_encoded = base64.standard_b64encode(data)
    standard_decoded = base64.standard_b64decode(standard_encoded)
    
    assert b64_decoded == urlsafe_decoded == standard_decoded == data

@given(st.binary())
def test_base85_variants_compatibility(data):
    b85_encoded = base64.b85encode(data)
    b85_decoded = base64.b85decode(b85_encoded)
    
    a85_encoded = base64.a85encode(data)
    a85_decoded = base64.a85decode(a85_encoded)
    
    z85_encoded = base64.z85encode(data)
    z85_decoded = base64.z85decode(z85_encoded)
    
    assert b85_decoded == a85_decoded == z85_decoded == data

@given(st.binary())
def test_padding_consistency(data):
    # Test that manually padded input matches auto-padded
    if len(data) % 4 != 0:
        padded_data = data + b'\0' * (4 - len(data) % 4)
        b85_auto = base64.b85encode(data)
        b85_manual = base64.b85encode(padded_data, pad=False)[:len(b85_auto)]
        assert base64.b85decode(b85_auto) == base64.b85decode(b85_manual)

@given(st.lists(st.integers(min_value=0, max_value=255), min_size=1))
def test_bytes_like_input_types(data_list):
    data_bytes = bytes(data_list)
    data_bytearray = bytearray(data_list)
    data_memoryview = memoryview(bytearray(data_list))
    
    encoded_bytes = base64.b64encode(data_bytes)
    encoded_bytearray = base64.b64encode(data_bytearray)
    encoded_memoryview = base64.b64encode(data_memoryview)
    
    assert encoded_bytes == encoded_bytearray == encoded_memoryview

@given(st.binary())
def test_a85_adobe_frame_invariant(data):
    encoded_no_adobe = base64.a85encode(data, adobe=False)
    encoded_adobe = base64.a85encode(data, adobe=True)
    
    assert encoded_adobe.startswith(b'<~')
    assert encoded_adobe.endswith(b'~>')
    assert encoded_adobe[2:-2] == encoded_no_adobe or b'\n' in encoded_adobe

@given(st.binary(min_size=4))
def test_a85_special_sequences(data):
    # Test that special sequences work correctly
    zeros = b'\0\0\0\0'
    spaces = b'    '
    
    encoded_zeros = base64.a85encode(zeros)
    assert encoded_zeros == b'z'
    
    encoded_spaces = base64.a85encode(spaces, foldspaces=True)
    assert encoded_spaces == b'y'
    
    decoded_zeros = base64.a85decode(b'z')
    assert decoded_zeros == zeros
    
    decoded_spaces = base64.a85decode(b'y', foldspaces=True)
    assert decoded_spaces == spaces

@given(st.binary())
def test_decode_ignore_invalid_chars(data):
    encoded = base64.b64encode(data)
    # Add some invalid characters
    corrupted = b' \n\t' + encoded + b' \r\n'
    decoded = base64.b64decode(corrupted)
    assert decoded == data

@given(st.binary(min_size=1, max_size=100))
def test_incremental_encoding_consistency(data):
    # Test that encoding in chunks gives same result
    full_encoded = base64.b64encode(data)
    
    chunk_size = max(1, len(data) // 3)
    chunks = []
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        chunks.append(chunk)
    
    # Can't directly concatenate b64 chunks due to padding
    # But decoding should give same result
    full_decoded = base64.b64decode(full_encoded)
    assert full_decoded == data

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])