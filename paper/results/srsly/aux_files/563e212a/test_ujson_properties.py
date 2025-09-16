#!/usr/bin/env python3
"""
Property-based testing for srsly.ujson using Hypothesis.
Testing fundamental properties that ujson claims to have based on its documentation and usage.
"""

import sys
import json
import math
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

import srsly.ujson as ujson
from hypothesis import given, strategies as st, assume, settings
import pytest


# Strategy for JSON-compatible values
json_primitives = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(2**53), max_value=2**53),  # JavaScript safe integer range
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
)

# Recursive strategy for nested JSON structures
json_values = st.recursive(
    json_primitives,
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(st.text(), children, max_size=10)
    ),
    max_leaves=50
)


class TestUjsonRoundTrip:
    """Test the fundamental round-trip property: decode(encode(x)) == x"""
    
    @given(json_values)
    @settings(max_examples=1000)
    def test_round_trip_property(self, value):
        """Property: For any JSON-serializable value x, decode(encode(x)) should equal x"""
        encoded = ujson.dumps(value)
        decoded = ujson.loads(encoded)
        
        # For floats, we need to handle precision issues
        if isinstance(value, float):
            if not math.isfinite(value):
                pytest.skip("Skipping non-finite float")
            # ujson seems to have precision limitations
            assert math.isclose(decoded, value, rel_tol=1e-9, abs_tol=1e-10)
        else:
            assert decoded == value, f"Round-trip failed: {value} != {decoded}"
    
    @given(st.dictionaries(st.text(), json_values, min_size=1))
    @settings(max_examples=500)
    def test_dict_round_trip(self, d):
        """Property: Dictionary round-trip should preserve all key-value pairs"""
        encoded = ujson.dumps(d)
        decoded = ujson.loads(encoded)
        
        assert set(decoded.keys()) == set(d.keys()), f"Keys mismatch: {set(d.keys())} != {set(decoded.keys())}"
        
        for key in d:
            if isinstance(d[key], float) and math.isfinite(d[key]):
                assert math.isclose(decoded[key], d[key], rel_tol=1e-9, abs_tol=1e-10)
            else:
                assert decoded[key] == d[key], f"Value mismatch for key '{key}': {d[key]} != {decoded[key]}"
    
    @given(st.lists(json_values, min_size=0, max_size=100))
    @settings(max_examples=500)
    def test_list_round_trip(self, lst):
        """Property: List round-trip should preserve order and all elements"""
        encoded = ujson.dumps(lst)
        decoded = ujson.loads(encoded)
        
        assert len(decoded) == len(lst), f"Length mismatch: {len(lst)} != {len(decoded)}"
        
        for i, (original, decoded_val) in enumerate(zip(lst, decoded)):
            if isinstance(original, float) and math.isfinite(original):
                assert math.isclose(decoded_val, original, rel_tol=1e-9, abs_tol=1e-10)
            else:
                assert decoded_val == original, f"Element mismatch at index {i}: {original} != {decoded_val}"


class TestUjsonJsonCompatibility:
    """Test compatibility between ujson and standard json module"""
    
    @given(json_values)
    @settings(max_examples=500)
    def test_ujson_can_decode_json_output(self, value):
        """Property: ujson should be able to decode standard json module output"""
        json_encoded = json.dumps(value)
        ujson_decoded = ujson.loads(json_encoded)
        
        # Account for float precision differences
        if isinstance(value, float) and math.isfinite(value):
            assert math.isclose(ujson_decoded, value, rel_tol=1e-9, abs_tol=1e-10)
        else:
            assert ujson_decoded == value
    
    @given(json_values)
    @settings(max_examples=500)
    def test_json_can_decode_ujson_output(self, value):
        """Property: standard json should be able to decode ujson output"""
        ujson_encoded = ujson.dumps(value)
        json_decoded = json.loads(ujson_encoded)
        
        # Account for float precision differences
        if isinstance(value, float) and math.isfinite(value):
            assert math.isclose(json_decoded, value, rel_tol=1e-9, abs_tol=1e-10)
        else:
            assert json_decoded == value


class TestUjsonUnicodeHandling:
    """Test Unicode string handling in ujson"""
    
    @given(st.text())
    @settings(max_examples=500)
    def test_unicode_string_round_trip(self, s):
        """Property: Any valid Unicode string should round-trip correctly"""
        encoded = ujson.dumps(s)
        decoded = ujson.loads(encoded)
        assert decoded == s, f"Unicode round-trip failed: {repr(s)} != {repr(decoded)}"
    
    @given(st.dictionaries(st.text(min_size=1), st.text(), min_size=1))
    @settings(max_examples=500)
    def test_unicode_keys_round_trip(self, d):
        """Property: Dictionaries with Unicode keys should round-trip correctly"""
        encoded = ujson.dumps(d)
        decoded = ujson.loads(encoded)
        assert decoded == d, f"Unicode key dict round-trip failed"
    
    @given(st.text())
    @settings(max_examples=500)
    def test_special_characters_preserved(self, s):
        """Property: Special characters like newlines, tabs, quotes should be preserved"""
        encoded = ujson.dumps(s)
        decoded = ujson.loads(encoded)
        
        # Check that special characters are preserved
        assert s.count('\n') == decoded.count('\n'), "Newlines not preserved"
        assert s.count('\t') == decoded.count('\t'), "Tabs not preserved"
        assert s.count('"') == decoded.count('"'), "Quotes not preserved"
        assert s.count('\\') == decoded.count('\\'), "Backslashes not preserved"


