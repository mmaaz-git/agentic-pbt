#!/usr/bin/env python3
"""Edge case and stress tests for esp_idf_monitor"""

from hypothesis import given, strategies as st, assume, settings, example
import sys
import re

sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')

from esp_idf_monitor.base.line_matcher import LineMatcher
from esp_idf_monitor.base.console_parser import ConsoleParser
from esp_idf_monitor.base.output_helpers import add_common_prefix, ANSI_RED, ANSI_NORMAL
from esp_idf_monitor.base.chip_specific_config import get_chip_config, conf
from esp_idf_monitor.base.ansi_color_converter import ANSIColorConverter, ANSI_TO_WINDOWS_COLOR


# Test: LineMatcher filter string parsing edge cases
@given(
    filter_str=st.text(min_size=0, max_size=100)
)
def test_line_matcher_filter_parsing_robustness(filter_str):
    """Test that LineMatcher handles arbitrary filter strings without crashing"""
    try:
        matcher = LineMatcher(filter_str)
        # If it creates successfully, it should have a valid dictionary
        assert isinstance(matcher._dict, dict)
    except ValueError as e:
        # ValueError is acceptable for invalid filter formats
        # Check that the error message is informative
        assert 'filter' in str(e).lower() or ':' in str(e)
    except Exception as e:
        # Any other exception is a bug
        assert False, f"Unexpected exception for filter '{filter_str}': {type(e).__name__}: {e}"


# Test: LineMatcher with special characters in tags
@given(
    tag=st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cf'), blacklist_characters=':()'), min_size=1, max_size=20),
    level=st.sampled_from(['E', 'W', 'I', 'D', 'V'])
)
def test_line_matcher_special_characters(tag, level):
    """Test LineMatcher with tags containing special characters"""
    assume(tag.strip())  # Skip empty/whitespace-only tags
    assume(':' not in tag)  # Colon is the delimiter
    
    try:
        filter_str = f"{tag}:{level}"
        matcher = LineMatcher(filter_str)
        
        # Test with proper ESP-IDF format
        test_line = f"{level} (12345) {tag}: Test message"
        result = matcher.match(test_line)
        
        # Should match since levels are equal
        assert result == True, f"Failed to match tag with special chars: {repr(tag)}"
    except ValueError:
        # Some characters might legitimately cause parsing errors
        pass


# Test: ConsoleParser with various control characters
@given(
    text=st.text(min_size=0, max_size=50),
    eol_mode=st.sampled_from(['CRLF', 'CR', 'LF'])
)
def test_console_parser_control_chars(text, eol_mode):
    """Test ConsoleParser handles various text including control characters"""
    parser = ConsoleParser(eol=eol_mode)
    
    # The translate_eol function should handle any input
    try:
        result = parser.translate_eol(text)
        # Should return a string
        assert isinstance(result, str)
        
        # Check EOL translation is consistent
        if '\n' in text and eol_mode == 'CRLF':
            assert '\r\n' in result or text.endswith('\n')
        elif '\n' in text and eol_mode == 'CR':
            assert '\r' in result or '\n' not in result
        elif '\r' in text and eol_mode == 'LF':
            assert '\n' in result or '\r' not in result
    except Exception as e:
        assert False, f"translate_eol crashed on text {repr(text)}: {e}"


# Test: add_common_prefix with edge cases
@given(
    message=st.text(min_size=0, max_size=200),
    prefix=st.text(min_size=0, max_size=50)
)
def test_add_common_prefix_edge_cases(message, prefix):
    """Test add_common_prefix with various edge cases"""
    result = add_common_prefix(message, prefix=prefix)
    
    # Basic properties
    assert isinstance(result, str)
    
    # Empty message should return empty
    if not message:
        assert result == message
    
    # Lines with only whitespace should not get prefix
    lines = message.split('\n')
    result_lines = result.split('\n')
    
    for orig, res in zip(lines, result_lines):
        if orig.strip():  # Non-empty line
            if prefix:  # Non-empty prefix
                assert res.startswith(f"{prefix} ") or res == f"{prefix} {orig}"
        else:  # Empty or whitespace-only line
            assert res == orig


