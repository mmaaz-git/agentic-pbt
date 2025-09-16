#!/usr/bin/env python3
"""Property-based tests for esp_idf_monitor using Hypothesis"""

import re
from hypothesis import given, strategies as st, assume, settings
import sys
import os

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')

# Import the modules to test
from esp_idf_monitor.base.line_matcher import LineMatcher
from esp_idf_monitor.base.console_parser import ConsoleParser
from esp_idf_monitor.base.output_helpers import add_common_prefix
from esp_idf_monitor.base.chip_specific_config import get_chip_config


# Test 1: LineMatcher log level filtering properties
@given(
    tag=st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1, max_size=20).filter(lambda x: ':' not in x),
    level=st.sampled_from(['N', 'E', 'W', 'I', 'D', 'V', '*', '']),
    line_level=st.sampled_from(['E', 'W', 'I', 'D', 'V'])
)
def test_line_matcher_level_filtering(tag, level, line_level):
    """Test that LineMatcher correctly filters based on log levels"""
    # Create filter with specific tag and level
    filter_str = f"{tag}:{level}" if level else tag
    matcher = LineMatcher(filter_str)
    
    # Create a log line with the specified level
    test_line = f"{line_level} ({tag}): Test message"
    
    # According to the code, the line should match if the filter level >= line level
    level_map = {'N': 0, 'E': 1, 'W': 2, 'I': 3, 'D': 4, 'V': 5, '*': 5, '': 5}
    filter_level = level_map[level if level else 'V']
    line_level_num = level_map[line_level]
    
    expected_match = filter_level >= line_level_num
    actual_match = matcher.match(test_line)
    
    # The match result should align with the level comparison
    assert actual_match == expected_match, f"Filter {filter_str} on line '{test_line}': expected {expected_match}, got {actual_match}"


# Test 2: LineMatcher default behavior
@given(line_level=st.sampled_from(['E', 'W', 'I', 'D', 'V']))
def test_line_matcher_default_prints_all(line_level):
    """Test that default LineMatcher (empty filter) prints everything at verbose level"""
    matcher = LineMatcher('')  # Empty filter should default to '*:V'
    
    # Any log line should match with default settings
    test_line = f"{line_level} (TestTag): Test message"
    assert matcher.match(test_line), f"Default matcher should match all log lines, but didn't match: {test_line}"


# Test 3: ConsoleParser EOL translation properties
@given(
    text=st.text(alphabet=st.characters(blacklist_characters='\r\n'), min_size=0, max_size=100),
    eol_mode=st.sampled_from(['CRLF', 'CR', 'LF'])
)
def test_console_parser_eol_translation(text, eol_mode):
    """Test ConsoleParser EOL translation preserves content and applies correct endings"""
    parser = ConsoleParser(eol=eol_mode)
    
    # Add different line endings to the text
    text_with_lf = text + '\n' if text else '\n'
    text_with_cr = text + '\r' if text else '\r'
    text_with_crlf = text + '\r\n' if text else '\r\n'
    
    # Test the translate_eol function
    if eol_mode == 'CRLF':
        # Should convert \n to \r\n
        result = parser.translate_eol(text_with_lf)
        assert result == text + '\r\n' if text else '\r\n'
    elif eol_mode == 'CR':
        # Should convert \n to \r
        result = parser.translate_eol(text_with_lf)
        assert result == text + '\r' if text else '\r'
    elif eol_mode == 'LF':
        # Should convert \r to \n
        result = parser.translate_eol(text_with_cr)
        assert result == text + '\n' if text else '\n'


