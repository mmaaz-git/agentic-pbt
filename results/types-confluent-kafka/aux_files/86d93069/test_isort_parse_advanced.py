"""Advanced property-based tests for isort.parse module - hunting for bugs"""

import re
from hypothesis import assume, given, strategies as st, settings, example
from hypothesis import note

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.parse import (
    _infer_line_separator, 
    normalize_line,
    import_type,
    strip_syntax,
    skip_line,
    file_contents
)
from isort.settings import Config


# Test skip_line with complex quote combinations
@given(
    st.text(min_size=1).filter(lambda x: '"' in x or "'" in x),
    st.sampled_from(["", "'", '"', "'''", '"""'])
)
def test_skip_line_quote_edge_cases(line, initial_quote):
    """Test skip_line with various quote combinations"""
    # Test that the function doesn't crash with complex quotes
    should_skip, final_quote = skip_line(line, initial_quote, 0, ())
    
    # Count quotes to verify tracking
    single_quotes = line.count("'") - line.count("\\'")
    double_quotes = line.count('"') - line.count('\\"')
    
    # Property: final quote should be empty or a valid quote type
    assert final_quote in ["", "'", '"', "'''", '"""']
    
    # If we end in a triple quote, we should be skipping
    if final_quote in ["'''", '"""']:
        assert should_skip == True


# Test normalize_line with malformed import statements
@given(st.text())
def test_normalize_line_malformed_imports(text):
    """Test normalize_line with potentially malformed import statements"""
    # Create malformed import patterns
    test_cases = [
        f"from{text}import something",
        f"from.{text}cimport thing",
        f"import{text}*",
        f"from...{text}import x",
    ]
    
    for case in test_cases:
        try:
            normalized, raw = normalize_line(case)
            # Should not raise exception
            assert raw == case
            # Should add spaces where needed
            if "from" in case and "import" in case:
                assert " import " in normalized or " cimport " in normalized
        except:
            pass  # Some inputs might still fail, which is ok


# Test strip_syntax with nested structures
@given(st.text())
def test_strip_syntax_nested_structures(text):
    """Test strip_syntax with nested parentheses and complex syntax"""
    # Add complex syntax patterns
    complex_patterns = [
        f"from x import ({text})",
        f"import ({text}, {text})",
        f"from module import \\{text}",
        f"from x import {{{text}}}",
    ]
    
    for pattern in complex_patterns:
        result = strip_syntax(pattern)
        # Check that problematic characters are handled
        assert result.count("(") == 0 or "{|" in result
        assert result.count(")") == 0 or "|}" in result
        # Backslashes should be removed
        assert "\\" not in result


# Test import_type with edge case lines
@given(st.text(alphabet=st.characters(blacklist_categories=["Cs"])))
def test_import_type_edge_cases(prefix):
    """Test import_type with various prefixes before import keywords"""
    assume(len(prefix) < 100)  # Avoid huge inputs
    
    # Test with text before import keywords
    test_lines = [
        f"{prefix}import module",
        f"{prefix}from module import x",
        f"{prefix}cimport something",
    ]
    
    config = Config()
    for line in test_lines:
        result = import_type(line, config)
        # If there's any non-whitespace before the keyword, it shouldn't be detected
        if prefix and not prefix.isspace():
            if not line.startswith(("import ", "from ", "cimport ")):
                assert result is None


# Test file_contents with import variations
@given(st.lists(st.sampled_from([
    "import os",
    "from sys import argv",
    "from . import module",
    "from .. import parent",
    "import os, sys",
    "from os import (path, \n    environ)",
    "import module as m",
    "from module import func as f",
    ""
]), min_size=0, max_size=20))
@settings(max_examples=50, deadline=10000)
def test_file_contents_import_variations(lines):
    """Test file_contents with various import statement combinations"""
    content = "\n".join(lines)
    
    try:
        result = file_contents(content, Config())
        
        # Count actual import lines (non-empty, starting with import/from)
        import_lines = [l for l in lines if l and (l.startswith("import ") or l.startswith("from "))]
        
        # Property: imports dict should contain categorized imports
        assert isinstance(result.imports, dict)
        
        # Property: import_index should be >= -1
        assert result.import_index >= -1
        
        # If there are imports, import_index should not be -1
        if import_lines:
            assert result.import_index >= 0
    except:
        # Some combinations might cause exceptions
        pass


