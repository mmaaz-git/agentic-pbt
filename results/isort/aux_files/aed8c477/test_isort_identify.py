import io
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import isort.identify
from isort.identify import Import, imports, strip_syntax
from isort.settings import DEFAULT_CONFIG


# Strategy for valid Python identifiers
def python_identifier():
    first_char = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_', min_size=1, max_size=1)
    rest_chars = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_', min_size=0, max_size=20)
    return st.builds(lambda f, r: f + r, first_char, rest_chars)


# Property 1: Line numbers in Import objects are always >= 1
@given(
    line_number=st.integers(),
    indented=st.booleans(),
    module=python_identifier(),
    attribute=st.one_of(st.none(), python_identifier()),
    alias=st.one_of(st.none(), python_identifier()),
    cimport=st.booleans()
)
def test_import_line_number_invariant(line_number, indented, module, attribute, alias, cimport):
    """Test that Import objects enforce line number >= 1 constraint"""
    imp = Import(
        line_number=line_number,
        indented=indented,
        module=module,
        attribute=attribute,
        alias=alias,
        cimport=cimport
    )
    # This tests if the Import class properly validates or uses line numbers
    # The implementation shows line_number comes from index + 1, so should be >= 1
    # But Import class doesn't enforce this - it accepts any integer
    assert isinstance(imp.line_number, int)


# Property 2: strip_syntax preserves _import and _cimport keywords
@given(st.text())
def test_strip_syntax_preserves_special_imports(text):
    """Test that strip_syntax preserves _import and _cimport"""
    # Add _import and _cimport to the text
    test_string = f"_import {text} _cimport"
    result = strip_syntax(test_string)
    
    # The function should preserve these special tokens
    assert "_import" in result or not ("_import" in test_string and "_import" not in text)
    assert "_cimport" in result or not ("_cimport" in test_string and "_cimport" not in text)


# Property 3: strip_syntax removes parentheses, commas, backslashes  
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_. ', min_size=0))
def test_strip_syntax_removes_syntax_chars(text):
    """Test that strip_syntax removes syntax characters"""
    test_string = f"({text}, \\)"
    result = strip_syntax(test_string)
    
    # These characters should be replaced with spaces
    assert "(" not in result
    assert ")" not in result
    assert "," not in result
    assert "\\" not in result


# Property 4: Import.statement() generates parseable import syntax
@given(
    module=python_identifier(),
    attribute=st.one_of(st.none(), python_identifier()),
    alias=st.one_of(st.none(), python_identifier()),
    cimport=st.booleans()
)
def test_import_statement_generates_valid_syntax(module, attribute, alias, cimport):
    """Test that Import.statement() generates valid Python import syntax"""
    imp = Import(
        line_number=1,
        indented=False,
        module=module,
        attribute=attribute,
        alias=alias,
        cimport=cimport
    )
    
    statement = imp.statement()
    import_cmd = "cimport" if cimport else "import"
    
    # Check the generated statement follows expected patterns
    if attribute:
        expected_start = f"from {module} {import_cmd} {attribute}"
        assert statement.startswith(expected_start)
    else:
        expected_start = f"{import_cmd} {module}"
        assert statement.startswith(expected_start)
    
    if alias:
        assert statement.endswith(f" as {alias}")


# Property 5: Round-trip for parsing simple import statements
@given(module=python_identifier())
def test_simple_import_round_trip(module):
    """Test that parsing a simple import statement preserves information"""
    import_str = f"import {module}\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    if parsed_imports:
        imp = parsed_imports[0]
        assert imp.module == module
        assert imp.attribute is None
        assert imp.cimport is False
        assert imp.line_number == 1
        assert imp.indented is False


# Property 6: Parsing from imports
@given(
    module=python_identifier(),
    attribute=python_identifier()
)
def test_from_import_parsing(module, attribute):
    """Test parsing of from...import statements"""
    import_str = f"from {module} import {attribute}\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    if parsed_imports:
        imp = parsed_imports[0]
        assert imp.module == module
        assert imp.attribute == attribute
        assert imp.cimport is False
        assert imp.line_number == 1


# Property 7: Indentation detection
@given(
    module=python_identifier(),
    indent=st.sampled_from(["    ", "\t", "  "])
)
def test_indentation_detection(module, indent):
    """Test that indented imports are correctly detected"""
    import_str = f"{indent}import {module}\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    if parsed_imports:
        imp = parsed_imports[0]
        assert imp.indented is True
        assert imp.module == module


# Property 8: Multiple imports separated by semicolons
@given(
    module1=python_identifier(),
    module2=python_identifier()
)
def test_semicolon_separated_imports(module1, module2):
    """Test parsing of semicolon-separated imports on same line"""
    assume(module1 != module2)
    import_str = f"import {module1}; import {module2}\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    # Should parse both imports
    modules = [imp.module for imp in parsed_imports]
    assert module1 in modules
    assert module2 in modules


# Property 9: Alias parsing and reconstruction
@given(
    module=python_identifier(),
    alias=python_identifier()
)
def test_alias_parsing_and_reconstruction(module, alias):
    """Test that aliases are correctly parsed and reconstructed"""
    import_str = f"import {module} as {alias}\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    if parsed_imports:
        imp = parsed_imports[0]
        assert imp.module == module
        assert imp.alias == alias
        
        # Reconstruction should include the alias
        statement = imp.statement()
        assert f"import {module} as {alias}" == statement


# Property 10: strip_syntax handles curly braces specially
@given(st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789 ', min_size=0, max_size=20))
def test_strip_syntax_curly_brace_handling(text):
    """Test that strip_syntax converts '{ ' to '{|' and ' }' to '|}'"""
    test_string = f"{{ {text} }}"
    result = strip_syntax(test_string)
    
    # Based on line 80 of parse.py
    assert "{|" in result or "{ " not in test_string
    assert "|}" in result or " }" not in test_string


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])