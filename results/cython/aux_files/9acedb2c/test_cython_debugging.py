import io
import sys
from contextlib import redirect_stdout, redirect_stderr
from hypothesis import given, strategies as st, settings
import Cython.Debugging


@given(st.data())
def test_print_call_chain_no_crash_various_types(data):
    """Test that print_call_chain doesn't crash on various input types."""
    args = data.draw(st.lists(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=True, allow_infinity=True),
            st.text(),
            st.binary(),
            st.lists(st.integers(), max_size=5),
            st.dictionaries(st.text(max_size=10), st.integers(), max_size=5),
            st.tuples(st.integers(), st.text(max_size=10)),
            st.sets(st.integers(), max_size=5),
            st.complex_numbers(allow_nan=True, allow_infinity=True),
        ),
        max_size=10
    ))
    
    # Capture both stdout and stderr to prevent output pollution
    f_out = io.StringIO()
    f_err = io.StringIO()
    
    with redirect_stdout(f_out), redirect_stderr(f_err):
        try:
            Cython.Debugging.print_call_chain(*args)
        except Exception as e:
            # The function should not raise any exceptions
            raise AssertionError(f"print_call_chain raised {type(e).__name__}: {e}")
    
    # Verify some output was produced
    output = f_out.getvalue()
    assert isinstance(output, str)
    assert len(output) > 0  # Should produce some output


@given(st.lists(st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.text(max_size=10),
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=3),
        st.dictionaries(st.text(max_size=5), children, max_size=3),
    ),
    max_leaves=20
), max_size=5))
def test_print_call_chain_recursive_structures(args):
    """Test that print_call_chain handles recursive/nested data structures."""
    f_out = io.StringIO()
    f_err = io.StringIO()
    
    with redirect_stdout(f_out), redirect_stderr(f_err):
        try:
            Cython.Debugging.print_call_chain(*args)
        except RecursionError:
            # RecursionError might be acceptable for deeply nested structures
            pass
        except Exception as e:
            raise AssertionError(f"Unexpected exception {type(e).__name__}: {e}")
    
    # Function should either complete or raise RecursionError for deep structures
    assert True


class CustomObject:
    """Custom object to test __str__ conversion."""
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        if self.value == "raise":
            raise ValueError("Cannot convert to string")
        elif self.value == "recursive":
            return str(self)  # Infinite recursion
        else:
            return f"CustomObject({self.value})"


@given(st.lists(st.sampled_from(["normal", "raise", "recursive", None]), max_size=5))
def test_print_call_chain_custom_objects(values):
    """Test print_call_chain with custom objects that may have problematic __str__ methods."""
    objects = [CustomObject(v) if v else None for v in values]
    
    f_out = io.StringIO()
    f_err = io.StringIO()
    
    with redirect_stdout(f_out), redirect_stderr(f_err):
        try:
            Cython.Debugging.print_call_chain(*objects)
        except (ValueError, RecursionError) as e:
            # These exceptions come from our custom __str__ methods
            # The function uses map(str, args), so these will propagate
            pass
        except Exception as e:
            raise AssertionError(f"Unexpected exception {type(e).__name__}: {e}")


@given(st.integers(min_value=0, max_value=1000))
def test_print_call_chain_many_args(num_args):
    """Test print_call_chain with varying number of arguments."""
    args = list(range(num_args))
    
    f_out = io.StringIO()
    f_err = io.StringIO()
    
    with redirect_stdout(f_out), redirect_stderr(f_err):
        try:
            Cython.Debugging.print_call_chain(*args)
        except Exception as e:
            raise AssertionError(f"Failed with {num_args} args: {type(e).__name__}: {e}")
    
    output = f_out.getvalue()
    assert isinstance(output, str)
    
    # When args are provided, they should appear in the output
    if num_args > 0:
        first_line = output.split('\n')[0]
        # The function joins args with spaces
        assert ' '.join(map(str, args[:min(10, num_args)])) in first_line


@given(st.data())
@settings(max_examples=100)
def test_print_call_chain_unicode_and_special_strings(data):
    """Test print_call_chain with various unicode and special string inputs."""
    special_strings = data.draw(st.lists(
        st.one_of(
            st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"]), min_size=0, max_size=100),
            st.sampled_from(["", "\n", "\t", "\r", "\x00", "\\", "'", '"', "`"]),
            st.sampled_from(["🦄", "你好", "مرحبا", "🔥💧⚡", "Ω≈ç√∫"]),
        ),
        max_size=10
    ))
    
    f_out = io.StringIO()
    f_err = io.StringIO()
    
    with redirect_stdout(f_out), redirect_stderr(f_err):
        try:
            Cython.Debugging.print_call_chain(*special_strings)
        except Exception as e:
            raise AssertionError(f"Failed with special strings: {type(e).__name__}: {e}")
    
    output = f_out.getvalue()
    assert isinstance(output, str)