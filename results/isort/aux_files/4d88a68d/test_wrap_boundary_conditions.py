#!/usr/bin/env python3
"""Boundary condition tests for isort.wrap module"""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

from hypothesis import given, strategies as st, settings, assume
from isort import wrap
from isort.settings import Config

# Test 1: Boundary conditions for line length
@given(
    line_length=st.integers(min_value=1, max_value=10),  # Very small values
    content=st.text(min_size=20, max_size=100),
)
@settings(max_examples=1000)
def test_extreme_small_line_length(line_length, content):
    """Test with extremely small line lengths."""
    config = Config(line_length=line_length)
    
    # Should not crash even with very small line length
    result = wrap.line(content, "\n", config)
    assert isinstance(result, str)


# Test 2: Line length exactly at boundary
@given(
    content_base=st.text(alphabet='abc', min_size=5, max_size=10),
    padding_size=st.integers(min_value=0, max_value=5),
)
@settings(max_examples=1000)
def test_exact_line_length_boundary(content_base, padding_size):
    """Test when content length exactly matches line length."""
    line_length = len(content_base) + padding_size
    content = content_base + ' ' * padding_size
    
    config = Config(line_length=line_length)
    
    result = wrap.line(content, "\n", config)
    assert isinstance(result, str)
    
    # If content exactly matches line length, it shouldn't be wrapped
    if len(content) == line_length:
        # Should not add line breaks for exact match
        pass  # Just ensure no crash


# Test 3: Wrap length vs line length interaction
@given(
    line_length=st.integers(min_value=20, max_value=100),
    wrap_length_offset=st.integers(min_value=-10, max_value=10),
    from_imports=st.lists(st.text(alphabet='abcdefg', min_size=2, max_size=8), min_size=1, max_size=5),
)
@settings(max_examples=500)
def test_wrap_length_vs_line_length(line_length, wrap_length_offset, from_imports):
    """Test interaction between wrap_length and line_length."""
    wrap_length = max(10, line_length + wrap_length_offset)  # Ensure wrap_length >= 10
    
    config = Config(
        line_length=line_length,
        wrap_length=wrap_length,
    )
    
    import_start = "from module import "
    
    result = wrap.import_statement(
        import_start=import_start,
        from_imports=from_imports.copy(),
        config=config
    )
    
    assert isinstance(result, str)
    
    # The code uses (config.wrap_length or config.line_length)
    # So effective length is wrap_length if set, else line_length
    effective_length = wrap_length
    
    # All imports should be present
    for imp in from_imports:
        assert imp in result


# Test 4: Empty and whitespace-only content
@given(
    whitespace=st.text(alphabet=' \t', max_size=50),
    line_length=st.integers(min_value=10, max_value=100),
)
@settings(max_examples=500)
def test_whitespace_content(whitespace, line_length):
    """Test with whitespace-only content."""
    config = Config(line_length=line_length)
    
    result = wrap.line(whitespace, "\n", config)
    assert isinstance(result, str)
    
    # Whitespace-only content should be returned as-is
    assert result == whitespace


# Test 5: Testing the line_length=10 boundary in balanced wrapping
@given(
    from_imports=st.lists(st.text(alphabet='a', min_size=1, max_size=2), min_size=2, max_size=4),
)
@settings(max_examples=500)
def test_balanced_wrapping_min_line_length(from_imports):
    """Test balanced wrapping at the minimum line length boundary (10)."""
    
    # The code has: while ... and line_length > 10:
    # So test exactly at 10 and 11
    for line_length in [10, 11]:
        config = Config(
            line_length=line_length,
            balanced_wrapping=True,
        )
        
        import_start = "from m import "
        
        result = wrap.import_statement(
            import_start=import_start,
            from_imports=from_imports.copy(),
            config=config
        )
        
        assert isinstance(result, str)
        for imp in from_imports:
            assert imp in result


# Test 6: Comment at exact position
@given(
    base_size=st.integers(min_value=10, max_value=50),
    comment_size=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=500)
def test_comment_at_boundary(base_size, comment_size):
    """Test comments when they push content over the line length."""
    base_content = 'a' * base_size
    comment = 'b' * comment_size
    
    # Set line length to be right at the boundary
    line_length = base_size + 3  # Just enough for " # "
    
    content = f"{base_content} # {comment}"
    
    config = Config(
        line_length=line_length,
        use_parentheses=True,
    )
    
    result = wrap.line(content, "\n", config)
    assert isinstance(result, str)
    
    # Comment should be preserved or NOQA added
    assert '#' in result


# Test 7: Testing pop operations on lists
@given(
    num_imports=st.integers(min_value=0, max_value=3),
)
@settings(max_examples=500)
def test_empty_and_small_import_lists(num_imports):
    """Test with very small or empty import lists."""
    from_imports = [f"item{i}" for i in range(num_imports)]
    
    config = Config(line_length=50)
    import_start = "from module import "
    
    # The code does pop operations on from_imports
    # Make sure it handles empty lists correctly
    result = wrap.import_statement(
        import_start=import_start,
        from_imports=from_imports.copy(),
        config=config
    )
    
    assert isinstance(result, str)
    
    if num_imports == 0:
        # With no imports, should get minimal result
        assert import_start.strip() not in result or result == import_start.strip()
    else:
        # All imports should be present
        for imp in from_imports:
            assert imp in result


# Test 8: Integer overflow protection
@given(
    base_content=st.text(min_size=10, max_size=50),
    line_length=st.integers(min_value=1, max_value=1000000),  # Very large
)
@settings(max_examples=200)
def test_large_line_length(base_content, line_length):
    """Test with very large line lengths."""
    config = Config(line_length=line_length)
    
    result = wrap.line(base_content, "\n", config)
    assert isinstance(result, str)
    
    # With huge line length, content should not be wrapped
    assert '\n' not in result or len(base_content) > line_length


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])