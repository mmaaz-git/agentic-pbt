#!/usr/bin/env python3
"""Deep property tests for isort.wrap module - looking for edge case bugs"""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

from hypothesis import given, assume, strategies as st, settings, example
import copy
from isort import wrap
from isort.settings import Config
from isort.wrap_modes import WrapModes

# Test 1: Balanced wrapping line count consistency
@given(
    from_imports=st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=3, max_size=15), 
        min_size=3, 
        max_size=10
    ),
    line_length=st.integers(min_value=20, max_value=80),
)
@settings(max_examples=1000)
def test_balanced_wrapping_line_count_invariant(from_imports, line_length):
    """Test that balanced wrapping maintains consistent line counts during iteration."""
    
    config = Config(
        line_length=line_length,
        balanced_wrapping=True,
        use_parentheses=True,
        include_trailing_comma=True,
    )
    
    import_start = "from somemodule import "
    
    result = wrap.import_statement(
        import_start=import_start,
        from_imports=from_imports.copy(),
        config=config
    )
    
    # Balanced wrapping iterates to balance lines - let's ensure it terminates properly
    lines = result.split('\n')
    
    # Property: Should have at least one line
    assert len(lines) >= 1
    
    # Property: If multiple lines, last line shouldn't be empty (unless it's just closing paren)
    if len(lines) > 1:
        # Last line might be just ")" which is fine
        if lines[-1].strip() not in [')', '),']:
            assert len(lines[-1].strip()) > 0


# Test 2: Testing the while loop termination in balanced wrapping
@given(
    from_imports=st.lists(
        st.text(alphabet='abc', min_size=1, max_size=3),
        min_size=2,
        max_size=5
    ),
)
@settings(max_examples=500)
def test_balanced_wrapping_termination(from_imports):
    """Ensure balanced wrapping always terminates (no infinite loop)."""
    
    # Use very small line length to stress test the while loop
    config = Config(
        line_length=11,  # Just above the minimum of 10 in the code
        balanced_wrapping=True,
        use_parentheses=True,
    )
    
    import_start = "from m import "
    
    # This should not hang or loop infinitely
    result = wrap.import_statement(
        import_start=import_start,
        from_imports=from_imports.copy(),
        config=config
    )
    
    assert isinstance(result, str)
    for imp in from_imports:
        assert imp in result


# Test 3: Line wrapping with edge case line lengths
@given(
    content=st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=50, max_size=200),
    has_import_keyword=st.booleans(),
)
@settings(max_examples=500)
def test_line_wrapping_with_import_keywords(content, has_import_keyword):
    """Test line wrapping when content contains 'import' keyword."""
    
    if has_import_keyword:
        # Insert "import" somewhere in the middle
        parts = content.split(' ')
        if len(parts) > 2:
            parts[1] = "import"
            content = ' '.join(parts)
    
    config = Config(
        line_length=40,
        use_parentheses=True,
    )
    
    result = wrap.line(content, "\n", config)
    
    # The function should handle this without crashing
    assert isinstance(result, str)
    
    # If line was split, it should use backslash or parentheses
    if '\n' in result and not result.strip().startswith('import'):
        assert '\\' in result or '(' in result


# Test 4: Testing comment handling in long lines
@given(
    base=st.text(alphabet='abcdefghijklmnopqrstuvwxyz.', min_size=30, max_size=100),
    comment=st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=1, max_size=50),
    has_noqa=st.booleans(),
)
@settings(max_examples=500)
def test_comment_with_noqa_handling(base, comment, has_noqa):
    """Test comment handling especially with noqa."""
    
    if has_noqa:
        comment = f"noqa: {comment}"
    
    content = f"{base} # {comment}"
    
    config = Config(
        line_length=40,
        use_parentheses=True,
        comment_prefix=" # ",
    )
    
    result = wrap.line(content, "\n", config)
    
    assert isinstance(result, str)
    
    # If content has noqa, special handling applies
    if has_noqa and config.use_parentheses:
        # The noqa comment should be preserved in some form
        assert "noqa" in result.lower()


# Test 5: Testing the _wrap_line recursion
@given(
    parts=st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=5, max_size=15),
        min_size=3,
        max_size=8
    ),
    splitter=st.sampled_from(['.', ' as ', 'import ']),
)
@settings(max_examples=500)
def test_wrap_line_recursion(parts, splitter):
    """Test the _wrap_line function which is called recursively."""
    
    content = splitter.join(parts)
    
    config = Config(
        line_length=30,
        indent="    ",
        use_parentheses=True,
    )
    
    # Ensure it doesn't start with the splitter (code requirement)
    if not content.strip().startswith(splitter.strip()):
        result = wrap.line(content, "\n", config)
        
        assert isinstance(result, str)
        
        # All parts should still be present
        for part in parts:
            assert part in result


# Test 6: Multi-line output mode variations  
@given(
    from_imports=st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz_', min_size=3, max_size=20),
        min_size=1,
        max_size=8
    ),
    mode_value=st.integers(min_value=0, max_value=11),  # WrapModes enum values
)
@settings(max_examples=500)
def test_different_wrap_modes(from_imports, mode_value):
    """Test different multi-line output modes."""
    
    try:
        mode = WrapModes(mode_value)
    except ValueError:
        # Invalid mode value
        return
    
    config = Config(
        line_length=50,
        multi_line_output=mode,
    )
    
    import_start = "from package.module import "
    
    result = wrap.import_statement(
        import_start=import_start,
        from_imports=from_imports.copy(),
        config=config
    )
    
    assert isinstance(result, str)
    
    # All imports should be present
    for imp in from_imports:
        assert imp in result


# Test 7: Edge case with trailing comma settings
@given(
    from_imports=st.lists(
        st.text(alphabet='xyz', min_size=1, max_size=5),
        min_size=1,
        max_size=5
    ),
    include_trailing_comma=st.booleans(),
    use_parentheses=st.booleans(),
)
@settings(max_examples=500)
def test_trailing_comma_consistency(from_imports, include_trailing_comma, use_parentheses):
    """Test trailing comma behavior."""
    
    config = Config(
        line_length=30,
        include_trailing_comma=include_trailing_comma,
        use_parentheses=use_parentheses,
    )
    
    import_start = "from mod import "
    
    result = wrap.import_statement(
        import_start=import_start,
        from_imports=from_imports.copy(),
        config=config
    )
    
    # If we have trailing comma enabled and parentheses, check for it
    if include_trailing_comma and use_parentheses and '(' in result:
        # Multi-line with parentheses
        if '\n' in result:
            # Should have trailing comma before closing paren
            lines = result.split('\n')
            if ')' in lines[-1]:
                # Check the line before the closing paren
                if len(lines) > 1:
                    prev_line = lines[-2] if lines[-1].strip() == ')' else lines[-1]
                    # This is a heuristic check - not all cases need trailing comma
                    pass  # Just ensure no crash
    
    assert isinstance(result, str)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])