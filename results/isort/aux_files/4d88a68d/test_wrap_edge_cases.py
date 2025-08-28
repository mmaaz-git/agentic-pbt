#!/usr/bin/env python3
"""Edge case tests for isort.wrap module"""

import sys
import re
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

from hypothesis import given, assume, strategies as st, settings, example
from hypothesis.strategies import composite
from isort import wrap
from isort.settings import Config
from isort.wrap_modes import WrapModes as Modes

# Test specific edge cases around balanced wrapping
@given(
    from_imports=st.lists(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10), min_size=2, max_size=10),
    line_length=st.integers(min_value=10, max_value=50),
)
@settings(max_examples=1000)  
def test_balanced_wrapping_edge_case(from_imports, line_length):
    """Test balanced wrapping with various configurations."""
    config = Config(
        line_length=line_length,
        balanced_wrapping=True,
        use_parentheses=True,
    )
    
    import_start = "from module import "
    
    result = wrap.import_statement(
        import_start=import_start,
        from_imports=from_imports,
        config=config
    )
    
    # Property: Result should be a valid string
    assert isinstance(result, str)
    
    # Property: All imports should be in result
    for imp in from_imports:
        assert imp in result
    

# Test edge case with empty from_imports
@given(
    import_start=st.text(min_size=1, max_size=50),
    config_balanced=st.booleans(),
)
@settings(max_examples=500)
def test_empty_from_imports(import_start, config_balanced):
    """Test import_statement with empty from_imports list."""
    config = Config(balanced_wrapping=config_balanced)
    
    result = wrap.import_statement(
        import_start=import_start,
        from_imports=[],  # Empty list
        config=config
    )
    
    # With empty imports, should get minimal result
    assert isinstance(result, str)
    

# Test line wrapping with special splitters
@given(
    prefix=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=5, max_size=20),
    suffix=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=5, max_size=20),
    splitter=st.sampled_from(["import ", "cimport ", ".", "as "]),
)
@settings(max_examples=1000)
def test_line_splitter_behavior(prefix, suffix, splitter):
    """Test line splitting behavior with different splitters."""
    # Skip if splitter would be at the start
    assume(not prefix.startswith(splitter.strip()))
    
    content = prefix + splitter + suffix
    config = Config(line_length=20, use_parentheses=True)
    
    result = wrap.line(content, "\n", config)
    
    # Property: Result should be a string
    assert isinstance(result, str)
    
    # Property: Essential parts should be preserved
    # (though they might be reformatted)
    assert prefix in result or "\\" in result or "(" in result


# Test interaction between comments and NOQA mode
@given(
    content=st.text(alphabet='abcdefghijklmnopqrstuvwxyz #', min_size=10, max_size=200),
    line_length=st.integers(min_value=10, max_value=50),
)
@settings(max_examples=500)
def test_noqa_mode_interaction(content, line_length):
    """Test NOQA mode with various content."""
    config = Config(
        line_length=line_length,
        multi_line_output=Modes.NOQA
    )
    
    result = wrap.line(content, "\n", config)
    
    # In NOQA mode, if line is too long and doesn't have NOQA, it should add it
    if len(content) > line_length and "# NOQA" not in content:
        assert "NOQA" in result
    
    # Result should always be a string
    assert isinstance(result, str)


# Test with very small line lengths to stress test the algorithm
@given(
    from_imports=st.lists(st.text(alphabet='abc', min_size=1, max_size=5), min_size=1, max_size=5),
)
@settings(max_examples=500)
def test_very_small_line_length(from_imports):
    """Test with very small line lengths."""
    config = Config(
        line_length=10,  # Very small
        wrap_length=8,   # Even smaller
        balanced_wrapping=True,
    )
    
    import_start = "from m import "
    
    # This might trigger edge cases in the balanced wrapping algorithm
    result = wrap.import_statement(
        import_start=import_start,
        from_imports=from_imports,
        config=config
    )
    
    assert isinstance(result, str)
    for imp in from_imports:
        assert imp in result


# Test special characters in imports  
@given(
    from_imports=st.lists(
        st.from_regex(r'[a-zA-Z_][a-zA-Z0-9_]*', fullmatch=True),
        min_size=1,
        max_size=10
    ),
    use_explode=st.booleans(),
)
@settings(max_examples=500)
def test_valid_identifiers_only(from_imports, use_explode):
    """Test with valid Python identifiers."""
    config = Config()
    
    result = wrap.import_statement(
        import_start="from module import ",
        from_imports=from_imports,
        config=config,
        explode=use_explode
    )
    
    assert isinstance(result, str)
    
    # All imports should be present
    for imp in from_imports:
        assert imp in result
        
    # If exploded with multiple imports, should have newlines
    if use_explode and len(from_imports) > 1:
        assert "\n" in result


# Test comment prefix edge cases
@given(
    base_content=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=20, max_size=100),
    comment_text=st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=1, max_size=20),
    comment_prefix=st.sampled_from([' #', '  #', '   #', '\t#']),
)
@settings(max_examples=500)
def test_comment_prefix_handling(base_content, comment_text, comment_prefix):
    """Test different comment prefix formats."""
    content = f"{base_content} #{comment_text}"
    
    config = Config(
        line_length=30,
        comment_prefix=comment_prefix,
        use_parentheses=True
    )
    
    result = wrap.line(content, "\n", config)
    
    # Result should preserve the comment in some form
    assert isinstance(result, str)
    # Comment text should still be there (unless it's in NOQA mode)
    assert comment_text in result or "NOQA" in result or "\\" in result


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])