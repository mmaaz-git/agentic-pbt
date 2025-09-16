import json
import math
import string
from decimal import Decimal
from io import StringIO

import pytest
from hypothesis import assume, given, settings, strategies as st


# Round-trip property tests
@given(st.integers())
def test_int_roundtrip(x):
    assert json.loads(json.dumps(x)) == x


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_float_roundtrip(x):
    result = json.loads(json.dumps(x))
    assert math.isclose(result, x, rel_tol=1e-15)


@given(st.text())
def test_string_roundtrip(s):
    assert json.loads(json.dumps(s)) == s


@given(st.booleans())
def test_bool_roundtrip(b):
    assert json.loads(json.dumps(b)) == b


@given(st.none())
def test_none_roundtrip(n):
    assert json.loads(json.dumps(n)) == n


@given(st.lists(st.integers()))
def test_list_roundtrip(lst):
    assert json.loads(json.dumps(lst)) == lst


@given(st.dictionaries(st.text(), st.integers()))
def test_dict_roundtrip(d):
    assert json.loads(json.dumps(d)) == d


# Nested structures
@given(st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text()
    ),
    lambda children: st.one_of(
        st.lists(children),
        st.dictionaries(st.text(), children)
    ),
    max_leaves=50
))
def test_nested_roundtrip(obj):
    assert json.loads(json.dumps(obj)) == obj


# Special characters and unicode
@given(st.text(alphabet=string.printable))
def test_printable_chars_roundtrip(s):
    assert json.loads(json.dumps(s)) == s


@given(st.text(min_size=1).filter(lambda x: any(ord(c) > 127 for c in x)))
def test_unicode_roundtrip(s):
    assert json.loads(json.dumps(s)) == s


# Edge cases with special float values
@given(st.floats())
def test_nan_infinity_handling(x):
    if math.isnan(x) or math.isinf(x):
        # NaN and infinity should round-trip with allow_nan=True (default)
        result = json.loads(json.dumps(x))
        if math.isnan(x):
            assert math.isnan(result)
        else:
            assert result == x
    else:
        result = json.loads(json.dumps(x))
        if x == 0.0:
            # Handle positive/negative zero
            assert result == x
        else:
            assert math.isclose(result, x, rel_tol=1e-15)


# Large numbers
@given(st.integers(min_value=-10**308, max_value=10**308))
def test_large_integers(x):
    assert json.loads(json.dumps(x)) == x


# Dict with non-string keys
@given(st.dictionaries(st.integers(), st.integers(), min_size=1))
def test_dict_non_string_keys(d):
    # Non-string keys should be converted to strings
    result = json.loads(json.dumps(d))
    assert result == {str(k): v for k, v in d.items()}


# skipkeys parameter
@given(st.dictionaries(
    st.one_of(st.text(), st.integers(), st.tuples(st.integers())),
    st.integers()
))
def test_skipkeys_parameter(d):
    # Filter out non-string/basic keys
    valid_keys = {k: v for k, v in d.items() 
                  if isinstance(k, (str, int, float, bool, type(None)))}
    
    if len(valid_keys) < len(d):
        # Should raise TypeError without skipkeys
        with pytest.raises(TypeError):
            json.dumps(d)
        # Should work with skipkeys=True
        result = json.loads(json.dumps(d, skipkeys=True))
        expected = {str(k): v for k, v in valid_keys.items()}
        assert result == expected


# ensure_ascii parameter
@given(st.text(alphabet='αβγδεζηθικλμνξοπρστυφχψω'))
def test_ensure_ascii_parameter(s):
    # With ensure_ascii=False, non-ASCII chars should be preserved
    json_str = json.dumps(s, ensure_ascii=False)
    assert s in json_str
    assert json.loads(json_str) == s
    
    # With ensure_ascii=True (default), non-ASCII should be escaped
    json_str_escaped = json.dumps(s, ensure_ascii=True)
    assert json.loads(json_str_escaped) == s


# sort_keys parameter
@given(st.dictionaries(st.text(min_size=1), st.integers(), min_size=2))
def test_sort_keys_parameter(d):
    json_str = json.dumps(d, sort_keys=True)
    # Keys should appear in sorted order in the JSON string
    keys_in_json = []
    import re
    for match in re.finditer(r'"([^"]+)":', json_str):
        keys_in_json.append(match.group(1))
    assert keys_in_json == sorted(d.keys())
    assert json.loads(json_str) == d


