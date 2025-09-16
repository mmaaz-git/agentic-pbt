"""Additional edge case tests for tqdm.autonotebook."""

import io
import sys
from hypothesis import given, strategies as st, settings, assume
from tqdm.autonotebook import tqdm, trange


@given(
    n=st.integers(min_value=-1000, max_value=-1)
)
def test_trange_negative_values(n):
    """Test trange with negative values."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # trange with negative n should give empty range like range(n)
        result1 = list(trange(n, disable=True))
        result2 = list(range(n))
        assert result1 == result2, f"trange({n}) != range({n})"
    finally:
        sys.stderr = original_stderr


@given(
    start=st.integers(),
    stop=st.integers()
)
def test_trange_arbitrary_start_stop(start, stop):
    """Test trange with arbitrary start and stop values."""
    # Limit the range to avoid memory issues
    assume(abs(stop - start) <= 10000)
    
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        result1 = list(trange(start, stop, disable=True))
        result2 = list(range(start, stop))
        assert result1 == result2, f"trange({start}, {stop}) != range({start}, {stop})"
    finally:
        sys.stderr = original_stderr


@given(
    n=st.one_of(
        st.just(0),
        st.integers(min_value=1, max_value=1),
        st.integers(min_value=100, max_value=10000)  # Reasonable boundary for testing
    )
)
def test_boundary_values(n):
    """Test tqdm with boundary values."""
    
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        result = list(trange(n, disable=True))
        expected = list(range(n))
        assert result == expected, f"Boundary value {n} failed"
    finally:
        sys.stderr = original_stderr


@given(
    step=st.integers(min_value=-10, max_value=10).filter(lambda x: x != 0),
    start=st.integers(min_value=-100, max_value=100), 
    stop=st.integers(min_value=-100, max_value=100)
)
def test_negative_step(start, stop, step):
    """Test trange with negative step values."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        result1 = list(trange(start, stop, step, disable=True))
        result2 = list(range(start, stop, step))
        assert result1 == result2, f"trange({start}, {stop}, {step}) != range({start}, {stop}, {step})"
    finally:
        sys.stderr = original_stderr


def test_trange_zero_step():
    """Test that trange with zero step raises ValueError like range."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # Both should raise ValueError for step=0
        try:
            list(trange(0, 10, 0, disable=True))
            assert False, "trange should raise ValueError for step=0"
        except ValueError:
            pass  # Expected
        
        try:
            list(range(0, 10, 0))
            assert False, "range should raise ValueError for step=0"
        except ValueError:
            pass  # Expected
    finally:
        sys.stderr = original_stderr


@given(
    items=st.one_of(
        st.just([]),  # Empty list
        st.lists(st.none(), min_size=1, max_size=10),  # List of None
        st.just(iter([])),  # Empty iterator
    )
)
def test_edge_case_iterables(items):
    """Test tqdm with edge case iterables."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        result = list(tqdm(items, disable=True))
        expected = list(items) if not hasattr(items, '__iter__') else list(items)
        assert result == expected, "Edge case iterable not handled correctly"
    finally:
        sys.stderr = original_stderr


@given(
    total=st.one_of(
        st.none(),
        st.integers(min_value=0, max_value=1000),
        st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False)
    ),
    items=st.lists(st.integers(), min_size=0, max_size=50)
)
def test_total_parameter(items, total):
    """Test that the total parameter doesn't affect iteration values."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # The total parameter is only for display, shouldn't affect values
        result = list(tqdm(items, total=total, disable=True))
        assert result == items, "total parameter affected iteration values"
    finally:
        sys.stderr = original_stderr


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])