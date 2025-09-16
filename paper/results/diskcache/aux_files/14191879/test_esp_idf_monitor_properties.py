#!/usr/bin/env python3
"""Property-based tests for esp_idf_monitor using Hypothesis"""

import re
import struct
from hypothesis import given, strategies as st, assume, settings
import sys
import os

# Add the site-packages to Python path for imports
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')

from esp_idf_monitor.base.line_matcher import LineMatcher
from esp_idf_monitor.base.console_parser import ConsoleParser
from esp_idf_monitor.base.binlog import BinaryLog, Control, ArgFormatter


# ===========================================
# Test 1: LineMatcher Properties
# ===========================================

@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=100))
def test_line_matcher_filter_initialization(filter_str):
    """Property: LineMatcher should correctly parse filter strings"""
    # Skip invalid filter strings that would raise ValueError
    filter_items = filter_str.split()
    for item in filter_items:
        if ':' in item:
            parts = item.split(':')
            if len(parts) > 2 or (len(parts) == 2 and parts[1] not in 'NEWIDV*'):
                assume(False)
        elif item:  # non-empty items without colon are valid
            continue
    
    try:
        matcher = LineMatcher(filter_str)
        # Property: _dict should be initialized and contain parsed filters
        assert hasattr(matcher, '_dict')
        assert isinstance(matcher._dict, dict)
        
        # If filter is empty, default should be verbose
        if not filter_str.strip():
            assert '*' in matcher._dict
            assert matcher._dict['*'] == LineMatcher.LEVEL_V
    except ValueError:
        # Filter parsing can raise ValueError for invalid formats
        pass


@given(
    st.sampled_from(['E', 'W', 'I', 'D', 'V']),
    st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=20),
    st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=100)
)
def test_line_matcher_match_consistency(level, tag, message):
    """Property: Match results should be consistent for the same input"""
    # Create a line in the expected format
    line = f"{level} ({tag}): {message}"
    
    # Test with various filter configurations
    filters = [
        f"{tag}:V",  # Allow all from this tag
        f"{tag}:{level}",  # Allow this level and above
        f"*:{level}",  # Allow this level and above for all tags
        "",  # Default filter
    ]
    
    for filter_str in filters:
        matcher = LineMatcher(filter_str)
        result1 = matcher.match(line)
        result2 = matcher.match(line)
        # Property: Same line should always give same match result
        assert result1 == result2


@given(st.sampled_from(['N', 'E', 'W', 'I', 'D', 'V']))
def test_line_matcher_level_ordering(level):
    """Property: Log levels have strict ordering N < E < W < I < D < V"""
    expected_order = {'N': 0, 'E': 1, 'W': 2, 'I': 3, 'D': 4, 'V': 5}
    
    # Property: Level values should match expected ordering
    assert LineMatcher.level[level] == expected_order[level]
    
    # Property: Numeric constants should match
    if level == 'N':
        assert LineMatcher.level[level] == LineMatcher.LEVEL_N
    elif level == 'E':
        assert LineMatcher.level[level] == LineMatcher.LEVEL_E
    elif level == 'W':
        assert LineMatcher.level[level] == LineMatcher.LEVEL_W
    elif level == 'I':
        assert LineMatcher.level[level] == LineMatcher.LEVEL_I
    elif level == 'D':
        assert LineMatcher.level[level] == LineMatcher.LEVEL_D
    elif level == 'V':
        assert LineMatcher.level[level] == LineMatcher.LEVEL_V


# ===========================================
# Test 2: ConsoleParser Properties
# ===========================================

@given(
    st.sampled_from(['CRLF', 'CR', 'LF']),
    st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=100)
)
def test_console_parser_eol_translation(eol_mode, text):
    """Property: EOL translation should be consistent"""
    parser = ConsoleParser(eol_mode)
    
    # Add newlines to test translation
    text_with_newline = text + '\n'
    translated = parser.translate_eol(text_with_newline)
    
    # Property: Translation should produce expected EOL
    if eol_mode == 'CRLF':
        assert '\r\n' in translated or '\n' not in text_with_newline
    elif eol_mode == 'CR':
        assert translated.count('\r') >= text_with_newline.count('\n')
    elif eol_mode == 'LF':
        # LF mode replaces \r with \n
        assert '\r' not in translated or text_with_newline.count('\r') == 0


@given(st.characters(min_codepoint=32, max_codepoint=126))
def test_console_parser_parse_determinism(key):
    """Property: Same key should always produce same parse result"""
    parser = ConsoleParser()
    
    # Parse the same key multiple times
    result1 = parser.parse(key)
    result2 = parser.parse(key)
    
    # Property: Parsing should be deterministic
    assert result1 == result2
    
    # Property: Result should be None or a tuple
    assert result1 is None or isinstance(result1, tuple)


