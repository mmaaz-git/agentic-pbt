"""Property-based tests for isort.core module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from io import StringIO
from hypothesis import given, strategies as st, assume, settings
import isort.core
from isort.format import format_natural, format_simplified, remove_whitespace
from isort.settings import Config


# Strategy for generating valid Python import statements
import_statement = st.one_of(
    # Simple imports: "import x"
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20).map(
        lambda x: f"import {x}"
    ),
    # Module imports: "import x.y.z"
    st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=10),
        min_size=2,
        max_size=4
    ).map(lambda parts: f"import {'.'.join(parts)}"),
    # From imports: "from x import y"
    st.tuples(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20)
    ).map(lambda t: f"from {t[0]} import {t[1]}"),
    # From module imports: "from x.y import z"
    st.tuples(
        st.lists(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=10),
            min_size=2,
            max_size=3
        ),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20)
    ).map(lambda t: f"from {'.'.join(t[0])} import {t[1]}")
)

# Strategy for simplified format (what format_simplified produces)
simplified_format = st.one_of(
    # Simple module: "module"
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20),
    # Dotted path: "module.submodule.item"
    st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=10),
        min_size=2,
        max_size=5
    ).map(lambda parts: '.'.join(parts))
)


@given(import_statement)
@settings(max_examples=1000)
def test_format_simplified_natural_round_trip(import_line):
    """Test that format_natural(format_simplified(x)) preserves the import."""
    simplified = format_simplified(import_line)
    restored = format_natural(simplified)
    
    # The round-trip should preserve the semantic meaning
    # Re-simplifying should give the same simplified form
    assert format_simplified(restored) == simplified


@given(simplified_format)
@settings(max_examples=1000) 
def test_format_natural_creates_valid_import(simplified):
    """Test that format_natural creates a valid Python import statement."""
    result = format_natural(simplified)
    
    # Result should start with either 'import' or 'from'
    assert result.startswith(('import ', 'from '))
    
    # If it's a from import, it should contain ' import '
    if result.startswith('from '):
        assert ' import ' in result


@given(
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=100),
    st.sampled_from(['\n', '\r\n', '\r']),
    st.booleans()
)
def test_has_changed_consistency(before, after, line_separator, ignore_whitespace):
    """Test _has_changed function for consistency."""
    result1 = isort.core._has_changed(before, after, line_separator, ignore_whitespace)
    result2 = isort.core._has_changed(before, after, line_separator, ignore_whitespace)
    
    # Calling with same inputs should give same result
    assert result1 == result2
    
    # If before and after are identical (after stripping), should return False
    if before.strip() == after.strip():
        assert not result1


@given(
    st.text(min_size=0, max_size=100),
    st.sampled_from(['\n', '\r\n'])
)
def test_has_changed_reflexivity(text, line_separator):
    """Test that _has_changed returns False for identical inputs."""
    result = isort.core._has_changed(text, text, line_separator, ignore_whitespace=False)
    assert not result


# Generate simple Python code with imports
python_code_with_imports = st.one_of(
    # Single import
    import_statement.map(lambda imp: f"{imp}\n"),
    # Multiple imports
    st.lists(import_statement, min_size=2, max_size=5).map(
        lambda imps: '\n'.join(imps) + '\n'
    ),
    # Imports with code after
    st.tuples(
        st.lists(import_statement, min_size=1, max_size=3),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz =():\n    ", min_size=1, max_size=50)
    ).map(lambda t: '\n'.join(t[0]) + '\n\n' + t[1])
)


@given(python_code_with_imports)
@settings(max_examples=500, deadline=5000)
def test_process_idempotence(code):
    """Test that running process twice produces the same result."""
    # First pass
    input1 = StringIO(code)
    output1 = StringIO()
    config = Config()
    
    try:
        changed1 = isort.core.process(
            input1, output1, 
            extension="py",
            raise_on_skip=False,
            config=config
        )
    except Exception:
        # Skip if the code causes an error (e.g., syntax issues)
        assume(False)
    
    result1 = output1.getvalue()
    
    # Second pass on the output of first pass
    input2 = StringIO(result1)
    output2 = StringIO()
    
    try:
        changed2 = isort.core.process(
            input2, output2,
            extension="py", 
            raise_on_skip=False,
            config=config
        )
    except Exception:
        assume(False)
    
    result2 = output2.getvalue()
    
    # The second pass should not change anything
    assert result1 == result2
    assert not changed2  # Second pass should report no changes


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20))
def test_format_simplified_removes_import_keywords(module_name):
    """Test that format_simplified removes 'import' keyword."""
    import_line = f"import {module_name}"
    result = format_simplified(import_line)
    
    # Should not contain 'import' keyword
    assert 'import' not in result.lower()
    assert result == module_name


@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20)
)  
def test_format_simplified_converts_from_import(module, item):
    """Test that format_simplified converts 'from X import Y' to 'X.Y'."""
    import_line = f"from {module} import {item}"
    result = format_simplified(import_line)
    
    # Should be in dotted format
    assert result == f"{module}.{item}"
    assert 'from' not in result
    assert 'import' not in result