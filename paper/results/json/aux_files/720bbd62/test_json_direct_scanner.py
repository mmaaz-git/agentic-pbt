import json
import json.scanner
import json.decoder
from hypothesis import given, strategies as st, assume, settings, example
import re


# Test using the scanner directly
class TestContext:
    """Context object for testing scanner directly"""
    def __init__(self, strict=True):
        self.strict = strict
        self.parse_float = float
        self.parse_int = int
        self.parse_constant = lambda x: {"NaN": float("nan"), "Infinity": float("inf"), "-Infinity": float("-inf")}.get(x)
        self.object_hook = None
        self.object_pairs_hook = None
        self.memo = {}
        
        # These need to be real implementations
        from json.decoder import JSONObject, JSONArray, py_scanstring
        self.parse_string = py_scanstring
        self.parse_object = JSONObject
        self.parse_array = JSONArray


@given(st.text(alphabet='0123456789+-eE.', min_size=1, max_size=30))
def test_scanner_number_parsing(text):
    """Test the scanner's number parsing directly"""
    context = TestContext()
    scanner = json.scanner.py_make_scanner(context)
    
    # Test if NUMBER_RE matches
    match = json.scanner.NUMBER_RE.match(text)
    
    if match and match.end() == len(text):
        # NUMBER_RE thinks it's a valid number
        try:
            # Try with the scanner
            result, end_idx = scanner(text, 0)
            
            # Scanner should parse it as a number
            assert isinstance(result, (int, float)), f"Scanner didn't parse as number: {text}"
            assert end_idx == len(text), f"Scanner didn't consume full number: {text}"
            
            # Compare with json.loads
            try:
                json_result = json.loads(text)
                assert result == json_result or (isinstance(result, float) and isinstance(json_result, float) and abs(result - json_result) < 1e-10)
            except json.JSONDecodeError:
                # Scanner parsed but json.loads didn't - potential bug
                pass
        except StopIteration:
            # Scanner couldn't parse it
            pass


@given(st.text(min_size=1, max_size=100))
def test_scanner_string_parsing(text):
    """Test scanner's string parsing"""
    context = TestContext()
    scanner = json.scanner.py_make_scanner(context)
    
    # Create a JSON string
    json_str = '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'
    
    try:
        result, end_idx = scanner(json_str, 0)
        
        # Should parse as string
        assert isinstance(result, str)
        
        # Compare with json.loads
        json_result = json.loads(json_str)
        assert result == json_result
    except (StopIteration, json.JSONDecodeError):
        pass


@given(st.lists(st.integers(), min_size=0, max_size=10))
def test_scanner_array_parsing(lst):
    """Test scanner's array parsing"""
    context = TestContext()
    scanner = json.scanner.py_make_scanner(context)
    
    json_str = json.dumps(lst)
    
    try:
        result, end_idx = scanner(json_str, 0)
        assert result == lst
        assert end_idx == len(json_str)
    except StopIteration:
        pass


@given(st.dictionaries(st.text(min_size=1), st.integers(), min_size=0, max_size=10))
def test_scanner_object_parsing(dct):
    """Test scanner's object parsing"""
    context = TestContext()
    scanner = json.scanner.py_make_scanner(context)
    
    json_str = json.dumps(dct)
    
    try:
        result, end_idx = scanner(json_str, 0)
        assert result == dct
        assert end_idx == len(json_str)
    except StopIteration:
        pass


@given(st.sampled_from(['NaN', 'Infinity', '-Infinity']))
def test_scanner_constants(const):
    """Test scanner's handling of special constants"""
    context = TestContext()
    scanner = json.scanner.py_make_scanner(context)
    
    try:
        result, end_idx = scanner(const, 0)
        
        if const == 'NaN':
            assert result != result  # NaN check
        elif const == 'Infinity':
            assert result == float('inf')
        elif const == '-Infinity':
            assert result == float('-inf')
            
        assert end_idx == len(const)
    except StopIteration:
        # Scanner might not support these
        pass


@given(st.text(alphabet=' \t\n\r', min_size=0, max_size=10))
def test_scanner_whitespace_handling(ws):
    """Test scanner's whitespace handling"""
    context = TestContext()
    scanner = json.scanner.py_make_scanner(context)
    
    # Test with whitespace around values
    test_values = ['true', 'false', 'null', '123', '"test"', '[]', '{}']
    
    for value in test_values:
        json_str = ws + value + ws
        
        try:
            # Scanner should skip leading whitespace
            result, end_idx = scanner(json_str, len(ws))
            
            # Should parse the value
            expected = json.loads(value)
            assert result == expected
        except (StopIteration, json.JSONDecodeError):
            pass


