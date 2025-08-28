"""Tests to confirm bugs in numpy.typing module."""

import numpy.typing as npt
from hypothesis import given, strategies as st, settings


# Bug 1: Error message inconsistency with repr vs str for attribute names
@given(st.text().filter(lambda x: x not in dir(npt) and x != "NBitBase" and repr(x) != f"'{x}'"))
@settings(max_examples=100)
def test_error_message_repr_inconsistency(attr_name):
    """Test that error messages use inconsistent repr for attribute names."""
    try:
        getattr(npt, attr_name)
        assert False, f"Expected AttributeError for {attr_name}"
    except AttributeError as e:
        error_msg = str(e)
        # The error message uses repr(name) instead of name in the f-string
        # This causes inconsistencies for special characters
        expected_with_str = f"module 'numpy.typing' has no attribute '{attr_name}'"
        expected_with_repr = f"module 'numpy.typing' has no attribute {repr(attr_name)}"
        
        # The bug: error message uses repr(name) not the raw string
        assert error_msg == expected_with_repr, f"Uses repr: {error_msg}"
        # This should be true for consistency but isn't:
        assert error_msg != expected_with_str, f"Inconsistent format"


# Bug 2: NBitBase subclass restriction doesn't handle special characters properly
@given(st.text(min_size=1).filter(lambda x: '\x00' in x))
@settings(max_examples=10)
def test_nbitbase_null_character_crash(class_name):
    """Test that NBitBase subclass restriction crashes on null characters."""
    # The __init_subclass__ method doesn't handle null characters
    # It should raise TypeError about inheriting from final class,
    # but instead crashes with ValueError about null characters
    try:
        type(class_name, (npt.NBitBase,), {})
        assert False, f"Should not be able to create subclass {repr(class_name)}"
    except ValueError as e:
        # This is the bug - it crashes with ValueError instead of TypeError
        assert "null character" in str(e).lower()
    except TypeError as e:
        # This is what we expect but don't get for null characters
        assert False, f"Got expected TypeError instead of ValueError for {repr(class_name)}"