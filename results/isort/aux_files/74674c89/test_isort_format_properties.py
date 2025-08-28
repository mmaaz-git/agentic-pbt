"""Property-based tests for isort.format module"""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import isort.format as fmt


# Strategies for generating valid Python identifiers
python_identifier = st.from_regex(r'[a-zA-Z_][a-zA-Z0-9_]*', fullmatch=True)

# Strategy for module names (dot-separated identifiers)
module_name = st.lists(python_identifier, min_size=1, max_size=5).map(lambda x: '.'.join(x))

# Strategy for import statements
from_import_stmt = st.builds(
    lambda mod, names: f"from {mod} import {', '.join(names)}",
    module_name,
    st.lists(python_identifier, min_size=1, max_size=3)
)

simple_import_stmt = st.builds(
    lambda mod: f"import {mod}",
    module_name
)

import_statement = st.one_of(from_import_stmt, simple_import_stmt)

# Strategy for simplified format (what format_simplified produces)
simplified_format = st.one_of(
    module_name,
    st.builds(
        lambda mod, name: f"{mod}.{name}",
        module_name,
        python_identifier
    )
)


@given(import_statement)
def test_format_simplified_idempotent(import_line):
    """format_simplified should be idempotent"""
    once = fmt.format_simplified(import_line)
    twice = fmt.format_simplified(once)
    assert once == twice


@given(simplified_format)
def test_format_natural_idempotent(simplified):
    """format_natural should be idempotent"""
    once = fmt.format_natural(simplified)
    twice = fmt.format_natural(once)
    assert once == twice


@given(simple_import_stmt)
def test_round_trip_simple_import(import_line):
    """Round trip for simple import statements"""
    simplified = fmt.format_simplified(import_line)
    restored = fmt.format_natural(simplified)
    assert restored.strip() == import_line.strip()


@given(module_name, st.lists(python_identifier, min_size=1, max_size=1))
def test_round_trip_from_import_single(module, names):
    """Round trip for from...import with single name"""
    import_line = f"from {module} import {names[0]}"
    simplified = fmt.format_simplified(import_line)
    restored = fmt.format_natural(simplified)
    assert restored.strip() == import_line.strip()


@given(st.text())
def test_remove_whitespace_idempotent(content):
    """remove_whitespace should be idempotent"""
    once = fmt.remove_whitespace(content)
    twice = fmt.remove_whitespace(once)
    assert once == twice


@given(st.text())
def test_remove_whitespace_no_spaces(content):
    """remove_whitespace should remove all spaces"""
    result = fmt.remove_whitespace(content)
    assert ' ' not in result


@given(st.text(), st.text(min_size=1, max_size=5))
def test_remove_whitespace_custom_separator(content, separator):
    """remove_whitespace should remove custom line separators"""
    result = fmt.remove_whitespace(content, line_separator=separator)
    assert separator not in result


@given(st.text())
def test_remove_whitespace_removes_formfeed(content):
    """remove_whitespace should remove form feed characters"""
    result = fmt.remove_whitespace(content)
    assert '\x0c' not in result


@given(module_name)
def test_format_operations_preserve_module_structure(module):
    """Converting a module name through format_natural should preserve structure"""
    # A bare module name should become an import statement
    natural = fmt.format_natural(module)
    
    # The result should be a valid import statement
    if '.' in module:
        # For dotted names, format_natural doesn't change them unless they're being imported
        # But if we have module.submodule, it should stay as is or become from module import submodule
        pass
    else:
        assert natural == f"import {module}"


@given(st.text())
def test_format_natural_preserves_existing_imports(text):
    """format_natural should preserve already-formatted import statements"""
    if text.strip().startswith("from ") or text.strip().startswith("import "):
        result = fmt.format_natural(text)
        assert result == text


@given(st.lists(st.sampled_from([' ', '\n', '\t', '\r', '\x0c']), min_size=0, max_size=20))
def test_remove_whitespace_handles_all_whitespace_types(whitespace_list):
    """remove_whitespace should handle various whitespace characters"""
    content = ''.join(whitespace_list) + 'test' + ''.join(whitespace_list)
    result = fmt.remove_whitespace(content)
    assert result == 'test'


@given(python_identifier, python_identifier)
def test_format_simplified_from_import_consistency(module, name):
    """format_simplified should consistently handle from...import statements"""
    import_line = f"from {module} import {name}"
    result = fmt.format_simplified(import_line)
    assert result == f"{module}.{name}"


@given(module_name)
def test_format_simplified_import_consistency(module):
    """format_simplified should consistently handle import statements"""
    import_line = f"import {module}"
    result = fmt.format_simplified(import_line)
    assert result == module


# Edge case tests
def test_format_natural_empty_string():
    """format_natural should handle empty strings"""
    result = fmt.format_natural("")
    assert result == "import "


def test_format_simplified_empty_string():
    """format_simplified should handle empty strings"""
    result = fmt.format_simplified("")
    assert result == ""


def test_format_natural_single_identifier():
    """format_natural should convert single identifier to import"""
    result = fmt.format_natural("os")
    assert result == "import os"


def test_format_natural_dotted_identifier():
    """format_natural should convert dotted identifier to from...import"""
    result = fmt.format_natural("os.path")
    assert result == "from os import path"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])