# Test skip_line with semicolons and imports
@given(st.text())
def test_skip_line_with_semicolons(line):
    """Test skip_line behavior with semicolons"""
    if ";" in line:
        should_skip, quote = skip_line(line, "", 0, (), needs_import=True)
        
        # If line has semicolon with non-import statement, should skip
        parts = line.split("#")[0].split(";")
        has_non_import = any(
            part.strip() and 
            not part.strip().startswith("from ") and
            not part.strip().startswith(("import ", "cimport "))
            for part in parts
        )
        
        if has_non_import:
            assert should_skip == True


# Test normalize_line with regex edge cases
@given(st.text(min_size=1))
def test_normalize_line_regex_safety(text):
    """Test that normalize_line handles regex special characters safely"""
    # Add regex special characters
    special_chars = r".$^*+?{}[]|()\\"
    
    for char in special_chars:
        test_line = f"from{char}import x"
        try:
            normalized, raw = normalize_line(test_line)
            assert raw == test_line
            # Should not crash on regex special chars
        except re.error:
            # This would indicate a bug - regex not properly escaped
            assert False, f"Regex error with character: {char}"
        except:
            pass  # Other exceptions are ok


# Test strip_syntax with from...import edge cases
@given(st.text())
def test_strip_syntax_keyword_removal(text):
    """Test that strip_syntax correctly removes import keywords"""
    # Ensure keywords are in the text
    test_cases = [
        f"from {text} import {text}",
        f"import {text}",
        f"cimport {text}",
    ]
    
    for case in test_cases:
        result = strip_syntax(case)
        words = result.split()
        
        # Keywords should be removed
        assert "from" not in words or text == "from"
        assert "import" not in words or text == "import" 
        assert "cimport" not in words or text == "cimport"


# Test complex multiline import scenarios
@given(st.text(min_size=0, max_size=50))
@example("")  # Empty string edge case
@example("\\")  # Single backslash
@example("'''")  # Triple quote
def test_skip_line_multiline_scenarios(content):
    """Test skip_line with content that might span multiple lines"""
    lines = [
        f"import module\\{content}",
        f"from package import ({content}",
        f"'''{content}",
        f'"""{content}',
    ]
    
    in_quote = ""
    for i, line in enumerate(lines):
        try:
            should_skip, in_quote = skip_line(line, in_quote, i, ())
            # Should handle these cases without crashing
            assert isinstance(should_skip, bool)
            assert isinstance(in_quote, str)
        except:
            pass  # Some edge cases might fail


# Test import_type with noqa comments
@given(st.text())
def test_import_type_noqa_handling(base_text):
    """Test import_type with noqa comments"""
    # Config with honor_noqa = True
    config = Config(honor_noqa=True)
    
    test_lines = [
        f"{base_text} # noqa",
        f"{base_text} # NOQA",
        f"{base_text} #noqa",
        f"import os  # noqa",
        f"from sys import argv  # noqa",
    ]
    
    for line in test_lines:
        result = import_type(line, config)
        # Lines ending with noqa should return None when honor_noqa is True
        if line.lower().rstrip().endswith("noqa"):
            assert result is None
        

# Test potential integer overflow in skip_line
@given(
    st.text(min_size=0, max_size=1000),
    st.integers(min_value=-10, max_value=10**9)
)
def test_skip_line_index_bounds(line, index):
    """Test skip_line with various index values"""
    try:
        should_skip, quote = skip_line(line, "", index, ())
        # Should handle any index without crashing
        assert isinstance(should_skip, bool)
    except:
        # Very large indices might cause issues
        pass


# Test file_contents with large numbers of imports
@given(st.integers(min_value=0, max_value=100))
@settings(max_examples=10, deadline=30000)
def test_file_contents_many_imports(n):
    """Test file_contents with many import statements"""
    imports = [f"import module{i}" for i in range(n)]
    content = "\n".join(imports)
    
    try:
        result = file_contents(content, Config())
        # Should handle many imports without issues
        assert result.original_line_count == len(imports) if imports else 0
    except:
        pass