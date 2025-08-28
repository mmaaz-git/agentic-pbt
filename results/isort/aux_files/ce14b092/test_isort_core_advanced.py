"""Advanced property-based tests for isort.core module to find edge cases."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from io import StringIO
from hypothesis import given, strategies as st, assume, settings, example
import isort.core
from isort.format import format_natural, format_simplified
from isort.settings import Config


# Test with wildcard imports
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20))
def test_format_simplified_wildcard_import(module):
    """Test format_simplified with wildcard imports."""
    import_line = f"from {module} import *"
    result = format_simplified(import_line)
    
    # Wildcard should be preserved in simplified format
    assert result == f"{module}.*"


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20))
def test_format_natural_wildcard_round_trip(module):
    """Test round-trip for wildcard imports."""
    simplified = f"{module}.*"
    natural = format_natural(simplified)
    
    # Should create a valid wildcard import
    assert natural == f"from {module} import *"
    
    # Round trip should work
    assert format_simplified(natural) == simplified


# Test with aliased imports
@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20)
)
def test_format_simplified_with_alias(module, item, alias):
    """Test format_simplified with aliased imports."""
    import_line = f"from {module} import {item} as {alias}"
    result = format_simplified(import_line)
    
    # The alias part should be preserved somehow
    # Based on the code, it looks like it just replaces 'from' and 'import'
    expected = f"{module}.{item} as {alias}"
    assert result == expected


# Test empty and whitespace edge cases
@given(st.text(alphabet=" \t\n", min_size=0, max_size=10))
def test_format_simplified_whitespace_only(whitespace):
    """Test format_simplified with whitespace-only input."""
    result = format_simplified(whitespace)
    assert result == ""


@given(st.text(alphabet=" \t\n", min_size=0, max_size=10))
def test_format_natural_whitespace_only(whitespace):
    """Test format_natural with whitespace-only input."""
    result = format_natural(whitespace)
    assert result == ""


# Test with parenthesized imports
@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20),
    st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=10),
        min_size=2,
        max_size=5
    )
)
def test_format_simplified_parenthesized(module, items):
    """Test format_simplified with parenthesized multi-line imports."""
    items_str = ", ".join(items)
    import_line = f"from {module} import ({items_str})"
    result = format_simplified(import_line)
    
    # Should handle parentheses
    expected = f"{module}.({items_str})"
    assert result == expected


# Test process with imports that have comments
@given(
    st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20),
        min_size=2,
        max_size=5
    )
)
@settings(max_examples=500, deadline=5000)
def test_process_preserves_all_imports(modules):
    """Test that process preserves all imports (no imports are lost)."""
    # Create code with multiple imports
    imports = [f"import {module}" for module in modules]
    code = "\n".join(imports) + "\n"
    
    input_stream = StringIO(code)
    output_stream = StringIO()
    config = Config()
    
    try:
        isort.core.process(
            input_stream, output_stream,
            extension="py",
            raise_on_skip=False,
            config=config
        )
    except Exception:
        assume(False)
    
    result = output_stream.getvalue()
    
    # All original modules should still be imported
    for module in modules:
        assert module in result
        # Either as "import module" or in some other valid form
        assert (f"import {module}" in result) or (f" {module}" in result)


# Test special characters that might break parsing
@example("")  # Empty string
@example("import")  # Just the keyword
@example("from")  # Just the from keyword
@example("from import")  # Invalid syntax
@example("import .")  # Invalid module name
@example("from . import")  # Relative import edge case
@given(st.text(max_size=50))
def test_format_simplified_robustness(text):
    """Test that format_simplified doesn't crash on arbitrary input."""
    try:
        result = format_simplified(text)
        # Should always return a string
        assert isinstance(result, str)
    except Exception as e:
        # Should not raise exceptions for any input
        assert False, f"format_simplified raised exception: {e}"


@example("")  # Empty string
@example(".")  # Just a dot
@example("..")  # Two dots
@example("...")  # Three dots
@given(st.text(max_size=50))
def test_format_natural_robustness(text):
    """Test that format_natural doesn't crash on arbitrary input."""
    try:
        result = format_natural(text)
        # Should always return a string
        assert isinstance(result, str)
    except Exception as e:
        # Should not raise exceptions for any input
        assert False, f"format_natural raised exception: {e}"


# Test for actual semantic preservation in round-trip
@given(
    st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=10),
        min_size=1,
        max_size=4
    ).filter(lambda parts: all(p and not p.startswith('_') for p in parts))
)
def test_dotted_import_round_trip(parts):
    """Test round-trip for dotted imports like 'import a.b.c'."""
    dotted = ".".join(parts)
    import_line = f"import {dotted}"
    
    simplified = format_simplified(import_line)
    restored = format_natural(simplified)
    
    # The semantic should be preserved even if format changes
    # Both should refer to the same module
    assert dotted in restored or simplified in restored


# Test indented config modification
@given(
    st.text(alphabet=" \t", min_size=0, max_size=10),
    st.integers(min_value=0, max_value=120)
)
def test_indented_config_line_length(indent, line_length):
    """Test that _indented_config correctly adjusts line length."""
    config = Config(line_length=line_length)
    indented = isort.core._indented_config(config, indent)
    
    # Line length should be reduced by indent length
    expected = max(line_length - len(indent), 0)
    assert indented.line_length == expected
    
    # Other configs should be preserved or set correctly
    assert indented.lines_after_imports == 1