"""Property-based tests for InquirerPy.separator.Separator using Hypothesis."""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages")

from hypothesis import given, strategies as st, settings
from InquirerPy.separator import Separator


@given(st.text())
def test_string_representation_invariant(line):
    """Test that str(Separator(line)) always equals line."""
    separator = Separator(line)
    assert str(separator) == line


def test_default_value_property():
    """Test that Separator() has default string representation of 15 dashes."""
    separator = Separator()
    assert str(separator) == "-" * 15
    assert str(separator) == "---------------"


@given(st.text(min_size=0, max_size=1000))
def test_string_representation_consistency(line):
    """Test that the string representation remains consistent after creation."""
    separator = Separator(line)
    initial_str = str(separator)
    
    # Call str() multiple times to ensure consistency
    for _ in range(10):
        assert str(separator) == initial_str
    
    # The value should equal the input line
    assert initial_str == line


@given(st.text())
def test_separator_instance_check(line):
    """Test that created objects are correctly identified as Separator instances."""
    separator = Separator(line)
    assert isinstance(separator, Separator)


@given(st.lists(st.text(), min_size=1, max_size=100))
def test_multiple_separators_independence(lines):
    """Test that multiple Separator instances are independent."""
    separators = [Separator(line) for line in lines]
    
    # Each separator should maintain its own line value
    for sep, expected_line in zip(separators, lines):
        assert str(sep) == expected_line


@given(st.one_of(
    st.text(),
    st.none(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.lists(st.text())
))
def test_separator_with_various_types(value):
    """Test that Separator can handle various input types.
    
    The constructor accepts any type, and the __str__ method
    returns _line directly without modification.
    """
    if value is None:
        # None is a special case - the constructor doesn't have type hints
        # but we can test what happens
        separator = Separator(value)
        assert str(separator) == value
    else:
        separator = Separator(value)
        assert str(separator) == value


@given(st.text(alphabet=st.characters(blacklist_categories=("Cs",)), min_size=0, max_size=10000))
def test_unicode_handling(line):
    """Test that Separator correctly handles Unicode strings."""
    separator = Separator(line)
    assert str(separator) == line


@given(st.text())
@settings(max_examples=1000)
def test_separator_creation_never_raises(line):
    """Test that creating a Separator never raises an exception for valid strings."""
    try:
        separator = Separator(line)
        _ = str(separator)
    except Exception as e:
        # If an exception is raised, the test fails
        assert False, f"Separator creation raised {type(e).__name__}: {e}"