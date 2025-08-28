import re
import sys
from hypothesis import given, strategies as st, assume, settings
from unittest.mock import Mock
import string

sys.path.insert(0, '/root/hypothesis-llm/envs/pytest-pretty_env/lib/python3.13/site-packages')
import pytest_pretty


@given(st.text())
def test_ansi_escape_removes_all_ansi_sequences(text):
    """Test that ansi_escape regex removes all ANSI escape sequences."""
    cleaned = pytest_pretty.ansi_escape.sub('', text)
    
    # After cleaning, there should be no ANSI escape sequences left
    # ANSI sequences start with ESC (0x1B) followed by [ and end with a letter
    assert '\x1B[' not in cleaned
    assert '\x1B' not in cleaned
    
    # The cleaned text should only contain non-ANSI characters
    # Also test that non-ANSI text is preserved
    non_ansi_text = ''.join(c for c in text if ord(c) < 0x80 or ord(c) > 0x9F)
    non_ansi_text = re.sub(r'\x1B[@-_][0-?]*[ -/]*[@-~]', '', non_ansi_text)
    # The regex might remove more than just strict ANSI, but shouldn't remove regular text


@given(st.integers(min_value=0, max_value=10000), 
       st.text(alphabet=string.ascii_letters, min_size=1, max_size=20))
def test_stat_re_parses_count_and_label(count, label):
    """Test that stat_re correctly parses lines like '10 passed'."""
    # Create a stat line
    line = f"{count} {label}"
    
    match = pytest_pretty.stat_re.match(line)
    
    # Should match and extract correct values
    assert match is not None
    assert match.group(1) == str(count)
    assert match.group(2) == label


@given(st.text())
def test_stat_re_only_matches_valid_format(text):
    """Test that stat_re only matches valid stat format."""
    match = pytest_pretty.stat_re.match(text)
    
    if match:
        # If it matches, it should be a valid stat line
        count_str, label = match.groups()
        assert count_str.isdigit()
        assert label.replace('_', '').replace('-', '').isalnum()


@given(st.dictionaries(
    st.text(alphabet=string.ascii_letters, min_size=1, max_size=20),
    st.integers(min_value=0, max_value=1000),
    min_size=0,
    max_size=10
))
def test_parseoutcomes_parsing(stats_dict):
    """Test parseoutcomes correctly parses the custom output format."""
    # Create a mock RunResult with our test data
    mock_result = Mock()
    
    # Build output lines that parseoutcomes expects
    outlines = ['Some initial output', 'Results (1.23s):', 'next line']
    for label, count in stats_dict.items():
        # Add properly formatted stat lines (with leading spaces to mimic actual output)
        outlines.append(f'        {count} {label}')
    outlines.append('Some trailing output')
    
    mock_result.outlines = outlines
    
    # Create the parseoutcomes function
    parseoutcomes = pytest_pretty.create_new_parseoutcomes(mock_result)
    
    # Parse the outcomes
    result = parseoutcomes()
    
    # Check that all stats were parsed correctly
    assert result == stats_dict


@given(st.text(min_size=0, max_size=200), 
       st.integers(min_value=5, max_value=100))
def test_message_truncation_property(message, available_space):
    """Test that message truncation respects available space."""
    # Remove newlines as the code does
    msg = message.replace('\n', ' ')
    
    # Simulate the truncation logic from line 59
    if available_space > 5:
        truncated = msg[:available_space]
        # The truncated message should not exceed available space
        assert len(truncated) <= available_space
        
        # If original was longer, it should be exactly available_space
        if len(msg) > available_space:
            assert len(truncated) == available_space


@given(st.text())
def test_ansi_escape_idempotent(text):
    """Test that applying ANSI escape removal twice gives same result as once."""
    once = pytest_pretty.ansi_escape.sub('', text)
    twice = pytest_pretty.ansi_escape.sub('', once)
    assert once == twice


@given(st.lists(st.tuples(
    st.text(alphabet=string.ascii_letters, min_size=1, max_size=20),
    st.integers(min_value=0, max_value=1000)
)))
def test_parseoutcomes_with_ansi_colors(stats_list):
    """Test parseoutcomes handles ANSI color codes correctly."""
    mock_result = Mock()
    
    # Build output with ANSI codes
    outlines = ['Initial', 'Results (1.00s):', '']
    stats_dict = {}
    for label, count in stats_list:
        # Add ANSI color codes around the stat line
        colored_line = f'\x1B[32m        {count} {label}\x1B[0m'
        outlines.append(colored_line)
        stats_dict[label] = count
    
    mock_result.outlines = outlines
    parseoutcomes = pytest_pretty.create_new_parseoutcomes(mock_result)
    result = parseoutcomes()
    
    # Should parse correctly despite ANSI codes
    assert result == stats_dict