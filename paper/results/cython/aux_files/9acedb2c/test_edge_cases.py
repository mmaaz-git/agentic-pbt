import io
import sys
from contextlib import redirect_stdout, redirect_stderr
import Cython.Debugging


class ObjectWithBadStr:
    """Object with __str__ that raises an exception."""
    def __str__(self):
        raise RuntimeError("__str__ failed!")


class ObjectWithInfiniteStr:
    """Object with __str__ that causes infinite recursion."""
    def __str__(self):
        return str(self)


class ObjectReturningNonString:
    """Object with __str__ that returns non-string."""
    def __str__(self):
        return 42  # Returns int instead of string


def test_object_with_failing_str():
    """Test print_call_chain with object whose __str__ raises exception."""
    obj = ObjectWithBadStr()
    
    f_out = io.StringIO()
    f_err = io.StringIO()
    
    with redirect_stdout(f_out), redirect_stderr(f_err):
        try:
            Cython.Debugging.print_call_chain(obj)
            print("No exception raised - unexpected!")
        except RuntimeError as e:
            print(f"Got expected RuntimeError: {e}")
        except Exception as e:
            print(f"Got unexpected exception: {type(e).__name__}: {e}")


def test_object_with_non_string_str():
    """Test print_call_chain with object whose __str__ returns non-string."""
    obj = ObjectReturningNonString()
    
    f_out = io.StringIO()
    f_err = io.StringIO()
    
    with redirect_stdout(f_out), redirect_stderr(f_err):
        try:
            Cython.Debugging.print_call_chain(obj)
            print("No exception raised - unexpected!")
        except TypeError as e:
            print(f"Got expected TypeError: {e}")
        except Exception as e:
            print(f"Got unexpected exception: {type(e).__name__}: {e}")


def test_bytes_input():
    """Test print_call_chain with bytes input."""
    f_out = io.StringIO()
    f_err = io.StringIO()
    
    with redirect_stdout(f_out), redirect_stderr(f_err):
        Cython.Debugging.print_call_chain(b"test bytes", b"\xff\xfe")
    
    output = f_out.getvalue()
    assert "test bytes" in output or "b'test bytes'" in output


def test_large_string():
    """Test with a very large string argument."""
    large_str = "x" * 1000000  # 1 million characters
    
    f_out = io.StringIO()
    f_err = io.StringIO()
    
    with redirect_stdout(f_out), redirect_stderr(f_err):
        Cython.Debugging.print_call_chain(large_str)
    
    output = f_out.getvalue()
    assert len(output) > 0


if __name__ == "__main__":
    print("Testing edge cases...")
    test_object_with_failing_str()
    test_object_with_non_string_str()
    test_bytes_input()
    test_large_string()
    print("All edge case tests completed!")