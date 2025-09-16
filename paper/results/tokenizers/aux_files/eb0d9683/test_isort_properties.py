#!/usr/bin/env python3
"""Property-based tests for isort using Hypothesis."""

import ast
import re
from hypothesis import given, strategies as st, assume, settings
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')
import isort


def extract_imports(code):
    """Extract all import statements from Python code."""
    imports = set()
    lines = code.split('\n')
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            # Normalize whitespace for comparison
            normalized = re.sub(r'\s+', ' ', stripped)
            imports.add(normalized)
    return imports


def is_valid_python(code):
    """Check if code is valid Python syntax."""
    try:
        compile(code, '<string>', 'exec')
        return True
    except SyntaxError:
        return False


# Strategy for generating Python import statements
def import_name():
    """Generate valid Python module/attribute names."""
    return st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz_',
        min_size=1,
        max_size=10
    ).filter(lambda x: x[0] != '_' and not x.isdigit())


def module_path():
    """Generate module paths like 'os.path' or 'django.conf'."""
    return st.lists(
        import_name(),
        min_size=1,
        max_size=3
    ).map(lambda parts: '.'.join(parts))


def import_statement():
    """Generate import statements."""
    return st.one_of(
        # Simple imports: import os
        st.builds(
            lambda mod: f"import {mod}",
            module_path()
        ),
        # From imports: from os import path
        st.builds(
            lambda mod, attr: f"from {mod} import {attr}",
            module_path(),
            import_name()
        ),
        # From imports with alias: from os import path as p
        st.builds(
            lambda mod, attr, alias: f"from {mod} import {attr} as {alias}",
            module_path(),
            import_name(),
            import_name()
        ),
        # Multiple imports: from os import path, environ
        st.builds(
            lambda mod, attrs: f"from {mod} import {', '.join(attrs)}",
            module_path(),
            st.lists(import_name(), min_size=1, max_size=3, unique=True)
        )
    )


def python_code_with_imports():
    """Generate Python code with import statements."""
    return st.builds(
        lambda imports, code: '\n'.join(imports) + '\n\n' + code if imports else code,
        st.lists(import_statement(), min_size=0, max_size=5, unique=True),
        st.just("# Some code\nprint('hello')")
    )


# Test 1: Idempotence - sorting twice should give the same result
@given(python_code_with_imports())
@settings(max_examples=100)
def test_idempotence(code):
    """Test that sorting is idempotent: sort(sort(x)) == sort(x)"""
    try:
        sorted_once = isort.code(code)
        sorted_twice = isort.code(sorted_once)
        assert sorted_once == sorted_twice, \
            f"Sorting is not idempotent.\nAfter 1st sort:\n{sorted_once}\nAfter 2nd sort:\n{sorted_twice}"
    except (isort.exceptions.FileSkipComment, isort.exceptions.FileSkipSetting):
        # Skip files that isort is configured to skip
        pass


# Test 2: Check-Sort Consistency
@given(python_code_with_imports())
@settings(max_examples=100)
def test_check_sort_consistency(code):
    """If check_code returns True, then sort_code should return the same code."""
    try:
        if isort.check_code(code):
            sorted_code = isort.code(code)
            assert code == sorted_code, \
                f"check_code returned True but sort_code changed the code.\nOriginal:\n{code}\nSorted:\n{sorted_code}"
    except (isort.exceptions.FileSkipComment, isort.exceptions.FileSkipSetting):
        pass


# Test 3: Import Preservation
@given(python_code_with_imports())
@settings(max_examples=100)
def test_import_preservation(code):
    """Sorting should preserve all imports (no imports lost or added)."""
    try:
        original_imports = extract_imports(code)
        sorted_code = isort.code(code)
        sorted_imports = extract_imports(sorted_code)
        
        # Check that no imports were lost
        lost_imports = original_imports - sorted_imports
        assert not lost_imports, \
            f"Lost imports during sorting: {lost_imports}\nOriginal:\n{code}\nSorted:\n{sorted_code}"
        
        # Check that no imports were added (except for config.add_imports)
        added_imports = sorted_imports - original_imports
        # Note: We allow added imports if they come from configuration
        # but for basic sorting, no new imports should appear
        if added_imports:
            # Check if these are from default configuration
            default_config = isort.Config()
            if not any(imp in str(default_config.add_imports) for imp in added_imports):
                assert False, f"Unexpected imports added: {added_imports}"
    except (isort.exceptions.FileSkipComment, isort.exceptions.FileSkipSetting):
        pass


