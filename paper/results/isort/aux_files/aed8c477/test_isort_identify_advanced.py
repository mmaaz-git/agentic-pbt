import io
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import isort.identify
from isort.identify import Import, imports, strip_syntax
from isort.parse import normalize_line
from isort.settings import DEFAULT_CONFIG


# Strategy for valid Python identifiers
def python_identifier():
    first_char = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_', min_size=1, max_size=1)
    rest_chars = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_', min_size=0, max_size=20)
    return st.builds(lambda f, r: f + r, first_char, rest_chars)


# Property: normalize_line idempotence
@given(st.text())
def test_normalize_line_idempotence(text):
    """Test that normalize_line is idempotent - applying it twice gives same result"""
    normalized1, _ = normalize_line(text)
    normalized2, _ = normalize_line(normalized1)
    assert normalized1 == normalized2


# Property: strip_syntax with special patterns
@given(st.text(min_size=0, max_size=100))
def test_strip_syntax_special_patterns(text):
    """Test strip_syntax behavior with complex patterns"""
    # Test that the temporary replacements work correctly
    if "_import" in text or "_cimport" in text:
        result = strip_syntax(text)
        # The function should handle these specially
        # It replaces them temporarily and then restores them
        if "_import" in text:
            # Check that _import is preserved (not treated as separate _ and import)
            parts = text.split("_import")
            for part in parts[:-1]:  # All but last part had _import after it
                # The _import should still be present in some form
                pass  # Complex to test without knowing exact positions
    
    # Test the curly brace replacement
    if "{ " in text:
        result = strip_syntax(text)
        # Should be replaced with {|
        assert result.count("{|") >= text.count("{ ")
    
    if " }" in text:
        result = strip_syntax(text)
        # Should be replaced with |}
        assert result.count("|}") >= text.count(" }")


# Property: Parsing imports with comments
@given(
    module=python_identifier(),
    comment=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ', min_size=0, max_size=20)
)
def test_import_with_comment(module, comment):
    """Test that imports with comments are parsed correctly"""
    import_str = f"import {module}  # {comment}\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    if parsed_imports:
        imp = parsed_imports[0]
        assert imp.module == module
        # Comments should not affect the module name


# Property: Multiline import with parentheses
@given(
    module=python_identifier(),
    attributes=st.lists(python_identifier(), min_size=2, max_size=5, unique=True)
)
def test_multiline_import_parentheses(module, attributes):
    """Test parsing of multiline imports with parentheses"""
    attrs_str = ",\n    ".join(attributes)
    import_str = f"from {module} import (\n    {attrs_str}\n)\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    # Should parse all attributes
    parsed_attrs = [imp.attribute for imp in parsed_imports]
    for attr in attributes:
        assert attr in parsed_attrs


# Property: Cimport handling
@given(module=python_identifier())
def test_cimport_parsing(module):
    """Test that cimport statements are correctly identified"""
    import_str = f"cimport {module}\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    if parsed_imports:
        imp = parsed_imports[0]
        assert imp.module == module
        assert imp.cimport is True
        assert imp.statement() == f"cimport {module}"


# Property: From cimport handling
@given(
    module=python_identifier(),
    attribute=python_identifier()
)
def test_from_cimport_parsing(module, attribute):
    """Test that from...cimport statements are correctly parsed"""
    import_str = f"from {module} cimport {attribute}\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    if parsed_imports:
        imp = parsed_imports[0]
        assert imp.module == module
        assert imp.attribute == attribute
        assert imp.cimport is True
        statement = imp.statement()
        assert statement == f"from {module} cimport {attribute}"


# Property: Handling backslash continuations
@given(
    module=python_identifier(),
    attr1=python_identifier(),
    attr2=python_identifier()
)
def test_backslash_continuation(module, attr1, attr2):
    """Test parsing of imports with backslash continuations"""
    assume(attr1 != attr2)
    import_str = f"from {module} import \\\n    {attr1}, \\\n    {attr2}\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    # Should parse both attributes
    parsed_attrs = [imp.attribute for imp in parsed_imports]
    assert attr1 in parsed_attrs
    assert attr2 in parsed_attrs


# Property: Empty and whitespace handling
@given(st.sampled_from([
    "",
    " ",
    "\n",
    "\t",
    "   \n",
    "\n\n",
    "# comment only\n",
    "   # indented comment\n"
]))
def test_empty_and_whitespace(content):
    """Test that empty content and whitespace-only content doesn't crash"""
    stream = io.StringIO(content)
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    # Should not crash and return empty or skip non-imports
    assert isinstance(parsed_imports, list)


# Property: Module names with dots (package imports)
@given(
    parts=st.lists(python_identifier(), min_size=2, max_size=4)
)
def test_dotted_module_names(parts):
    """Test parsing of dotted module names"""
    module = ".".join(parts)
    import_str = f"import {module}\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    if parsed_imports:
        imp = parsed_imports[0]
        assert imp.module == module


# Property: Relative imports
@given(
    dots=st.integers(min_value=1, max_value=5),
    module=st.one_of(st.none(), python_identifier()),
    attribute=python_identifier()
)
def test_relative_imports(dots, module, attribute):
    """Test parsing of relative imports"""
    dot_str = "." * dots
    if module:
        import_str = f"from {dot_str}{module} import {attribute}\n"
    else:
        import_str = f"from {dot_str} import {attribute}\n"
    
    stream = io.StringIO(import_str)
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    if parsed_imports:
        imp = parsed_imports[0]
        assert imp.attribute == attribute
        # Module should include the dots
        if module:
            assert imp.module == f"{dot_str}{module}"
        else:
            assert imp.module == dot_str


# Property: Import statement reconstruction preserves semantics
@given(
    module=python_identifier(),
    attribute=st.one_of(st.none(), python_identifier()),
    alias=st.one_of(st.none(), python_identifier()),
    cimport=st.booleans()
)
def test_import_reconstruction_semantics(module, attribute, alias, cimport):
    """Test that Import.statement() produces semantically equivalent imports"""
    imp = Import(
        line_number=1,
        indented=False,
        module=module,
        attribute=attribute,
        alias=alias,
        cimport=cimport
    )
    
    statement = imp.statement()
    
    # Parse the reconstructed statement
    stream = io.StringIO(statement + "\n")
    parsed = list(imports(stream, config=DEFAULT_CONFIG))
    
    if parsed and len(parsed) == 1:
        parsed_imp = parsed[0]
        # Check semantic equivalence
        assert parsed_imp.module == module
        assert parsed_imp.attribute == attribute
        assert parsed_imp.cimport == cimport
        # Alias might be affected by remove_redundant_aliases config
        if alias and alias != (attribute or module):
            assert parsed_imp.alias == alias


# Edge case: Unicode in comments
@given(module=python_identifier())
@example(module="test")
def test_unicode_in_comments(module):
    """Test imports with unicode characters in comments"""
    import_str = f"import {module}  # 🦄 Unicode comment\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    if parsed_imports:
        imp = parsed_imports[0]
        assert imp.module == module


# Property: Star imports
@given(module=python_identifier())
def test_star_import(module):
    """Test parsing of star imports"""
    import_str = f"from {module} import *\n"
    stream = io.StringIO(import_str)
    
    parsed_imports = list(imports(stream, config=DEFAULT_CONFIG))
    
    if parsed_imports:
        imp = parsed_imports[0]
        assert imp.module == module
        assert imp.attribute == "*"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])