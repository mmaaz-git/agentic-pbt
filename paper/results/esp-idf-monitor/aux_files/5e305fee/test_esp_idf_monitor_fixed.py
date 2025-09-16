#!/usr/bin/env python3
"""Fixed property-based tests for esp_idf_monitor using correct ESP-IDF log format"""

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


# Fixed Test 1: LineMatcher with proper ESP-IDF format
@given(
    tag=st.text(alphabet=st.characters(min_codepoint=33, max_codepoint=126), min_size=1, max_size=20).filter(lambda x: ':' not in x and '(' not in x and ')' not in x),
    level=st.sampled_from(['N', 'E', 'W', 'I', 'D', 'V', '*', '']),
    line_level=st.sampled_from(['E', 'W', 'I', 'D', 'V']),
    timestamp=st.integers(min_value=0, max_value=999999)
)
def test_line_matcher_proper_format(tag, level, line_level, timestamp):
    """Test LineMatcher with proper ESP-IDF log format"""
    # Create filter with specific tag and level
    filter_str = f"{tag}:{level}" if level else tag
    matcher = LineMatcher(filter_str)
    
    # Create a properly formatted ESP-IDF log line: LEVEL (TIMESTAMP) TAG: MESSAGE
    test_line = f"{line_level} ({timestamp}) {tag}: Test message"
    
    # According to the code, the line should match if the filter level >= line level
    level_map = {'N': 0, 'E': 1, 'W': 2, 'I': 3, 'D': 4, 'V': 5, '*': 5, '': 5}
    filter_level = level_map[level if level else 'V']
    line_level_num = level_map[line_level]
    
    expected_match = filter_level >= line_level_num
    actual_match = matcher.match(test_line)
    
    # The match result should align with the level comparison
    assert actual_match == expected_match, f"Filter {filter_str} on line '{test_line}': expected {expected_match}, got {actual_match}"


# Test: Edge case with numeric tags (potential parsing ambiguity)
@given(
    numeric_tag=st.integers(min_value=0, max_value=9999),
    level=st.sampled_from(['E', 'W', 'I', 'D', 'V']),
    timestamp=st.integers(min_value=0, max_value=999999)
)
def test_line_matcher_numeric_tags(numeric_tag, level, timestamp):
    """Test LineMatcher with numeric tags that could be confused with timestamps"""
    tag = str(numeric_tag)
    filter_str = f"{tag}:{level}"
    matcher = LineMatcher(filter_str)
    
    # Proper format with numeric tag
    test_line = f"{level} ({timestamp}) {tag}: Test message"
    
    # Should match since levels are the same
    assert matcher.match(test_line), f"Failed to match numeric tag {tag} in line: {test_line}"


# Test: LineMatcher with wildcard filters
@given(
    tag=st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=3, max_size=10),
    line_level=st.sampled_from(['E', 'W', 'I', 'D', 'V']),
    wildcard_level=st.sampled_from(['N', 'E', 'W', 'I', 'D', 'V']),
    timestamp=st.integers(min_value=0, max_value=999999)
)
def test_line_matcher_wildcard(tag, line_level, wildcard_level, timestamp):
    """Test LineMatcher wildcard (*) behavior"""
    # Create a filter with wildcard
    filter_str = f"*:{wildcard_level}"
    matcher = LineMatcher(filter_str)
    
    # Create test line
    test_line = f"{line_level} ({timestamp}) {tag}: Test message"
    
    # Wildcard should match any tag at the specified level or below
    level_map = {'N': 0, 'E': 1, 'W': 2, 'I': 3, 'D': 4, 'V': 5}
    expected = level_map[wildcard_level] >= level_map[line_level]
    actual = matcher.match(test_line)
    
    assert actual == expected, f"Wildcard filter *:{wildcard_level} on {test_line}: expected {expected}, got {actual}"


# Test for potential bug: What happens with malformed lines?
@given(
    tag=st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=90), min_size=3, max_size=10),
    level=st.sampled_from(['E', 'W', 'I', 'D', 'V'])
)
def test_line_matcher_malformed_lines(tag, level):
    """Test LineMatcher behavior with malformed log lines"""
    matcher = LineMatcher(f"{tag}:{level}")
    
    # Various malformed formats
    malformed_lines = [
        f"{level} {tag}: No timestamp",  # Missing timestamp
        f"{level} ({tag}): Tag in parens",  # Tag where timestamp should be
        f"{level}: No tag",  # Missing tag entirely
        f"X ({tag}): Invalid level",  # Invalid log level
        f"{level} () {tag}: Empty timestamp",  # Empty parentheses
    ]
    
    for line in malformed_lines:
        # The matcher should handle these gracefully (not crash)
        try:
            result = matcher.match(line)
            # Document the actual behavior for each malformed case
            # Most of these should return False or handle gracefully
        except Exception as e:
            assert False, f"LineMatcher crashed on malformed line '{line}': {e}"


# Keep the other working tests from before
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
    
    # Test the translate_eol function
    if eol_mode == 'CRLF':
        result = parser.translate_eol(text_with_lf)
        assert result == text + '\r\n' if text else '\r\n'
    elif eol_mode == 'CR':
        result = parser.translate_eol(text_with_lf)
        assert result == text + '\r' if text else '\r'
    elif eol_mode == 'LF':
        result = parser.translate_eol(text_with_cr)
        assert result == text + '\n' if text else '\n'


if __name__ == '__main__':
    # Run tests with pytest
    import pytest
    pytest.main([__file__, '-v'])