# Test 4: No Syntax Errors
@given(python_code_with_imports())
@settings(max_examples=100)
def test_no_syntax_errors(code):
    """Sorting valid Python code should produce valid Python code."""
    # Only test with valid Python code
    assume(is_valid_python(code))
    
    try:
        sorted_code = isort.code(code)
        assert is_valid_python(sorted_code), \
            f"Sorted code has syntax errors.\nOriginal (valid):\n{code}\nSorted (invalid):\n{sorted_code}"
    except (isort.exceptions.FileSkipComment, isort.exceptions.FileSkipSetting):
        pass
    except isort.exceptions.ExistingSyntaxErrors:
        # This is expected if the input had syntax errors
        pass


# Test 5: Line ending preservation
@given(
    python_code_with_imports(),
    st.sampled_from(['\n', '\r\n', '\r'])
)
@settings(max_examples=50)
def test_line_ending_preservation(code, line_ending):
    """Test that isort preserves line endings."""
    code_with_ending = code.replace('\n', line_ending)
    try:
        config = isort.Config(line_ending=line_ending)
        sorted_code = isort.code(code_with_ending, config=config)
        
        # Check that the line ending is preserved
        if line_ending in sorted_code:
            # Good, line ending preserved
            pass
        elif '\n' in sorted_code and line_ending != '\n':
            # Line ending was not preserved
            assert False, f"Line ending {repr(line_ending)} not preserved in output"
    except (isort.exceptions.FileSkipComment, isort.exceptions.FileSkipSetting):
        pass


# Test 6: Multi-line import handling
def multiline_import():
    """Generate multi-line import statements."""
    return st.builds(
        lambda mod, attrs: f"from {mod} import (\n    " + ",\n    ".join(attrs) + "\n)",
        module_path(),
        st.lists(import_name(), min_size=2, max_size=5, unique=True)
    )


@given(multiline_import())
@settings(max_examples=50)
def test_multiline_import_handling(import_stmt):
    """Test that multi-line imports are handled correctly."""
    code = import_stmt + "\n\nprint('test')"
    try:
        sorted_code = isort.code(code)
        
        # Extract imports from both versions
        original_imports = extract_imports(code)
        sorted_imports = extract_imports(sorted_code)
        
        # The actual imports should be preserved (though formatting may change)
        assert len(original_imports) > 0, "No imports found in original"
        assert len(sorted_imports) > 0, "No imports found after sorting"
        
        # Basic validation
        assert is_valid_python(sorted_code), "Sorted multi-line import code is invalid"
    except (isort.exceptions.FileSkipComment, isort.exceptions.FileSkipSetting):
        pass


# Test 7: Check that isort handles edge cases
@given(st.text(min_size=0, max_size=100))
@settings(max_examples=50)
def test_arbitrary_text_handling(text):
    """Test that isort doesn't crash on arbitrary text input."""
    try:
        # isort should handle any text input gracefully
        result = isort.code(text)
        # If it returns a result, it should be a string
        assert isinstance(result, str)
    except (SyntaxError, isort.exceptions.ExistingSyntaxErrors):
        # These are acceptable - invalid Python code
        pass
    except (isort.exceptions.FileSkipComment, isort.exceptions.FileSkipSetting):
        # These are acceptable - file marked to skip
        pass


if __name__ == "__main__":
    print("Running property-based tests for isort...")
    
    # Run each test function
    test_functions = [
        test_idempotence,
        test_check_sort_consistency,
        test_import_preservation,
        test_no_syntax_errors,
        test_line_ending_preservation,
        test_multiline_import_handling,
        test_arbitrary_text_handling
    ]
    
    for test_func in test_functions:
        print(f"\nTesting: {test_func.__name__}")
        try:
            test_func()
            print(f"✓ {test_func.__name__} passed")
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
        except Exception as e:
            print(f"✗ {test_func.__name__} error: {e}")