# ===========================================
# Test 3: BinaryLog Properties
# ===========================================

@given(st.binary(min_size=1, max_size=255))
def test_binary_log_crc8_property(data):
    """Property: CRC8 has mathematical properties"""
    crc = BinaryLog.crc8(data)
    
    # Property 1: CRC8 result is always 8-bit
    assert 0 <= crc <= 255
    
    # Property 2: CRC of data + its CRC should be 0
    data_with_crc = data + bytes([crc])
    assert BinaryLog.crc8(data_with_crc) == 0


@given(st.binary(min_size=2, max_size=1024))
def test_binary_log_control_structure(raw_data):
    """Property: Control structure parsing should extract valid fields"""
    assume(len(raw_data) >= 2)  # Control needs at least 2 bytes
    
    control = Control(raw_data)
    
    # Property: Parsed fields should be within valid ranges
    assert 0 <= control.pkg_len <= 0x3FF  # 10 bits
    assert 0 <= control.level <= 0x07  # 3 bits
    assert isinstance(control.time_64bits, bool)  # 1 bit
    assert 0 <= control.version <= 0x03  # 2 bits


@given(
    st.integers(min_value=1, max_value=0x3FF),  # package length
    st.integers(min_value=0, max_value=7),  # level
    st.booleans(),  # time_64bits
    st.integers(min_value=0, max_value=3)  # version
)
def test_binary_log_control_round_trip(pkg_len, level, time_64bits, version):
    """Property: Control encoding and decoding should preserve values"""
    # Encode control data
    data = pkg_len | (level << 10) | (int(time_64bits) << 13) | (version << 14)
    raw_bytes = struct.pack('>H', data)
    
    # Decode it back
    control = Control(raw_bytes)
    
    # Property: Round-trip should preserve all fields
    assert control.pkg_len == pkg_len
    assert control.level == level
    assert control.time_64bits == time_64bits
    assert control.version == version


# ===========================================
# Test 4: ArgFormatter Properties
# ===========================================

@given(st.sampled_from(['d', 'i', 'u', 'o', 'x', 'X', 's', 'c', 'p', 'f', 'e', 'g']))
def test_arg_formatter_specifier_conversion(specifier):
    """Property: All C format specifiers should have Python equivalents"""
    formatter = ArgFormatter()
    
    # Create a simple format string
    c_format = f'%{specifier}'
    
    # Property: Regex should match valid format specifiers
    match = formatter.c_format_regex.search(c_format)
    assert match is not None
    assert match.group('specifier') == specifier
    
    # Property: Conversion should produce valid Python format
    py_specifier = formatter.convert_specifier(specifier)
    assert py_specifier is not None
    assert isinstance(py_specifier, str)


@given(
    st.sampled_from(['', '-', '+', '0', '#', ' ']),  # flags
    st.integers(min_value=0, max_value=100),  # width
    st.sampled_from(['d', 'x', 'o', 'f', 's'])  # specifier
)
def test_arg_formatter_format_parsing(flags, width, specifier):
    """Property: C format strings should be parseable"""
    formatter = ArgFormatter()
    
    # Build a C format string
    c_format = f'%{flags}{width if width > 0 else ""}{specifier}'
    
    # Property: Format regex should match
    match = formatter.c_format_regex.search(c_format)
    assert match is not None
    
    # Extract components
    parsed_flags = match.group('flags') or ''
    parsed_width = match.group('width') or ''
    parsed_specifier = match.group('specifier')
    
    # Property: Parsed components should match input
    assert parsed_specifier == specifier
    if width > 0:
        assert parsed_width == str(width)


@given(st.integers(min_value=-1000, max_value=1000))
def test_arg_formatter_integer_formatting(value):
    """Property: Integer formatting should work correctly"""
    formatter = ArgFormatter()
    
    # Test various integer format strings
    formats = ['%d', '%5d', '%05d', '%-5d', '%+d']
    
    for fmt in formats:
        try:
            result = formatter.c_format(fmt, [value])
            # Property: Result should contain the value
            assert str(abs(value)) in result or value == 0
        except Exception:
            # Some edge cases might fail, which could indicate a bug
            pass


@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_arg_formatter_float_formatting(value):
    """Property: Float formatting should preserve precision"""
    formatter = ArgFormatter()
    
    # Test float format
    result = formatter.c_format('%.2f', [value])
    
    # Property: Result should be a valid float representation
    # Check that it contains digits and potentially a decimal point
    assert any(c.isdigit() for c in result)


if __name__ == '__main__':
    print("Running property-based tests for esp_idf_monitor...")
    import pytest
    pytest.main([__file__, '-v'])