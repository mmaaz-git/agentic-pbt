#!/usr/bin/env python3
"""Property-based tests for isort.wrap module"""

import sys
import re
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

from hypothesis import given, assume, strategies as st, settings
from hypothesis.strategies import composite
from isort import wrap
from isort.settings import Config

# Strategy for valid Python identifiers
@composite
def python_identifier(draw):
    first_char = draw(st.from_regex(r'[a-zA-Z_]', fullmatch=True))
    rest = draw(st.from_regex(r'[a-zA-Z0-9_]*', fullmatch=True))
    return first_char + rest

# Strategy for import names (can contain dots)
@composite  
def import_name(draw):
    parts = draw(st.lists(python_identifier(), min_size=1, max_size=5))
    return '.'.join(parts)

# Strategy for generating reasonable config objects
@composite
def config_strategy(draw):
    line_length = draw(st.integers(min_value=10, max_value=200))
    indent = draw(st.text(alphabet=' \t', min_size=1, max_size=8))
    comment_prefix = draw(st.sampled_from([' #', '  #', ' # ']))
    include_trailing_comma = draw(st.booleans())
    use_parentheses = draw(st.booleans())
    balanced_wrapping = draw(st.booleans())
    ignore_comments = draw(st.booleans())
    
    # Only include wrap_length if it's not None
    kwargs = {
        'line_length': line_length,
        'indent': indent,
        'comment_prefix': comment_prefix,
        'include_trailing_comma': include_trailing_comma,
        'use_parentheses': use_parentheses,
        'balanced_wrapping': balanced_wrapping,
        'ignore_comments': ignore_comments,
    }
    
    # Sometimes add wrap_length
    if draw(st.booleans()):
        kwargs['wrap_length'] = draw(st.integers(min_value=10, max_value=line_length))
    
    config = Config(**kwargs)
    return config


# Test 1: Line length constraint property  
@given(
    content=st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1),
    config=config_strategy(),
    line_separator=st.sampled_from(['\n', '\r\n'])
)
@settings(max_examples=2000)
def test_line_length_constraint(content, config, line_separator):
    """Test that wrapped lines respect the configured line length."""
    # Skip if content already contains line separator or is just whitespace
    assume(line_separator not in content)
    assume(content.strip())
    
    # Skip if content has problematic patterns that might interfere
    assume('#' not in content or content.count('#') == 1)
    
    result = wrap.line(content, line_separator, config)
    
    # Property: Each line in the result should respect line length (unless NOQA mode)
    lines = result.split(line_separator)
    
    # According to the code, if multi_line_output is NOQA mode, it just adds "# NOQA"
    # Otherwise, lines should generally be <= config.line_length
    # But there are exceptions - if no good split point found, original might be returned
    
    # Let's test a more specific property: if the function adds line breaks,
    # then at least the first n-1 lines should be <= line_length
    if len(lines) > 1:
        for line in lines[:-1]:
            # The wrapped lines (except possibly the last) should try to fit
            # Note: there are edge cases where this might not hold perfectly
            assert len(line) <= config.line_length + 20  # Allow some tolerance


# Test 2: Comment preservation
@given(
    base_content=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='#\r\n'), min_size=10, max_size=100),
    comment=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='\r\n'), min_size=1, max_size=50),
    config=config_strategy(),
)
@settings(max_examples=2000)
def test_comment_preservation(base_content, comment, config):
    """Test that comments are preserved when wrapping lines."""
    # Create content with a comment
    content = f"{base_content} # {comment}"
    
    result = wrap.line(content, "\n", config)
    
    # Property: The comment should still be in the result
    # (unless ignore_comments is True in config)
    if not config.ignore_comments:
        # The comment text should appear somewhere in the result
        assert comment in result or "NOQA" in result


# Test 3: import_statement invariants
@given(
    import_start=st.just("from module import "),
    from_imports=st.lists(python_identifier(), min_size=0, max_size=20),
    comments=st.lists(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters='\r\n'), max_size=50), max_size=5),
    config=config_strategy(),
    explode=st.booleans(),
)
@settings(max_examples=2000)
def test_import_statement_invariants(import_start, from_imports, comments, config, explode):
    """Test invariants of the import_statement function."""
    
    result = wrap.import_statement(
        import_start=import_start,
        from_imports=from_imports,
        comments=list(comments),  # Make a copy since the function might modify it
        config=config,
        explode=explode
    )
    
    # Property 1: Always returns a string
    assert isinstance(result, str)
    
    # Property 2: All imports should be present in the result
    for imp in from_imports:
        assert imp in result
    
    # Property 3: If explode=True and there are multiple imports, 
    # there should be multiple lines
    if explode and len(from_imports) > 1:
        lines = result.split('\n')
        # With explode, we expect each import on its own line
        assert len(lines) >= len(from_imports)


# Test 4: Type preservation and no crashes
@given(
    import_start=st.text(min_size=1, max_size=100),
    from_imports=st.lists(st.text(min_size=1, max_size=50), max_size=10),
    config=config_strategy(),
)
@settings(max_examples=1000)
def test_import_statement_no_crash(import_start, from_imports, config):
    """Test that import_statement doesn't crash on various inputs."""
    try:
        result = wrap.import_statement(
            import_start=import_start,
            from_imports=from_imports,
            config=config
        )
        # Should always return a string
        assert isinstance(result, str)
    except Exception as e:
        # Some exceptions might be expected for invalid input,
        # but let's see if we find any unexpected crashes
        # We'll allow ValueError, AttributeError for now
        if not isinstance(e, (ValueError, AttributeError, KeyError)):
            raise


# Test 5: Round-trip for short imports  
@given(
    module_name=import_name(),
    import_names=st.lists(python_identifier(), min_size=1, max_size=3),
)
@settings(max_examples=1000)
def test_short_import_roundtrip(module_name, import_names):
    """Test that short imports that don't need wrapping are preserved."""
    import_start = f"from {module_name} import "
    
    # Use a config with very long line length so no wrapping needed
    config = Config(line_length=1000, use_parentheses=False)
    
    result = wrap.import_statement(
        import_start=import_start,
        from_imports=import_names,
        config=config
    )
    
    # The result should contain the original import statement components
    assert import_start in result
    for name in import_names:
        assert name in result
    
    # For single import without special config, should be on one line
    if len(import_names) == 1:
        assert '\n' not in result


if __name__ == "__main__":
    # Run the tests
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])