import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume, example
import fire.custom_descriptions as custom_descriptions
import fire.formatting as formatting


@given(st.text(alphabet=st.characters(min_codepoint=0x1F600, max_codepoint=0x1F64F), min_size=1, max_size=10))  # Emoji
def test_emoji_handling(text):
    summary = custom_descriptions.GetStringTypeSummary(text, 50, 80)
    assert summary.startswith('"') and summary.endswith('"')
    # Content should preserve emojis
    content = summary[1:-1]
    if '...' not in content:
        assert content == text


@given(st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"], min_codepoint=0x4E00, max_codepoint=0x9FFF), min_size=1, max_size=10))  # CJK characters
def test_cjk_characters(text):
    summary = custom_descriptions.GetStringTypeSummary(text, 50, 80)
    assert summary.startswith('"') and summary.endswith('"')
    content = summary[1:-1]
    if '...' not in content:
        assert content == text


@given(st.text(alphabet=st.sampled_from(['\n', '\r', '\t', '\0', '\x0b', '\x0c']), min_size=1, max_size=5))  # Control characters
def test_control_characters(text):
    summary = custom_descriptions.GetStringTypeSummary(text, 50, 80)
    assert summary.startswith('"') and summary.endswith('"')
    # Should handle control characters without crashing
    assert isinstance(summary, str)


@given(st.text(alphabet=st.sampled_from(['‚', '„', '"', '"', '«', '»', '‹', '›']), min_size=1, max_size=5))  # Special quote marks
def test_special_quotes(text):
    summary = custom_descriptions.GetStringTypeSummary(text, 50, 80)
    # Should still use regular double quotes for wrapping
    assert summary.startswith('"') and summary.endswith('"')
    assert summary[0] == '"' and summary[-1] == '"'  # Regular ASCII quotes


@given(st.text(min_size=1, max_size=100).filter(lambda x: '\x00' not in x), 
       st.integers(min_value=5, max_value=50))
def test_unicode_truncation_boundary(text, available_space):
    # Test that truncation doesn't break unicode characters
    summary = custom_descriptions.GetStringTypeSummary(text, available_space, 80)
    
    # Should not raise UnicodeError
    assert isinstance(summary, str)
    
    # Should be valid UTF-8
    try:
        summary.encode('utf-8').decode('utf-8')
    except UnicodeDecodeError:
        assert False, f"Summary produced invalid UTF-8: {repr(summary)}"


@example(text='💀' * 10, available_space=8, line_length=80)  # Specific edge case
@given(st.text(alphabet='💀', min_size=0, max_size=20), 
       st.integers(min_value=5, max_value=15), 
       st.integers(min_value=80, max_value=100))
def test_emoji_truncation(text, available_space, line_length):
    summary = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
    
    # Should handle emoji truncation properly
    assert summary.startswith('"') and summary.endswith('"')
    
    # If truncated, should have ellipsis
    if len(text) + 2 > available_space:
        assert '...' in summary


@given(st.text())
def test_consistent_type_check(text):
    # GetSummary and GetDescription should handle strings consistently
    summary = custom_descriptions.GetSummary(text, 50, 80)
    description = custom_descriptions.GetDescription(text, 50, 80)
    
    # Both should return something for strings
    assert summary is not None
    assert description is not None
    
    # Both should be strings themselves
    assert isinstance(summary, str)
    assert isinstance(description, str)


@given(st.text(alphabet=st.sampled_from(['\\', '/', '|', '-', '_', '.', ',', '!', '?', '@', '#', '$', '%', '^', '&', '*', '(', ')', '[', ']', '{', '}', '<', '>', ':', ';', "'", '`', '~', '=', '+']), min_size=1, max_size=20))
def test_special_ascii_characters(text):
    summary = custom_descriptions.GetStringTypeSummary(text, 50, 80)
    description = custom_descriptions.GetStringTypeDescription(text, 50, 80)
    
    # Should handle all ASCII special characters
    assert summary.startswith('"') and summary.endswith('"')
    assert description.startswith('The string "') and description.endswith('"')
    
    # Content should be preserved
    summary_content = summary[1:-1]
    if '...' not in summary_content:
        assert summary_content == text


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])