class TestUjsonFloatPrecision:
    """Test float handling and precision in ujson"""
    
    @given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e308, max_value=1e308))
    @settings(max_examples=1000)
    def test_float_precision(self, f):
        """Property: Floats should maintain reasonable precision through round-trip"""
        encoded = ujson.dumps(f)
        decoded = ujson.loads(encoded)
        
        # Based on the documentation mentioning double_precision parameter,
        # ujson should handle doubles but may have precision limits
        if f == 0.0:
            assert decoded == 0.0
        else:
            # ujson appears to limit precision - test what precision is maintained
            # The exploration showed precision issues at ~10 digits
            rel_error = abs((decoded - f) / f) if f != 0 else abs(decoded - f)
            assert rel_error < 1e-9 or abs(decoded - f) < 1e-10, \
                f"Float precision lost: {f} encoded as {encoded}, decoded as {decoded}, rel_error={rel_error}"
    
    @given(st.floats(allow_nan=False, allow_infinity=False))
    @settings(max_examples=500)
    def test_float_string_representation(self, f):
        """Property: Float encoding should produce valid JSON number format"""
        encoded = ujson.dumps(f)
        
        # Should be a valid JSON number
        try:
            json.loads(encoded)
        except json.JSONDecodeError:
            pytest.fail(f"ujson produced invalid JSON for float {f}: {encoded}")
        
        # Should not contain NaN or Infinity strings
        assert 'NaN' not in encoded
        assert 'Infinity' not in encoded
        assert '-Infinity' not in encoded


class TestUjsonEdgeCases:
    """Test edge cases and special values"""
    
    def test_empty_structures(self):
        """Property: Empty structures should round-trip correctly"""
        empty_values = [
            [],
            {},
            "",
            {"empty_list": [], "empty_dict": {}, "empty_string": ""},
        ]
        
        for value in empty_values:
            encoded = ujson.dumps(value)
            decoded = ujson.loads(encoded)
            assert decoded == value, f"Empty structure failed: {value}"
    
    @given(st.integers())
    @settings(max_examples=500)
    def test_integer_precision(self, i):
        """Property: Integers within JSON safe range should round-trip exactly"""
        # JSON safe integer range is -(2^53) to 2^53
        if -(2**53) <= i <= 2**53:
            encoded = ujson.dumps(i)
            decoded = ujson.loads(encoded)
            assert decoded == i, f"Integer round-trip failed: {i} != {decoded}"
        else:
            # Outside safe range, might lose precision
            encoded = ujson.dumps(i) 
            decoded = ujson.loads(encoded)
            # Should at least be close for large integers
            if i != decoded:
                rel_error = abs((decoded - i) / i) if i != 0 else abs(decoded - i)
                assert rel_error < 1e-15, f"Large integer precision lost: {i} != {decoded}"
    
    @given(st.recursive(
        st.dictionaries(st.text(), st.none(), max_size=3),
        lambda children: st.dictionaries(st.text(), children, max_size=3),
        max_leaves=10
    ))
    @settings(max_examples=200)
    def test_deeply_nested_structures(self, nested):
        """Property: Deeply nested structures should round-trip correctly"""
        encoded = ujson.dumps(nested)
        decoded = ujson.loads(encoded)
        assert decoded == nested, "Deeply nested structure round-trip failed"


class TestUjsonInvariantProperties:
    """Test invariant properties that should always hold"""
    
    @given(json_values)
    @settings(max_examples=500)
    def test_encode_is_string(self, value):
        """Property: encode/dumps always returns a string"""
        encoded = ujson.dumps(value)
        assert isinstance(encoded, str), f"dumps did not return string: {type(encoded)}"
    
    @given(json_values)
    @settings(max_examples=500)
    def test_encode_decode_inverse(self, value):
        """Property: encode and decode are inverse operations"""
        # encode then decode should return original
        encoded = ujson.dumps(value)
        decoded = ujson.loads(encoded)
        
        # decode then encode should produce equivalent JSON
        re_encoded = ujson.dumps(decoded)
        re_decoded = ujson.loads(re_encoded)
        
        # Account for float precision
        def values_equal(a, b):
            if isinstance(a, float) and isinstance(b, float):
                return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-10)
            elif isinstance(a, dict) and isinstance(b, dict):
                return all(k in b and values_equal(a[k], b[k]) for k in a) and len(a) == len(b)
            elif isinstance(a, list) and isinstance(b, list):
                return len(a) == len(b) and all(values_equal(x, y) for x, y in zip(a, b))
            else:
                return a == b
        
        assert values_equal(decoded, re_decoded), "encode/decode are not inverse operations"


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "--tb=short"])