@given(st.integers(min_value=0, max_value=1000))
def test_scanner_index_boundary(idx):
    """Test scanner with various starting indices"""
    context = TestContext()
    scanner = json.scanner.py_make_scanner(context)
    
    # Create a long string with JSON values at different positions
    padding = ' ' * idx
    test_str = padding + '123'
    
    try:
        result, end_idx = scanner(test_str, idx)
        assert result == 123
        assert end_idx == idx + 3
    except StopIteration:
        # Expected at end of string
        if idx >= len(test_str):
            pass


@given(st.text(alphabet='truefalsn', min_size=1, max_size=10))
def test_scanner_partial_literals(text):
    """Test scanner with partial literal constants"""
    context = TestContext()
    scanner = json.scanner.py_make_scanner(context)
    
    # Test partial matches of true, false, null
    try:
        result, end_idx = scanner(text, 0)
        
        # Should only succeed for complete literals
        if text == 'true':
            assert result is True
        elif text == 'false':
            assert result is False
        elif text == 'null':
            assert result is None
        else:
            # Partial match should have failed
            assert False, f"Scanner accepted partial literal: {text}"
    except (StopIteration, IndexError):
        # Expected for partial literals
        if text not in ['true', 'false', 'null']:
            pass


@given(st.from_regex(r'-?0+[0-9]+', fullmatch=True))
def test_scanner_leading_zeros(num_str):
    """Test scanner with numbers having leading zeros"""
    context = TestContext()
    scanner = json.scanner.py_make_scanner(context)
    
    # NUMBER_RE behavior
    match = json.scanner.NUMBER_RE.match(num_str)
    
    try:
        result, end_idx = scanner(num_str, 0)
        
        # Check if scanner accepts invalid leading zeros
        if num_str not in ['0', '-0']:
            # Should have rejected per JSON spec
            pass
    except StopIteration:
        # Expected - should reject leading zeros
        pass


@given(st.from_regex(r'[0-9]+\.[eE]?[+-]?[0-9]*', fullmatch=True))
def test_scanner_decimal_incomplete(num_str):
    """Test scanner with incomplete decimal numbers"""
    context = TestContext()
    scanner = json.scanner.py_make_scanner(context)
    
    match = json.scanner.NUMBER_RE.match(num_str)
    
    try:
        result, end_idx = scanner(num_str, 0)
        
        # Check if it's a valid JSON number
        try:
            json_result = json.loads(num_str)
            assert result == json_result or (isinstance(result, float) and abs(result - json_result) < 1e-10)
        except json.JSONDecodeError:
            # Scanner accepted but JSON didn't
            pass
    except StopIteration:
        # Scanner rejected
        if match and match.end() == len(num_str):
            # NUMBER_RE matched but scanner rejected
            pass


@given(st.text())
def test_scanner_memo_clearing(text):
    """Test that scanner clears memo correctly"""
    context = TestContext()
    scanner = json.scanner.py_make_scanner(context)
    
    # Test multiple scans with same context
    test_values = ['123', '"test"', 'true', 'null']
    
    for value in test_values:
        try:
            result, end_idx = scanner(value, 0)
            # Memo should be cleared after each scan
            assert len(context.memo) == 0
        except StopIteration:
            pass


@given(st.text(alphabet='\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f', min_size=1))
def test_scanner_control_characters(ctrl):
    """Test scanner with control characters"""
    context = TestContext(strict=True)
    scanner = json.scanner.py_make_scanner(context)
    
    # Test in string context
    json_str = '"' + ctrl + '"'
    
    try:
        result, end_idx = scanner(json_str, 0)
        # Should reject unescaped control characters in strict mode
        assert False, f"Scanner accepted unescaped control characters: {repr(ctrl)}"
    except (StopIteration, json.JSONDecodeError):
        pass  # Expected
    
    # Test non-strict mode
    context.strict = False
    scanner = json.scanner.py_make_scanner(context)
    
    try:
        result, end_idx = scanner(json_str, 0)
        # Non-strict mode might accept them
        assert result == ctrl
    except (StopIteration, json.JSONDecodeError):
        pass


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])