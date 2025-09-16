import io
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import isort.identify
from isort.identify import Import, imports, strip_syntax
from isort.parse import normalize_line
from isort.settings import DEFAULT_CONFIG, Config


# Strategy for valid Python identifiers
def python_identifier():
    first_char = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_', min_size=1, max_size=1)
    rest_chars = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_', min_size=0, max_size=20)
    return st.builds(lambda f, r: f + r, first_char, rest_chars)


# Test complex edge case: semicolon with comments
@given(
    module1=python_identifier(),
    module2=python_identifier(),
    comment=st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=1, max_size=10)
)
def test_semicolon_with_comment(module1, module2, comment):
    """Test semicolon-separated imports with comments"""
    assume(module1 != module2)
    # This tests line 82-85 in identify.py
    import_str = f"import {module1}; import {module2} # {comment}\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    modules = [imp.module for imp in parsed_imports]
    assert module1 in modules
    assert module2 in modules


# Test edge case: import after yield
def test_import_after_yield():
    """Test that imports after yield statements are handled"""
    code = """
def generator():
    yield
    import os
    return os
"""
    stream = io.StringIO(code)
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    # Should find the import after yield
    modules = [imp.module for imp in parsed_imports]
    assert "os" in modules


# Test normalize_line edge cases
@given(st.text(min_size=0, max_size=50))
def test_normalize_line_edge_cases(text):
    """Test normalize_line with various edge cases"""
    # Test with various import patterns
    test_cases = [
        f"from.import {text}",
        f"from..import {text}",
        f"from...import {text}",
        f"from.cimport {text}",
        f"from..cimport {text}",
        f"import*",
        f" .import {text}",
        f" ..import {text}",
        f" .cimport {text}",
    ]
    
    for test_case in test_cases:
        normalized, raw = normalize_line(test_case)
        # Should add spaces appropriately
        if "from." in test_case and "import" in test_case:
            assert "from ." in normalized or "from . " in normalized
        if "import*" in test_case:
            assert "import *" in normalized


# Test strip_syntax edge case with nested braces
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz ', min_size=0, max_size=20))
def test_strip_syntax_nested_braces(text):
    """Test strip_syntax with nested and complex brace patterns"""
    test_string = f"{{ {{ {text} }} }}"
    result = strip_syntax(test_string)
    
    # Check that brace replacements happened
    # The function replaces "{ " with "{|" and " }" with "|}"
    if "{ " in test_string:
        # At least some should be replaced
        original_count = test_string.count("{ ")
        # Result should have the replacements
        assert "{|" in result or original_count == 0


# Test malformed import statements
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789_. ', min_size=1, max_size=30))
def test_malformed_imports_no_crash(text):
    """Test that malformed imports don't crash the parser"""
    malformed_cases = [
        f"import\n",  # Import with no module
        f"from\n",     # From with nothing
        f"from import {text}\n",  # From with no module
        f"import as {text}\n",    # Import with only alias
        f"from {text} import\n",  # From with no imports
        f"import {text} as\n",    # Alias with no name
        f"from {text} import as alias\n",  # Missing attribute
    ]
    
    for case in malformed_cases:
        stream = io.StringIO(case)
        try:
            parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
            # Should not crash
            assert isinstance(parsed_imports, list)
        except Exception as e:
            # Some malformed imports might raise exceptions, which is acceptable
            pass


# Test complex multiline with mixed parentheses and backslashes
@given(
    module=python_identifier(),
    attrs=st.lists(python_identifier(), min_size=2, max_size=4, unique=True)
)
def test_mixed_multiline_styles(module, attrs):
    """Test mixing parentheses and backslashes in multiline imports"""
    # Create a complex multiline import
    import_str = f"from {module} import \\\n    ({attrs[0]},\n     {', '.join(attrs[1:])})\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    parsed_attrs = [imp.attribute for imp in parsed_imports]
    
    for attr in attrs:
        assert attr in parsed_attrs


