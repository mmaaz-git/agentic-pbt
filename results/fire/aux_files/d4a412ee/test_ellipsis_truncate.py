import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, example
import fire.formatting as formatting


@given(st.text(), st.integers(min_value=-10, max_value=200), st.integers(min_value=10, max_value=200))
def test_ellipsis_truncate_direct(text, available_space, line_length):
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    # Basic invariant: result should be a string
    assert isinstance(result, str)
    
    # If available_space < 3 (len of "..."), should use line_length
    effective_space = available_space if available_space >= 3 else line_length
    
    # Length constraint
    if len(text) <= effective_space:
        assert result == text, f"Should not truncate when text fits"
    else:
        assert result.endswith('...'), f"Should end with ellipsis when truncated"
        assert len(result) == effective_space, f"Length should match effective_space"
        # The non-ellipsis part should be a prefix of the original
        assert text.startswith(result[:-3]), f"Truncated part should be prefix"


@example(text='a', available_space=0, line_length=80)
@example(text='ab', available_space=1, line_length=80)
@example(text='abc', available_space=2, line_length=80)
@example(text='abcd', available_space=3, line_length=80)
@given(st.text(min_size=1, max_size=10), st.integers(min_value=0, max_value=2), st.integers(min_value=80, max_value=100))
def test_ellipsis_truncate_boundary_cases(text, available_space, line_length):
    # Test when available_space < len("...")
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    # Should fall back to line_length
    if len(text) <= line_length:
        assert result == text
    else:
        assert result.endswith('...')
        assert len(result) == line_length


@given(st.text(min_size=10, max_size=100), st.integers(min_value=5, max_value=20), st.integers(min_value=80, max_value=100))
def test_ellipsis_truncate_always_preserves_prefix(text, available_space, line_length):
    result = formatting.EllipsisTruncate(text, available_space, line_length)
    
    if '...' in result:
        prefix = result[:-3]
        assert text.startswith(prefix), f"Result should preserve text prefix"
        assert len(prefix) == available_space - 3 or len(prefix) == line_length - 3


@given(st.text())
def test_ellipsis_truncate_with_exact_space(text):
    # Test when available_space exactly matches text length
    available_space = len(text)
    result = formatting.EllipsisTruncate(text, available_space, 80)
    
    assert result == text, f"Should not truncate when space exactly matches"


@given(st.text(min_size=4, max_size=100))
def test_ellipsis_truncate_one_less_space(text):
    # Test when available_space is exactly 1 less than needed
    available_space = len(text) - 1
    if available_space < 3:
        available_space = 80  # Use line_length
    
    result = formatting.EllipsisTruncate(text, available_space, 80)
    
    if available_space >= len(text):
        assert result == text
    else:
        assert result.endswith('...')
        assert len(result) == available_space


@given(st.text(alphabet=st.characters(min_codepoint=0x1F600, max_codepoint=0x1F64F), min_size=1, max_size=20), 
       st.integers(min_value=5, max_value=10))
def test_ellipsis_truncate_emoji_boundary(text, available_space):
    # Test that emoji truncation doesn't break characters
    result = formatting.EllipsisTruncate(text, available_space, 80)
    
    # Should be valid UTF-8
    try:
        result.encode('utf-8').decode('utf-8')
    except UnicodeDecodeError:
        assert False, f"Result is not valid UTF-8: {repr(result)}"
    
    # Should either fit completely or be truncated with ellipsis
    if len(result) > len(text):
        assert False, f"Result should not be longer than original"
    
    if '...' in result:
        assert result.endswith('...')


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])