# Whitespace handling
@given(st.text(), st.sampled_from([' ', '\t', '\n', '\r']))
def test_whitespace_in_json(content, ws):
    # Extra whitespace in JSON should be ignored during parsing
    obj = {"key": content}
    json_str = json.dumps(obj)
    json_with_ws = json_str.replace(':', ':' + ws).replace(',', ',' + ws)
    assert json.loads(json_with_ws) == obj


# File-like object support
@given(st.recursive(
    st.one_of(st.none(), st.booleans(), st.integers(), st.text()),
    lambda children: st.lists(children),
    max_leaves=10
))
def test_dump_load_file_objects(obj):
    fp = StringIO()
    json.dump(obj, fp)
    fp.seek(0)
    assert json.load(fp) == obj


# Circular reference detection
def test_circular_reference_detection():
    circular = []
    circular.append(circular)
    with pytest.raises(ValueError):
        json.dumps(circular)
    
    # Should work with check_circular=False but might cause recursion
    # We won't test this as it could crash


# Custom encoder/decoder behavior
@given(st.floats(min_value=0.1, max_value=1000))
def test_custom_float_parsing(x):
    # Test parse_float parameter
    json_str = json.dumps(x)
    result = json.loads(json_str, parse_float=Decimal)
    assert isinstance(result, Decimal)
    assert float(result) == pytest.approx(x)


@given(st.integers())
def test_custom_int_parsing(x):
    # Test parse_int parameter
    json_str = json.dumps(x)
    result = json.loads(json_str, parse_int=lambda n: int(n) * 2)
    assert result == x * 2


# Separators parameter
@given(st.dictionaries(st.text(), st.integers(), min_size=1))
def test_separators_parameter(d):
    compact = json.dumps(d, separators=(',', ':'))
    normal = json.dumps(d)
    
    # Compact should have no extra spaces
    assert ' ' not in compact.replace('" ', '"').replace(' "', '"')
    assert json.loads(compact) == d
    assert json.loads(normal) == d


# Escape sequences
@given(st.text(alphabet='\\\"\b\f\n\r\t'))
def test_escape_sequences(s):
    result = json.loads(json.dumps(s))
    assert result == s


# Empty containers
def test_empty_containers():
    assert json.loads(json.dumps([])) == []
    assert json.loads(json.dumps({})) == {}
    assert json.loads(json.dumps("")) == ""


# Mixed type lists
@given(st.lists(st.one_of(
    st.integers(),
    st.text(),
    st.booleans(),
    st.none()
)))
def test_mixed_type_lists(lst):
    assert json.loads(json.dumps(lst)) == lst


# Very deeply nested structures
@given(st.integers(min_value=1, max_value=100))
def test_deeply_nested_lists(depth):
    obj = []
    current = obj
    for _ in range(depth - 1):
        current.append([])
        current = current[0]
    current.append(42)
    
    result = json.loads(json.dumps(obj))
    assert result == obj


# Special string patterns
@given(st.text(alphabet='{}[],:"\\ \t\n'))
def test_json_special_chars_in_strings(s):
    # Strings containing JSON special characters should be properly escaped
    result = json.loads(json.dumps(s))
    assert result == s


# Test interaction between parameters
@given(
    st.dictionaries(st.text(), st.floats()),
    st.booleans(),
    st.booleans()
)
def test_parameter_interactions(d, sort_keys, ensure_ascii):
    json_str = json.dumps(d, sort_keys=sort_keys, ensure_ascii=ensure_ascii)
    result = json.loads(json_str)
    
    # Handle NaN/infinity comparison
    for key in d:
        if math.isnan(d[key]):
            assert math.isnan(result[key])
        elif math.isinf(d[key]):
            assert result[key] == d[key]
        else:
            assert result[key] == pytest.approx(d[key])


# Test bytes input to loads
@given(st.dictionaries(st.text(), st.integers()))
def test_loads_bytes_input(d):
    json_str = json.dumps(d)
    json_bytes = json_str.encode('utf-8')
    assert json.loads(json_bytes) == d
    
    # Also test with other encodings
    json_bytes_utf16 = json_str.encode('utf-16')
    assert json.loads(json_bytes_utf16) == d


# Test invalid JSON handling
@given(st.text(min_size=1))
def test_invalid_json_detection(s):
    # Most random strings should not be valid JSON
    if s not in ('null', 'true', 'false') and not s.startswith('"'):
        try:
            result = json.loads(s)
            # If it parsed, it should be a valid number
            assert s.strip().replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '').isdigit()
        except json.JSONDecodeError:
            pass  # Expected for most random strings