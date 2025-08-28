import json
import json.encoder
import math
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import pytest


@composite
def json_serializable(draw):
    """Generate JSON serializable objects"""
    return draw(st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(min_value=-10**308, max_value=10**308),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text()
        ),
        lambda children: st.one_of(
            st.lists(children),
            st.dictionaries(st.text(), children)
        ),
        max_leaves=100
    ))


@given(json_serializable())
def test_round_trip_basic(obj):
    """Test that json.dumps and json.loads are inverse operations"""
    encoded = json.dumps(obj)
    decoded = json.loads(encoded)
    assert decoded == obj


@given(st.text())
def test_string_encoding_escapes(s):
    """Test that string encoding properly escapes special characters"""
    encoder = json.encoder.JSONEncoder(ensure_ascii=False)
    encoded = encoder.encode(s)
    
    # Should start and end with quotes
    assert encoded.startswith('"')
    assert encoded.endswith('"')
    
    # Should properly escape quotes and backslashes
    if '"' in s:
        assert '\\"' in encoded or encoded == '"\\"' * s.count('"') + '"'
    
    # Decode should recover original string
    decoded = json.loads(encoded)
    assert decoded == s


@given(st.text())
def test_ascii_encoding_consistency(s):
    """Test consistency between ASCII and non-ASCII encoding"""
    ascii_encoder = json.encoder.JSONEncoder(ensure_ascii=True)
    non_ascii_encoder = json.encoder.JSONEncoder(ensure_ascii=False)
    
    ascii_encoded = ascii_encoder.encode(s)
    non_ascii_encoded = non_ascii_encoder.encode(s)
    
    # Both should decode to the same value
    assert json.loads(ascii_encoded) == json.loads(non_ascii_encoded) == s


@given(
    st.dictionaries(
        st.one_of(st.text(), st.integers(), st.floats(allow_nan=False), st.booleans(), st.none()),
        st.text()
    )
)
def test_dict_key_handling(d):
    """Test dictionary key handling with various types"""
    encoder = json.encoder.JSONEncoder(skipkeys=False)
    
    # Check if all keys are valid JSON keys
    valid_keys = all(isinstance(k, (str, int, float, bool, type(None))) for k in d.keys())
    
    if valid_keys:
        encoded = encoder.encode(d)
        decoded = json.loads(encoded)
        
        # Keys might be converted to strings
        for key in d:
            str_key = str(key) if not isinstance(key, str) else key
            if key is None:
                str_key = 'null'
            elif key is True:
                str_key = 'true'
            elif key is False:
                str_key = 'false'
            elif isinstance(key, float) and not math.isnan(key):
                str_key = str(key)
            assert str_key in decoded or str(key) in decoded
    else:
        # Should raise TypeError for invalid keys
        with pytest.raises(TypeError):
            encoder.encode(d)


@given(
    st.text(min_size=0, max_size=10),
    st.text(min_size=0, max_size=10)
)
def test_custom_separators(item_sep, key_sep):
    """Test that custom separators are correctly applied"""
    assume(len(item_sep) > 0 or len(key_sep) > 0)
    
    data = {"a": [1, 2], "b": {"c": 3}}
    encoder = json.encoder.JSONEncoder(separators=(item_sep, key_sep))
    
    encoded = encoder.encode(data)
    
    # Check separators are used
    if len(data) > 0:
        if item_sep:
            # Item separator should appear between list items
            assert item_sep in encoded or len(data["a"]) <= 1
        if key_sep:
            # Key separator should appear after keys
            assert key_sep in encoded


@given(st.floats())
def test_special_float_handling(f):
    """Test handling of special float values (NaN, Infinity)"""
    encoder_allow = json.encoder.JSONEncoder(allow_nan=True)
    encoder_strict = json.encoder.JSONEncoder(allow_nan=False)
    
    if math.isnan(f) or math.isinf(f):
        # Should encode with allow_nan=True
        encoded = encoder_allow.encode(f)
        if math.isnan(f):
            assert encoded == 'NaN'
        elif f == float('inf'):
            assert encoded == 'Infinity'
        elif f == float('-inf'):
            assert encoded == '-Infinity'
        
        # Should raise with allow_nan=False
        with pytest.raises(ValueError):
            encoder_strict.encode(f)
    else:
        # Normal floats should work with both
        encoded_allow = encoder_allow.encode(f)
        encoded_strict = encoder_strict.encode(f)
        assert encoded_allow == encoded_strict


