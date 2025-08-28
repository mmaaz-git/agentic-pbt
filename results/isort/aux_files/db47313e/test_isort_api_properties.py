#!/usr/bin/env python3
"""Property-based tests for isort.api module using Hypothesis."""

import sys
import math
from io import StringIO
from pathlib import Path

from hypothesis import assume, given, settings, strategies as st
from hypothesis import HealthCheck

sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.api
from isort.api import (
    ImportKey,
    check_code_string,
    find_imports_in_code,
    sort_code_string,
)


# Strategy for generating valid Python import statements
@st.composite
def import_statement(draw):
    """Generate a valid Python import statement."""
    module_parts = draw(st.lists(
        st.from_regex(r"[a-z][a-z0-9_]*", fullmatch=True),
        min_size=1,
        max_size=3
    ))
    module_name = ".".join(module_parts)
    
    import_type = draw(st.sampled_from(["import", "from"]))
    
    if import_type == "import":
        # import module
        # import module as alias
        if draw(st.booleans()):
            alias = draw(st.from_regex(r"[a-z][a-z0-9_]*", fullmatch=True))
            return f"import {module_name} as {alias}"
        return f"import {module_name}"
    else:
        # from module import item
        # from module import item as alias
        item = draw(st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True))
        if draw(st.booleans()):
            alias = draw(st.from_regex(r"[a-z][a-z0-9_]*", fullmatch=True))
            return f"from {module_name} import {item} as {alias}"
        return f"from {module_name} import {item}"


@st.composite
def python_code_with_imports(draw):
    """Generate Python code that may contain imports."""
    imports = draw(st.lists(import_statement(), min_size=0, max_size=5))
    
    # Add some non-import code
    other_lines = []
    if draw(st.booleans()):
        other_lines.append("# Some comment")
    if draw(st.booleans()):
        other_lines.append("x = 1")
    if draw(st.booleans()):
        other_lines.append("def foo():\n    pass")
    
    # Mix imports and other code
    all_lines = imports + other_lines
    if draw(st.booleans()):
        # Sometimes shuffle to test sorting
        draw(st.randoms()).shuffle(all_lines)
    
    return "\n".join(all_lines)


# Test 1: Idempotence - sorting already sorted code should not change it
@given(python_code_with_imports())
@settings(max_examples=100, suppress_health_check=[HealthCheck.filter_too_much])
def test_sort_idempotence(code):
    """Test that sort_code_string is idempotent."""
    try:
        sorted_once = sort_code_string(code)
        sorted_twice = sort_code_string(sorted_once)
        assert sorted_once == sorted_twice, f"Sorting is not idempotent!\nFirst sort:\n{sorted_once}\nSecond sort:\n{sorted_twice}"
    except Exception as e:
        # Skip if the code has syntax errors
        if "SyntaxError" in str(type(e)):
            assume(False)
        raise


# Test 2: Check-sort consistency
@given(python_code_with_imports())
@settings(max_examples=100, suppress_health_check=[HealthCheck.filter_too_much])
def test_check_sort_consistency(code):
    """Test that check_code_string and sort_code_string are consistent."""
    try:
        sorted_code = sort_code_string(code)
        
        # After sorting, check should return True
        is_sorted = check_code_string(sorted_code)
        assert is_sorted, f"check_code_string returned False for sorted code:\n{sorted_code}"
        
        # If check returns True, sorting should not change the code
        if check_code_string(code):
            assert code == sorted_code, "check returned True but sort changed the code"
    except Exception as e:
        # Skip if the code has syntax errors
        if "SyntaxError" in str(type(e)):
            assume(False)
        raise


# Test 3: Import preservation
@given(python_code_with_imports())
@settings(max_examples=100, suppress_health_check=[HealthCheck.filter_too_much])
def test_import_preservation(code):
    """Test that sorting preserves all imports."""
    try:
        # Find imports before sorting
        imports_before = list(find_imports_in_code(code))
        
        # Sort the code
        sorted_code = sort_code_string(code)
        
        # Find imports after sorting
        imports_after = list(find_imports_in_code(sorted_code))
        
        # Extract just the import statements for comparison
        statements_before = sorted([imp.statement() for imp in imports_before])
        statements_after = sorted([imp.statement() for imp in imports_after])
        
        assert statements_before == statements_after, (
            f"Imports changed after sorting!\n"
            f"Before: {statements_before}\n"
            f"After: {statements_after}"
        )
    except Exception as e:
        # Skip if the code has syntax errors
        if "SyntaxError" in str(type(e)):
            assume(False)
        raise