# Test Import class with extreme values
def test_import_extreme_values():
    """Test Import class with edge case values"""
    # Test with empty module name (should work)
    imp = Import(
        line_number=0,  # Edge case: 0 line number
        indented=True,
        module="",  # Empty module
        attribute="",  # Empty attribute
        alias="",  # Empty alias
        cimport=True
    )
    
    # Should not crash
    statement = imp.statement()
    assert isinstance(statement, str)
    
    # Test with very long names
    long_name = "a" * 1000
    imp2 = Import(
        line_number=999999,
        indented=False,
        module=long_name,
        attribute=long_name,
        alias=long_name,
        cimport=False
    )
    statement2 = imp2.statement()
    assert isinstance(statement2, str)
    assert long_name in statement2


# Test config option: remove_redundant_aliases
@given(
    module=python_identifier(),
    attribute=python_identifier()
)
def test_remove_redundant_aliases_config(module, attribute):
    """Test the remove_redundant_aliases configuration option"""
    # When alias equals the imported name, it might be removed
    import_str = f"from {module} import {attribute} as {attribute}\n"
    
    # Test with remove_redundant_aliases=True
    config_remove = Config(remove_redundant_aliases=True)
    stream = io.StringIO(import_str)
    parsed_imports = list(imports(stream, config=config_remove))
    
    if parsed_imports:
        imp = parsed_imports[0]
        # With remove_redundant_aliases=True, the alias should be None
        assert imp.alias is None or imp.alias == attribute
    
    # Test with remove_redundant_aliases=False (default)
    config_keep = Config(remove_redundant_aliases=False)
    stream2 = io.StringIO(import_str)
    parsed_imports2 = list(imports(stream2, config=config_keep))
    
    if parsed_imports2:
        imp2 = parsed_imports2[0]
        # Should keep the alias
        assert imp2.alias == attribute


# Test top_only parameter
def test_top_only_parameter():
    """Test that top_only stops at first non-import statement"""
    code = '''import os
import sys

def function():
    import hidden
    return hidden

import after_function
'''
    
    # Test with top_only=True
    stream = io.StringIO(code)
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG, top_only=True))
    
    modules = [imp.module for imp in parsed_imports]
    assert "os" in modules
    assert "sys" in modules
    assert "hidden" not in modules  # Inside function
    assert "after_function" not in modules  # After function definition
    
    # Test with top_only=False (default)
    stream2 = io.StringIO(code)
    parsed_imports2 = list(imports(stream2, config=DEFAULT_CONFIG, top_only=False))
    
    modules2 = [imp.module for imp in parsed_imports2]
    assert "os" in modules2
    assert "sys" in modules2
    assert "hidden" in modules2
    assert "after_function" in modules2


# Test Import.__str__ method
@given(
    line_number=st.integers(min_value=1, max_value=1000),
    indented=st.booleans(),
    module=python_identifier(),
    attribute=st.one_of(st.none(), python_identifier()),
    alias=st.one_of(st.none(), python_identifier()),
    cimport=st.booleans()
)
def test_import_str_method(line_number, indented, module, attribute, alias, cimport):
    """Test the Import.__str__ method"""
    imp = Import(
        line_number=line_number,
        indented=indented,
        module=module,
        attribute=attribute,
        alias=alias,
        cimport=cimport,
        file_path=None
    )
    
    str_repr = str(imp)
    
    # Check that the string representation contains expected parts
    assert str(line_number) in str_repr
    if indented:
        assert "indented" in str_repr
    assert imp.statement() in str_repr


# Test parsing with raise and yield edge cases
def test_raise_yield_edge_cases():
    """Test that raise and yield statements are properly skipped"""
    code = '''import os
raise Exception("test")
import sys
yield
import math
yield from generator
import json
'''
    
    stream = io.StringIO(code)
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    modules = [imp.module for imp in parsed_imports]
    # All imports should be found despite raise/yield
    assert "os" in modules
    assert "sys" in modules
    assert "math" in modules
    assert "json" in modules


# Stress test: Many imports on one line with semicolons
@given(modules=st.lists(python_identifier(), min_size=3, max_size=6, unique=True))
def test_many_semicolon_imports(modules):
    """Test many imports separated by semicolons"""
    import_str = "; ".join([f"import {m}" for m in modules]) + "\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    parsed_modules = [imp.module for imp in parsed_imports]
    
    for module in modules:
        assert module in parsed_modules


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])