"""Property-based tests for tqdm.autonotebook using Hypothesis."""

import io
import sys
from hypothesis import given, strategies as st, settings, assume
from tqdm.autonotebook import tqdm, trange


@given(
    n=st.integers(min_value=0, max_value=1000),
    start=st.integers(min_value=-100, max_value=100),
    stop=st.integers(min_value=-100, max_value=100)
)
def test_trange_equivalence_to_tqdm_range(n, start, stop):
    """Test that trange(*args) is equivalent to tqdm(range(*args))."""
    # Redirect stderr to avoid progress bar output
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # Test single argument: trange(n) == tqdm(range(n))
        result1 = list(trange(n, disable=True))
        result2 = list(tqdm(range(n), disable=True))
        assert result1 == result2, f"trange({n}) != tqdm(range({n}))"
        
        # Test two arguments: trange(start, stop) == tqdm(range(start, stop))
        result3 = list(trange(start, stop, disable=True))
        result4 = list(tqdm(range(start, stop), disable=True))
        assert result3 == result4, f"trange({start}, {stop}) != tqdm(range({start}, {stop}))"
    finally:
        sys.stderr = original_stderr


@given(
    step=st.integers(min_value=1, max_value=10),
    start=st.integers(min_value=-50, max_value=50),
    stop=st.integers(min_value=-50, max_value=50)
)
def test_trange_with_step(start, stop, step):
    """Test that trange with step argument works correctly."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # Test three arguments: trange(start, stop, step) == tqdm(range(start, stop, step))
        result1 = list(trange(start, stop, step, disable=True))
        result2 = list(tqdm(range(start, stop, step), disable=True))
        assert result1 == result2, f"trange({start}, {stop}, {step}) != tqdm(range({start}, {stop}, {step}))"
    finally:
        sys.stderr = original_stderr


@given(
    items=st.lists(st.integers(), min_size=0, max_size=100)
)
def test_iterator_value_preservation(items):
    """Test that tqdm preserves all values from the iterable it wraps."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # The docstring says it "acts exactly like the original iterable"
        result = list(tqdm(items, disable=True))
        assert result == items, f"tqdm altered the iterable values"
        
        # Test that order is preserved
        for i, (original, wrapped) in enumerate(zip(items, tqdm(items, disable=True))):
            assert original == wrapped, f"Value at index {i} was altered"
    finally:
        sys.stderr = original_stderr


@given(
    items=st.lists(st.text(min_size=0, max_size=10), min_size=0, max_size=50)
)
def test_iterator_preservation_with_strings(items):
    """Test that tqdm preserves string values correctly."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        result = list(tqdm(items, disable=True))
        assert result == items, "tqdm altered string values"
    finally:
        sys.stderr = original_stderr


@given(
    items=st.lists(
        st.one_of(
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(min_size=0, max_size=10),
            st.none()
        ),
        min_size=0,
        max_size=50
    )
)
def test_mixed_type_preservation(items):
    """Test that tqdm preserves mixed type iterables."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        result = list(tqdm(items, disable=True))
        assert result == items, "tqdm altered mixed type values"
        assert all(type(a) == type(b) for a, b in zip(items, result)), "tqdm changed types"
    finally:
        sys.stderr = original_stderr


@given(
    n=st.integers(min_value=0, max_value=100),
    desc=st.text(min_size=0, max_size=20),
    unit=st.text(min_size=1, max_size=10)
)
def test_disabled_mode_passthrough(n, desc, unit):
    """Test that disabled tqdm acts as a pure pass-through."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # When disabled, tqdm should just return the iterable unchanged
        items = list(range(n))
        result = list(tqdm(items, disable=True, desc=desc, unit=unit))
        assert result == items, "Disabled tqdm didn't pass through values correctly"
        
        # Test with trange as well
        result2 = list(trange(n, disable=True, desc=desc, unit=unit))
        assert result2 == list(range(n)), "Disabled trange didn't pass through correctly"
    finally:
        sys.stderr = original_stderr


@given(
    items=st.lists(st.integers(), min_size=0, max_size=100)
)
def test_length_preservation(items):
    """Test that tqdm preserves the length of the iterable."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        result = list(tqdm(items, disable=True))
        assert len(result) == len(items), f"Length changed: {len(items)} -> {len(result)}"
    finally:
        sys.stderr = original_stderr


@given(
    items=st.lists(st.integers(), min_size=1, max_size=100).filter(lambda x: len(x) == len(set(x)))
)
def test_uniqueness_preservation(items):
    """Test that tqdm preserves uniqueness of elements."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        result = list(tqdm(items, disable=True))
        assert len(set(result)) == len(set(items)), "tqdm altered uniqueness of elements"
    finally:
        sys.stderr = original_stderr


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])