# Test: Multiple newlines and special line endings
@given(
    lines=st.lists(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=20), min_size=0, max_size=10),
    separator=st.sampled_from(['\n', '\n\n', '\n\n\n']),
    prefix=st.text(min_size=1, max_size=10)
)
def test_add_common_prefix_multiple_newlines(lines, separator, prefix):
    """Test add_common_prefix preserves multiple newlines"""
    message = separator.join(lines)
    result = add_common_prefix(message, prefix=prefix)
    
    # Count newlines - should be preserved
    assert message.count('\n') == result.count('\n'), "Number of newlines should be preserved"


# Test: get_chip_config with unknown chips
@given(
    chip=st.text(min_size=1, max_size=50),
    revision=st.integers()
)
@example(chip='esp32', revision=-1)  # Negative revision
@example(chip='esp32', revision=2**32)  # Very large revision
@example(chip='', revision=0)  # Empty chip name
def test_get_chip_config_robustness(chip, revision):
    """Test get_chip_config handles arbitrary inputs without crashing"""
    try:
        config = get_chip_config(chip, revision)
        
        # Should always return a dictionary
        assert isinstance(config, dict)
        
        # Should have the default keys at minimum
        assert 'reset' in config
        assert 'enter_boot_set' in config
        assert 'enter_boot_unset' in config
        
        # Values should be numeric
        for value in config.values():
            assert isinstance(value, (int, float))
    except Exception as e:
        assert False, f"get_chip_config crashed with chip='{chip}', revision={revision}: {e}"


# Test: LineMatcher with ANSI color codes
@given(
    tag=st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=3, max_size=10),
    level=st.sampled_from(['E', 'W', 'I', 'D', 'V']),
    color_code=st.sampled_from(['\033[0;31m', '\033[1;32m', '\033[0;33m', '\033[1;34m'])
)
def test_line_matcher_with_ansi_colors(tag, level, color_code):
    """Test LineMatcher correctly handles lines with ANSI color codes"""
    matcher = LineMatcher(f"{tag}:{level}")
    
    # Line with ANSI color code at the beginning (as mentioned in the regex)
    colored_line = f"{color_code}{level} (12345) {tag}: Test message"
    
    # Should still match despite color code
    result = matcher.match(colored_line)
    assert result == True, f"Failed to match line with ANSI color: {repr(colored_line)}"


# Test: ANSIColorConverter edge cases (Windows specific but can test logic)
@given(
    data=st.binary(min_size=0, max_size=100)
)
@settings(max_examples=50)
def test_ansi_color_converter_binary_data(data):
    """Test ANSIColorConverter handles arbitrary binary data without crashing"""
    import io
    
    # Create a mock output stream
    output = io.BytesIO()
    converter = ANSIColorConverter(output=output, force_color=True)
    
    try:
        converter.write(data)
        converter.flush()
        # Should not crash on any input
    except Exception as e:
        # Some exceptions are expected for invalid UTF-8, but it shouldn't crash completely
        assert isinstance(e, (UnicodeDecodeError, UnicodeEncodeError, OSError))


# Test: Complex filter combinations
@given(
    tags=st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789_', min_size=1, max_size=10),
        min_size=1, 
        max_size=5,
        unique=True
    ),
    levels=st.lists(
        st.sampled_from(['E', 'W', 'I', 'D', 'V']),
        min_size=1,
        max_size=5
    )
)
def test_line_matcher_complex_filters(tags, levels):
    """Test LineMatcher with complex filter combinations"""
    # Build a complex filter string
    filters = []
    for i, tag in enumerate(tags):
        if i < len(levels):
            filters.append(f"{tag}:{levels[i]}")
        else:
            filters.append(tag)  # No level specified
    
    filter_str = ' '.join(filters)
    
    try:
        matcher = LineMatcher(filter_str)
        
        # Test matching with each tag
        for tag, level in zip(tags, levels):
            test_line = f"{level} (12345) {tag}: Test message"
            result = matcher.match(test_line)
            # Should match since we added this tag to the filter
            assert isinstance(result, bool)  # Just check it returns a bool
    except ValueError:
        # Complex filters might have conflicts
        pass


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])