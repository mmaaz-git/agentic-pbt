#!/usr/bin/env python3
"""
Property-based tests for fixit.format module.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from pathlib import Path
from hypothesis import given, strategies as st, assume
import pytest
from libcst import parse_module, Module

from fixit.format import Formatter, FORMAT_STYLES, format_module
from fixit.ftypes import Config


# Test basic Formatter properties
@given(
    code=st.text(
        alphabet=st.characters(min_codepoint=32, max_codepoint=126),
        min_size=0,
        max_size=100
    )
)
def test_base_formatter_identity(code):
    """Test that base Formatter returns module bytes unchanged."""
    try:
        # Try to parse as valid Python code
        module = parse_module(code.encode('utf-8'))
    except:
        # Skip invalid Python code
        assume(False)
    
    formatter = Formatter()
    path = Path("test.py")
    
    result = formatter.format(module, path)
    
    # Base formatter should return module bytes unchanged
    assert result == module.bytes


def test_format_styles_registry():
    """Test that FORMAT_STYLES registry contains expected entries."""
    # None should map to base Formatter
    assert FORMAT_STYLES[None] == Formatter
    
    # Should have registered formatters
    assert "black" in FORMAT_STYLES or "ufmt" in FORMAT_STYLES or None in FORMAT_STYLES


@given(
    formatter_name=st.sampled_from([None, "nonexistent"])
)
def test_format_module_with_formatter(formatter_name):
    """Test format_module with different formatter configurations."""
    code = b"x = 1\n"
    module = parse_module(code)
    path = Path("test.py")
    
    # Create config with specified formatter
    config = Config(path=path, formatter=formatter_name)
    
    if formatter_name in FORMAT_STYLES:
        # Should work for valid formatters
        result = format_module(module, path, config)
        assert isinstance(result, bytes)
    else:
        # Should raise for invalid formatters
        with pytest.raises(KeyError):
            format_module(module, path, config)


# Test properties of module parsing and formatting
@given(
    code=st.one_of(
        st.just(b""),  # empty
        st.just(b"pass"),  # minimal valid
        st.just(b"x = 1"),  # simple assignment
        st.just(b"def f(): pass"),  # function def
        st.just(b"class C: pass"),  # class def
        st.just(b"# comment\nx = 1"),  # with comment
        st.just(b"x = 1\ny = 2\nz = x + y"),  # multiple statements
    )
)
def test_parse_format_roundtrip(code):
    """Test that parsing and formatting maintains code structure."""
    module1 = parse_module(code)
    
    # Format with base formatter
    formatter = Formatter()
    path = Path("test.py")
    formatted = formatter.format(module1, path)
    
    # Parse the formatted code
    module2 = parse_module(formatted)
    
    # The parsed modules should be equivalent
    # (We can't use direct equality as CST nodes include metadata)
    assert module1.code == module2.code


# Test that Formatter subclasses are properly registered
def test_formatter_subclass_registration():
    """Test that creating a Formatter subclass registers it in FORMAT_STYLES."""
    
    # Create a custom formatter
    class TestFormatter(Formatter):
        STYLE = "test_formatter_unique_name_12345"
        
        def format(self, module: Module, path: Path) -> bytes:
            return b"# formatted\n" + module.bytes
    
    # Should be registered
    assert FORMAT_STYLES["test_formatter_unique_name_12345"] == TestFormatter
    
    # Clean up
    del FORMAT_STYLES["test_formatter_unique_name_12345"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])