# Test 4: add_common_prefix function property
@given(
    lines=st.lists(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=50), min_size=1, max_size=10),
    prefix=st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1, max_size=10)
)
def test_add_common_prefix_property(lines, prefix):
    """Test that add_common_prefix adds prefix only to non-empty lines"""
    message = '\n'.join(lines)
    result = add_common_prefix(message, prefix=prefix)
    
    result_lines = result.split('\n')
    original_lines = message.split('\n')
    
    # Property: non-empty lines should have prefix, empty lines should not
    for orig, res in zip(original_lines, result_lines):
        if orig.strip():  # Non-empty line
            assert res.startswith(f"{prefix} "), f"Non-empty line '{orig}' should start with prefix '{prefix} ', got '{res}'"
            assert res == f"{prefix} {orig}", f"Expected '{prefix} {orig}', got '{res}'"
        else:  # Empty line
            assert res == orig, f"Empty line should remain unchanged, but '{orig}' became '{res}'"


# Test 5: get_chip_config inheritance property
@given(
    chip=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=3, max_size=10),
    revision=st.integers(min_value=0, max_value=200)
)
def test_get_chip_config_always_returns_config(chip, revision):
    """Test that get_chip_config always returns at least the default configuration"""
    config = get_chip_config(chip, revision)
    
    # Property: should always return a dict with expected keys
    assert isinstance(config, dict), f"get_chip_config should return a dict, got {type(config)}"
    
    # Should at least have the default keys
    expected_keys = {'reset', 'enter_boot_set', 'enter_boot_unset'}
    assert expected_keys.issubset(config.keys()), f"Config missing expected keys. Got: {config.keys()}"
    
    # All values should be numeric (floats)
    for key, value in config.items():
        assert isinstance(value, (int, float)), f"Config value for '{key}' should be numeric, got {type(value)}: {value}"
        assert value >= 0, f"Config value for '{key}' should be non-negative, got {value}"


# Test 6: get_chip_config known chips test
@given(revision=st.integers(min_value=0, max_value=200))
def test_get_chip_config_esp32_specific(revision):
    """Test ESP32 chip config returns appropriate values based on revision"""
    config = get_chip_config('esp32', revision)
    
    # ESP32 has special config for revision < 100 and >= 100
    if revision < 100:
        # Should use revision 0 config
        assert config['enter_boot_set'] == 1.3
        assert config['enter_boot_unset'] == 0.45
    else:
        # Should use revision 100 config
        assert config['enter_boot_set'] == 0.1
        assert config['enter_boot_unset'] == 0.05


# Test 7: LineMatcher filter parsing property
@given(
    tags=st.lists(
        st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1, max_size=10).filter(lambda x: ':' not in x),
        min_size=1,
        max_size=5,
        unique=True
    ),
    levels=st.lists(st.sampled_from(['N', 'E', 'W', 'I', 'D', 'V', '*', '']), min_size=1, max_size=5)
)
def test_line_matcher_multiple_filters(tags, levels):
    """Test LineMatcher with multiple filter specifications"""
    # Create filter string with multiple tag:level pairs
    filter_parts = []
    for i in range(min(len(tags), len(levels))):
        if levels[i]:
            filter_parts.append(f"{tags[i]}:{levels[i]}")
        else:
            filter_parts.append(tags[i])
    
    filter_str = ' '.join(filter_parts)
    
    # This should not raise an exception
    try:
        matcher = LineMatcher(filter_str)
        # The matcher should be created successfully
        assert matcher._dict is not None
        assert len(matcher._dict) >= len(filter_parts)
    except ValueError:
        # Should only raise ValueError for invalid formats, not for valid ones
        assert False, f"Valid filter string '{filter_str}' raised ValueError"


# Test 8: ConsoleParser key parsing consistency
@given(key=st.text(min_size=1, max_size=1))
def test_console_parser_key_consistency(key):
    """Test that ConsoleParser.parse returns consistent results for the same key"""
    parser = ConsoleParser()
    
    # Parse the same key twice
    result1 = parser.parse(key)
    # Reset the state if needed
    parser._pressed_menu_key = False
    result2 = parser.parse(key)
    
    # For non-menu keys, results should be consistent
    if key not in ['\x14']:  # MENU_KEY is Ctrl-T (0x14)
        assert result1 == result2, f"Parsing key '{repr(key)}' gave inconsistent results: {result1} vs {result2}"


if __name__ == '__main__':
    # Run tests with pytest
    import pytest
    pytest.main([__file__, '-v'])