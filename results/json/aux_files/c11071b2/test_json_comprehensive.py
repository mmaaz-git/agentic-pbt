import json
import math
from decimal import Decimal
from hypothesis import given, strategies as st, assume, settings


# Test Unicode escape sequences beyond BMP
@given(st.integers(min_value=0x10000, max_value=0x10FFFF))
def test_unicode_beyond_bmp(codepoint):
    # Characters beyond Basic Multilingual Plane
    char = chr(codepoint)
    json_str = json.dumps(char)
    result = json.loads(json_str)
    assert result == char


# Test edge case numbers as strings vs numbers
@given(st.sampled_from(['1.0', '1e0', '1E0', '1.0e0', '10e-1']))
def test_equivalent_number_formats(num_str):
    # All these should parse to 1.0
    result = json.loads(num_str)
    assert result == 1.0


# Test object_hook and object_pairs_hook interaction
def test_hooks_interaction():
    json_str = '{"a": 1, "b": {"c": 2}}'
    
    hook_calls = []
    pairs_hook_calls = []
    
    def obj_hook(d):
        hook_calls.append(d.copy())
        return d
    
    def pairs_hook(pairs):
        pairs_hook_calls.append(list(pairs))
        return dict(pairs)
    
    # When both are specified, only object_pairs_hook should be called
    result = json.loads(json_str, object_hook=obj_hook, object_pairs_hook=pairs_hook)
    assert len(pairs_hook_calls) == 2  # Called for both objects
    assert len(hook_calls) == 0  # Should not be called


# Test preservation of float precision edge cases
@given(st.floats(min_value=0.0, max_value=1.0).filter(
    lambda x: x != 0 and len(str(x)) > 15
))
def test_float_precision_edge_cases(x):
    json_str = json.dumps(x)
    result = json.loads(json_str)
    # Some precision loss is expected with floats
    assert math.isclose(result, x, rel_tol=1e-15)


# Test different unicode normalization forms
@given(st.text(alphabet='é').map(lambda s: s if s else 'é'))
def test_unicode_normalization(s):
    # Test both composed and decomposed forms
    import unicodedata
    nfc = unicodedata.normalize('NFC', s)
    nfd = unicodedata.normalize('NFD', s)
    
    # Both should round-trip correctly
    assert json.loads(json.dumps(nfc)) == nfc
    assert json.loads(json.dumps(nfd)) == nfd


# Test JSON Pointer-like keys
@given(st.text(alphabet='/#~', min_size=1, max_size=10))
def test_json_pointer_chars_in_keys(key):
    # Keys with JSON Pointer special characters
    d = {key: "value"}
    assert json.loads(json.dumps(d)) == d


# Test very small positive floats
@given(st.floats(min_value=1e-320, max_value=1e-300, allow_nan=False))
def test_tiny_positive_floats(x):
    json_str = json.dumps(x)
    result = json.loads(json_str)
    if x != 0:
        assert math.isclose(result, x, rel_tol=1e-10)
    else:
        assert result == x


# Test string containing JSON-like content
@given(st.text(alphabet='{}[],":\\', min_size=5, max_size=20))
def test_json_syntax_in_strings(s):
    # Strings that look like JSON should still work
    assert json.loads(json.dumps(s)) == s


# Test skipkeys with various non-serializable types
def test_skipkeys_comprehensive():
    class CustomObj:
        pass
    
    d = {
        "valid": 1,
        CustomObj(): 2,
        (1, 2): 3,
        frozenset([1, 2]): 4,
        1.5: 5,
        True: 6,
        None: 7
    }
    
    # Without skipkeys, should fail
    try:
        json.dumps(d)
        assert False, "Should have raised TypeError"
    except TypeError:
        pass
    
    # With skipkeys, should work
    result_str = json.dumps(d, skipkeys=True)
    result = json.loads(result_str)
    
    # Only basic types should remain
    assert "valid" in result
    assert "1.5" in result  # Float keys become strings
    assert "true" in result  # Boolean True becomes "true"
    assert "null" in result  # None becomes "null"


# Test separators with unicode
def test_separators_unicode():
    # Using non-ASCII characters as separators should fail
    d = {"key": "value"}
    
    try:
        json.dumps(d, separators=('，', '：'))  # Chinese comma and colon
        # Actually this might work, let's see
        result = json.dumps(d, separators=('，', '：'))
        # If it works, can we parse it back?
        try:
            json.loads(result)
            assert False, "Should not parse with non-standard separators"
        except json.JSONDecodeError:
            pass  # Expected
    except (TypeError, ValueError):
        pass  # Some implementations might reject non-ASCII separators


# Test integer key conversion order
def test_integer_key_order():
    d = {2: "two", 1: "one", 3: "three"}
    json_str = json.dumps(d, sort_keys=True)
    result = json.loads(json_str)
    
    # Integer keys become strings, should be sorted as strings
    assert list(result.keys()) == ["1", "2", "3"]


# Test allow_nan parameter
def test_allow_nan_false():
    values = [float('inf'), float('-inf'), float('nan')]
    
    for val in values:
        # Should fail with allow_nan=False
        try:
            json.dumps(val, allow_nan=False)
            assert False, f"Should have rejected {val} with allow_nan=False"
        except ValueError:
            pass  # Expected


# Test check_circular with complex references
def test_check_circular_complex():
    a = []
    b = [a]
    a.append(b)
    
    # Should detect circular reference
    try:
        json.dumps(a)
        assert False, "Should have detected circular reference"
    except ValueError as e:
        assert "circular" in str(e).lower()


# Test cls parameter with custom encoder
def test_custom_encoder_class():
    class MyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, set):
                return list(obj)
            return super().default(obj)
    
    data = {"items": {1, 2, 3}}
    result_str = json.dumps(data, cls=MyEncoder)
    result = json.loads(result_str)
    
    assert set(result["items"]) == {1, 2, 3}


# Test indent with various values
@given(st.one_of(st.integers(min_value=0, max_value=10), st.text(alphabet=' \t', max_size=4)))
def test_indent_parameter(indent):
    d = {"a": {"b": 1}}
    
    try:
        json_str = json.dumps(d, indent=indent)
        # Should be able to parse it back
        result = json.loads(json_str)
        assert result == d
        
        # With indent, should have newlines
        if indent:
            assert '\n' in json_str
    except (TypeError, ValueError):
        # Some indent values might be rejected
        pass


# Test bytes input with BOM
def test_bytes_with_bom():
    d = {"key": "value"}
    json_str = json.dumps(d)
    
    # Add UTF-8 BOM
    json_bytes = b'\xef\xbb\xbf' + json_str.encode('utf-8')
    result = json.loads(json_bytes)
    assert result == d
    
    # UTF-16 with BOM
    json_bytes_16 = json_str.encode('utf-16')  # Automatically adds BOM
    result = json.loads(json_bytes_16)
    assert result == d


# Test default parameter with various types
def test_default_parameter():
    def custom_default(obj):
        if isinstance(obj, complex):
            return {"real": obj.real, "imag": obj.imag}
        elif isinstance(obj, bytes):
            return obj.decode('utf-8')
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        raise TypeError(f"Cannot serialize {type(obj)}")
    
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y
    
    data = {
        "complex": 1 + 2j,
        "bytes": b"hello",
        "point": Point(3, 4)
    }
    
    json_str = json.dumps(data, default=custom_default)
    result = json.loads(json_str)
    
    assert result["complex"] == {"real": 1.0, "imag": 2.0}
    assert result["bytes"] == "hello"
    assert result["point"] == {"x": 3, "y": 4}