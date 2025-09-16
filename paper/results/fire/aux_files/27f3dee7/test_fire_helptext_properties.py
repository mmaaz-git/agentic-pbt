"""Property-based tests for fire.helptext module using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import collections
from fire import helptext
from fire import formatting


@given(st.lists(st.text(min_size=1, max_size=50)))
def test_get_short_flags_returns_unique_chars(flags):
    """_GetShortFlags should only return characters that appear as first char exactly once."""
    result = helptext._GetShortFlags(flags)
    
    # Get all first characters
    first_chars = [f[0] for f in flags if f]
    char_counts = collections.Counter(first_chars)
    
    # The result should contain only characters that appear exactly once
    for char in result:
        assert char_counts[char] == 1, f"Character {char} appears {char_counts[char]} times, not 1"
    
    # All unique first characters should be in the result
    expected = [char for char, count in char_counts.items() if count == 1]
    assert sorted(result) == sorted(expected)


@given(st.lists(st.text(min_size=0, max_size=10)))
def test_get_short_flags_preserves_order(flags):
    """_GetShortFlags should preserve the order of flags."""
    result = helptext._GetShortFlags(flags)
    
    # The result should be in the same order as the input
    first_chars = [f[0] if f else '' for f in flags]
    char_counts = collections.Counter(first_chars)
    
    # Filter to get expected result maintaining order
    expected = []
    seen = set()
    for f in flags:
        if f and f[0] not in seen and char_counts[f[0]] == 1:
            expected.append(f[0])
            seen.add(f[0])
    
    assert result == expected


@given(
    st.text(min_size=0, max_size=200),
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=1, max_value=200)
)
def test_ellipsis_truncate_respects_available_space(text, available_space, line_length):
    """EllipsisTruncate should never exceed available_space when truncating."""
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    # If available_space is less than ellipsis length, use line_length
    ellipsis_len = len('...')
    effective_space = available_space if available_space >= ellipsis_len else line_length
    
    # Result should never exceed the effective space
    assert len(result) <= effective_space, f"Result '{result}' ({len(result)}) exceeds space {effective_space}"
    
    # If text fits, it should be unchanged
    if len(text) <= effective_space:
        assert result == text
    # If text doesn't fit, it should be truncated with ellipsis
    else:
        assert result.endswith('...')
        assert len(result) == effective_space


@given(
    st.text(min_size=0, max_size=200),
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=1, max_value=200)
)
def test_ellipsis_middle_truncate_respects_available_space(text, available_space, line_length):
    """EllipsisMiddleTruncate should never exceed available_space when truncating."""
    result = formatting.EllipsisMiddleTruncate(text, available_space, line_length)
    
    # If available_space is less than ellipsis length, use line_length
    ellipsis_len = len('...')
    effective_space = available_space if available_space >= ellipsis_len else line_length
    
    # Result should never exceed the effective space
    assert len(result) <= effective_space, f"Result '{result}' ({len(result)}) exceeds space {effective_space}"
    
    # If text fits, it should be unchanged
    if len(text) < effective_space:
        assert result == text
    # If text doesn't fit, it should contain ellipsis in the middle
    elif len(text) >= effective_space:
        assert '...' in result
        assert len(result) == effective_space
        # Check that we have text from both start and end
        if effective_space > ellipsis_len:
            available_string_len = effective_space - ellipsis_len
            first_half_len = int(available_string_len / 2)
            second_half_len = available_string_len - first_half_len
            assert result.startswith(text[:first_half_len])
            assert result.endswith(text[-second_half_len:])


@given(
    st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=10),
    st.text(min_size=1, max_size=5),
    st.integers(min_value=10, max_value=100)
)
def test_wrapped_join_respects_width(items, separator, width):
    """WrappedJoin should respect the width constraint for each line."""
    lines = formatting.WrappedJoin(items, separator, width)
    
    # Each line should not exceed the width
    for line in lines:
        assert len(line) <= width, f"Line '{line}' ({len(line)}) exceeds width {width}"
    
    # If we rejoin the lines, we should get all items
    if items:
        rejoined = ''.join(lines).replace(separator, '|')
        original = '|'.join(items)
        # The rejoined text should contain all items
        for item in items:
            assert item in ''.join(lines), f"Item '{item}' not found in result"


@given(
    st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5),
    st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5)
)
def test_action_group_maintains_consistency(names, members):
    """ActionGroup should maintain consistency between names and members lists."""
    # Create an ActionGroup
    group = helptext.ActionGroup(name='test', plural='tests')
    
    # Add items one by one
    for i in range(min(len(names), len(members))):
        group.Add(name=names[i], member=members[i])
    
    # Check consistency
    assert len(group.names) == len(group.members)
    assert len(group.names) == min(len(names), len(members))
    
    # Check GetItems returns correct pairs
    items = list(group.GetItems())
    assert len(items) == len(group.names)
    
    for i, (name, member) in enumerate(items):
        assert name == names[i]
        assert member == members[i]


@given(st.text(min_size=0, max_size=100), st.integers(min_value=0, max_value=10))
def test_indent_preserves_content(text, spaces):
    """Indent should preserve text content while adding indentation."""
    result = formatting.Indent(text, spaces)
    
    # Each line should be indented by the specified number of spaces
    lines_original = text.split('\n')
    lines_result = result.split('\n')
    
    assert len(lines_original) == len(lines_result)
    
    for orig, res in zip(lines_original, lines_result):
        if orig:  # Non-empty lines should be indented
            assert res == ' ' * spaces + orig
        else:  # Empty lines should remain empty
            assert res == orig


@given(st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122))))
def test_get_short_flags_with_duplicates(flags):
    """Test _GetShortFlags handles duplicates correctly."""
    # Add some intentional duplicates
    if flags:
        flags_with_dups = flags + [flags[0], flags[0]] if len(flags) > 0 else flags
        result = helptext._GetShortFlags(flags_with_dups)
        
        # No character from a duplicate should be in result
        first_chars = [f[0] for f in flags_with_dups if f]
        char_counts = collections.Counter(first_chars)
        
        for char in result:
            assert char_counts[char] == 1
        
        # Result should be empty if all are duplicates
        if all(count > 1 for count in char_counts.values()):
            assert result == []


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])