"""Advanced property-based tests for tqdm.autonotebook."""

import io
import sys
from hypothesis import given, strategies as st, settings, assume
from tqdm.autonotebook import tqdm, trange


@given(
    items=st.lists(st.integers(), min_size=0, max_size=100)
)
def test_iterator_protocol_completeness(items):
    """Test that tqdm properly implements the iterator protocol."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # Test that tqdm returns an iterator
        wrapped = tqdm(items, disable=True)
        assert hasattr(wrapped, '__iter__'), "tqdm doesn't have __iter__"
        assert hasattr(wrapped, '__next__'), "tqdm doesn't have __next__"
        
        # Test that iterator protocol works correctly
        wrapped_iter = iter(tqdm(items, disable=True))
        for expected in items:
            actual = next(wrapped_iter)
            assert actual == expected, f"Iterator protocol failed: {actual} != {expected}"
        
        # Ensure StopIteration is raised
        try:
            next(wrapped_iter)
            assert False, "StopIteration not raised at end of iteration"
        except StopIteration:
            pass  # Expected
    finally:
        sys.stderr = original_stderr


@given(
    items=st.lists(st.integers(), min_size=1, max_size=100)
)
def test_multiple_iterations(items):
    """Test that tqdm can only be iterated once (like most iterators)."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        wrapped = tqdm(items, disable=True)
        
        # First iteration should work
        result1 = list(wrapped)
        assert result1 == items
        
        # Second iteration should be empty (standard iterator behavior)
        result2 = list(wrapped)
        assert result2 == [], "tqdm iterator should be exhausted after first iteration"
    finally:
        sys.stderr = original_stderr


@given(
    items=st.lists(st.integers(), min_size=0, max_size=50),
    initial=st.integers(min_value=0, max_value=100)
)
def test_initial_parameter(items, initial):
    """Test that the initial parameter doesn't affect iteration values."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # Initial parameter is for display only, shouldn't affect values
        result = list(tqdm(items, initial=initial, disable=True))
        assert result == items, "initial parameter affected iteration values"
    finally:
        sys.stderr = original_stderr


@given(
    n=st.integers(min_value=0, max_value=100),
    leave=st.one_of(st.booleans(), st.none())
)
def test_leave_parameter(n, leave):
    """Test that the leave parameter doesn't affect iteration values."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # Leave parameter is for display only
        result = list(trange(n, leave=leave, disable=True))
        assert result == list(range(n)), "leave parameter affected iteration"
    finally:
        sys.stderr = original_stderr


@given(
    items=st.lists(st.integers(), min_size=0, max_size=50),
    position=st.one_of(st.none(), st.integers(min_value=0, max_value=10))
)
def test_position_parameter(items, position):
    """Test that the position parameter doesn't affect iteration values."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # Position parameter is for display only
        result = list(tqdm(items, position=position, disable=True))
        assert result == items, "position parameter affected iteration values"
    finally:
        sys.stderr = original_stderr


class CustomIterable:
    """Custom iterable class for testing."""
    def __init__(self, items):
        self.items = items
    
    def __iter__(self):
        return iter(self.items)
    
    def __len__(self):
        return len(self.items)


@given(
    items=st.lists(st.integers(), min_size=0, max_size=50)
)
def test_custom_iterable(items):
    """Test that tqdm works with custom iterable objects."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        custom = CustomIterable(items)
        result = list(tqdm(custom, disable=True))
        assert result == items, "tqdm failed with custom iterable"
    finally:
        sys.stderr = original_stderr


@given(
    items=st.lists(st.integers(), min_size=0, max_size=50),
    smoothing=st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
)
def test_smoothing_parameter(items, smoothing):
    """Test that the smoothing parameter doesn't affect iteration values."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # Smoothing is for speed estimation only
        result = list(tqdm(items, smoothing=smoothing, disable=True))
        assert result == items, "smoothing parameter affected iteration values"
    finally:
        sys.stderr = original_stderr


@given(
    desc=st.text(alphabet=st.characters(blacklist_categories=("Cc", "Cs")), min_size=0, max_size=100)
)
def test_unicode_description(desc):
    """Test that tqdm handles unicode descriptions correctly."""
    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    
    try:
        # Unicode in description shouldn't affect iteration
        items = list(range(10))
        result = list(tqdm(items, desc=desc, disable=True))
        assert result == items, f"Unicode description '{desc}' affected iteration"
    finally:
        sys.stderr = original_stderr


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])