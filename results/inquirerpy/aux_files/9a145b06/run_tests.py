"""Run property-based tests for InquirerPy.separator.Separator."""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages")

from hypothesis import given, strategies as st, settings
from InquirerPy.separator import Separator


def run_all_tests():
    """Run all property-based tests."""
    
    print("Testing string representation invariant...")
    test_string_representation_invariant()
    
    print("Testing default value property...")
    test_default_value_property()
    
    print("Testing string representation consistency...")
    test_string_representation_consistency()
    
    print("Testing separator instance check...")
    test_separator_instance_check()
    
    print("Testing multiple separators independence...")
    test_multiple_separators_independence()
    
    print("Testing various input types...")
    test_separator_with_various_types()
    
    print("Testing Unicode handling...")
    test_unicode_handling()
    
    print("Testing separator creation never raises...")
    test_separator_creation_never_raises()
    
    print("\nAll tests completed!")


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
    
    for _ in range(10):
        assert str(separator) == initial_str
    
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
    """Test that Separator can handle various input types."""
    if value is None:
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
        assert False, f"Separator creation raised {type(e).__name__}: {e}"


if __name__ == "__main__":
    run_all_tests()