@given(st.integers(min_value=0, max_value=10))
def test_indent_formatting(indent):
    """Test that indentation works correctly"""
    data = {"a": [1, 2], "b": {"c": 3}}
    encoder = json.encoder.JSONEncoder(indent=indent)
    
    encoded = encoder.encode(data)
    
    if indent is not None and indent > 0:
        # Should contain newlines for pretty printing
        assert '\n' in encoded
        # Should contain indentation
        assert ' ' * indent in encoded or len(data) == 0


@given(st.booleans())
def test_sort_keys(sort_keys):
    """Test that sort_keys option works correctly"""
    # Use OrderedDict to ensure consistent input order
    from collections import OrderedDict
    data = OrderedDict([("z", 1), ("a", 2), ("m", 3)])
    
    encoder = json.encoder.JSONEncoder(sort_keys=sort_keys)
    encoded = encoder.encode(data)
    
    if sort_keys:
        # Keys should appear in sorted order
        z_pos = encoded.index('"z"')
        a_pos = encoded.index('"a"')
        m_pos = encoded.index('"m"')
        assert a_pos < m_pos < z_pos
    

@given(
    st.lists(st.text(), min_size=0, max_size=100),
    st.booleans()
)
def test_iterencode_consistency(items, ensure_ascii):
    """Test that iterencode produces same result as encode"""
    encoder = json.encoder.JSONEncoder(ensure_ascii=ensure_ascii)
    
    # Regular encode
    encoded = encoder.encode(items)
    
    # iterencode  
    chunks = list(encoder.iterencode(items))
    iter_encoded = ''.join(chunks)
    
    assert encoded == iter_encoded


@given(st.text())
def test_basestring_functions_consistency(s):
    """Test consistency between Python and C implementations of basestring encoding"""
    # Test regular encoding
    py_encoded = json.encoder.py_encode_basestring(s)
    c_or_py_encoded = json.encoder.encode_basestring(s)
    
    # Both should decode to same value
    assert json.loads(py_encoded) == json.loads(c_or_py_encoded) == s
    
    # Test ASCII encoding
    py_ascii = json.encoder.py_encode_basestring_ascii(s)
    c_or_py_ascii = json.encoder.encode_basestring_ascii(s)
    
    # Both should decode to same value
    assert json.loads(py_ascii) == json.loads(c_or_py_ascii) == s


@given(st.text())
def test_unicode_surrogate_pairs(s):
    """Test that high Unicode characters are properly encoded as surrogate pairs"""
    encoder = json.encoder.JSONEncoder(ensure_ascii=True)
    encoded = encoder.encode(s)
    
    # Decode should recover original
    decoded = json.loads(encoded)
    assert decoded == s
    
    # Check surrogate pair encoding for high Unicode
    for char in s:
        if ord(char) >= 0x10000:
            # Should be encoded as surrogate pair
            char_encoded = encoder.encode(char)
            assert '\\u' in char_encoded
            # Should have two \u escapes for surrogate pair
            assert char_encoded.count('\\u') >= 2


@given(
    st.dictionaries(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False)
        ),
        st.text(),
        min_size=1,
        max_size=10
    )
)
def test_dict_key_conversion(d):
    """Test that non-string dict keys are properly converted"""
    encoder = json.encoder.JSONEncoder()
    encoded = encoder.encode(d)
    decoded = json.loads(encoded)
    
    # All keys in decoded dict should be strings
    assert all(isinstance(k, str) for k in decoded.keys())
    
    # Values should be preserved
    for key, value in d.items():
        if key is None:
            str_key = 'null'
        elif key is True:
            str_key = 'true'
        elif key is False:
            str_key = 'false'
        else:
            str_key = str(key)
        assert decoded[str_key] == value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])