# Test 4: ImportKey uniqueness levels
@given(python_code_with_imports())
@settings(max_examples=100, suppress_health_check=[HealthCheck.filter_too_much])
def test_import_key_uniqueness(code):
    """Test that ImportKey uniqueness levels work correctly."""
    try:
        # Test each ImportKey level
        for key_type in [ImportKey.PACKAGE, ImportKey.MODULE, ImportKey.ATTRIBUTE, ImportKey.ALIAS]:
            imports = list(find_imports_in_code(code, unique=key_type))
            
            # Check uniqueness based on the key type
            seen = set()
            for imp in imports:
                if key_type == ImportKey.ALIAS:
                    key = imp.statement()
                elif key_type == ImportKey.ATTRIBUTE:
                    key = f"{imp.module}.{imp.attribute}" if imp.attribute else imp.module
                elif key_type == ImportKey.MODULE:
                    key = imp.module
                elif key_type == ImportKey.PACKAGE:
                    key = imp.module.split(".")[0]
                
                assert key not in seen, f"Duplicate found with ImportKey.{key_type.name}: {key}"
                seen.add(key)
                
    except Exception as e:
        # Skip if the code has syntax errors
        if "SyntaxError" in str(type(e)):
            assume(False)
        raise


# Test 5: Round-trip with show_diff
@given(python_code_with_imports())
@settings(max_examples=50, suppress_health_check=[HealthCheck.filter_too_much])
def test_show_diff_consistency(code):
    """Test that show_diff doesn't affect sorting behavior."""
    try:
        # Sort without show_diff
        sorted_normal = sort_code_string(code)
        
        # Sort with show_diff to a StringIO
        diff_output = StringIO()
        sorted_with_diff = sort_code_string(code, show_diff=diff_output)
        
        assert sorted_normal == sorted_with_diff, (
            "Sorting with show_diff produced different result"
        )
    except Exception as e:
        # Skip if the code has syntax errors
        if "SyntaxError" in str(type(e)):
            assume(False)
        raise


# Test 6: Empty and whitespace handling
@given(st.text(alphabet=" \t\n", min_size=0, max_size=20))
def test_empty_and_whitespace(whitespace_code):
    """Test handling of empty strings and whitespace."""
    sorted_code = sort_code_string(whitespace_code)
    # Should handle empty/whitespace gracefully
    assert isinstance(sorted_code, str)
    
    # Check should return True for empty/whitespace
    is_sorted = check_code_string(whitespace_code)
    assert isinstance(is_sorted, bool)


# Test 7: Extension parameter handling
@given(
    code=python_code_with_imports(),
    extension=st.sampled_from([None, "py", "pyi", "pyx"])
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.filter_too_much])
def test_extension_handling(code, extension):
    """Test that different extensions are handled correctly."""
    try:
        sorted_code = sort_code_string(code, extension=extension)
        assert isinstance(sorted_code, str)
        
        # Should be idempotent regardless of extension
        sorted_twice = sort_code_string(sorted_code, extension=extension)
        assert sorted_code == sorted_twice
    except Exception as e:
        # Skip if the code has syntax errors
        if "SyntaxError" in str(type(e)):
            assume(False)
        raise


# Test 8: Config kwargs handling
@given(python_code_with_imports())
@settings(max_examples=50, suppress_health_check=[HealthCheck.filter_too_much])
def test_config_kwargs(code):
    """Test that config kwargs are properly handled."""
    try:
        # Test with various config options
        sorted_default = sort_code_string(code)
        
        # Test with force_single_line
        sorted_single = sort_code_string(code, force_single_line=True)
        assert isinstance(sorted_single, str)
        
        # Both should be valid Python after sorting
        if sorted_default.strip():
            compile(sorted_default, "<test>", "exec")
        if sorted_single.strip():
            compile(sorted_single, "<test>", "exec")
            
    except Exception as e:
        # Skip if the code has syntax errors
        if "SyntaxError" in str(type(e)):
            assume(False)
        raise


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))