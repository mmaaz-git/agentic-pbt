"""Direct tests confirming bugs in numpy.typing module."""

import numpy.typing as npt


def test_bug1_error_message_repr():
    """Bug: Error message uses repr() incorrectly for attribute names."""
    # Test with a simple case - newline character
    attr_name = '\n'
    
    try:
        getattr(npt, attr_name)
        assert False, "Should have raised AttributeError"
    except AttributeError as e:
        error_msg = str(e)
        
        # What we expect (consistent with Python's standard AttributeError format)
        expected = f"module 'numpy.typing' has no attribute '{attr_name}'"
        
        # What we actually get (uses repr internally)
        actual_expected = f"module 'numpy.typing' has no attribute {repr(attr_name)}"
        
        print(f"Error message: {repr(error_msg)}")
        print(f"Expected format: {repr(expected)}")
        print(f"Actual format: {repr(actual_expected)}")
        
        # The bug: message uses repr(name) not name in f-string
        assert error_msg == actual_expected
        assert error_msg != expected  # This shows the inconsistency


def test_bug2_nbitbase_null_character():
    """Bug: NBitBase subclass validation crashes on null characters."""
    class_name = "Test\x00Class"
    
    try:
        # Try to create a subclass with null character in name
        MyClass = type(class_name, (npt.NBitBase,), {})
        assert False, "Should not allow subclass creation"
    except ValueError as e:
        # BUG: Crashes with ValueError about null characters
        print(f"Got ValueError: {e}")
        assert "null character" in str(e).lower()
        # This is the bug - it should give TypeError about final class
        # but instead crashes earlier due to null character
    except TypeError as e:
        # This is what we'd expect based on NBitBase.__init_subclass__
        assert False, f"Got expected TypeError (no bug): {e}"


if __name__ == "__main__":
    print("Testing Bug 1: Error message repr inconsistency")
    test_bug1_error_message_repr()
    print("✓ Bug 1 confirmed\n")
    
    print("Testing Bug 2: NBitBase null character crash")
    test_bug2_nbitbase_null_character()
    print("✓ Bug 2 confirmed")