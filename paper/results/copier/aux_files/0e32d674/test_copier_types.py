"""Property-based tests for copier._types module."""

import random
from pathlib import Path

import pytest
from hypothesis import assume, given, strategies as st

# Import the actual implementation module, not the deprecated wrapper
from copier import _types
from copier.errors import PathNotAbsoluteError, PathNotRelativeError


# LazyDict Tests
@given(st.lists(st.tuples(st.text(), st.integers())))
def test_lazydict_idempotence(items):
    """Once a value is computed, it should remain the same."""
    call_counts = {}
    
    def make_value_factory(key, value):
        def factory():
            call_counts[key] = call_counts.get(key, 0) + 1
            return value
        return factory
    
    # Create LazyDict with tracking factories
    lazy_dict = _types.LazyDict({k: make_value_factory(k, v) for k, v in items})
    
    # Access each key multiple times
    for key, expected_value in items:
        first_value = lazy_dict[key]
        second_value = lazy_dict[key]
        third_value = lazy_dict[key]
        
        # Value should be the same each time
        assert first_value == expected_value
        assert second_value == expected_value
        assert third_value == expected_value
        
        # Function should only be called once
        assert call_counts[key] == 1


@given(st.dictionaries(st.text(), st.integers()))
def test_lazydict_setitem_invalidates_cache(data):
    """Setting a value should invalidate any previous lazy computation."""
    assume(len(data) > 0)  # Need at least one item
    
    call_count = 0
    
    def factory():
        nonlocal call_count
        call_count += 1
        return "lazy_value"
    
    key = next(iter(data.keys()))
    
    # Create LazyDict with a lazy value
    lazy_dict = _types.LazyDict({key: factory})
    
    # Access the value (should call factory)
    value1 = lazy_dict[key]
    assert value1 == "lazy_value"
    assert call_count == 1
    
    # Set a new value
    lazy_dict[key] = "new_value"
    
    # Access again (should not call factory, should return new value)
    value2 = lazy_dict[key]
    assert value2 == "new_value"
    assert call_count == 1  # Factory not called again


@given(st.dictionaries(st.text(), st.integers()))
def test_lazydict_dictionary_invariants(data):
    """LazyDict should maintain standard dictionary invariants."""
    lazy_dict = _types.LazyDict({k: lambda v=v: v for k, v in data.items()})
    
    # Length should match
    assert len(lazy_dict) == len(data)
    
    # Keys should match
    assert set(lazy_dict.keys()) == set(data.keys())
    
    # Iteration should yield all keys
    assert set(lazy_dict) == set(data.keys())
    
    # Values should be accessible and correct
    for key, expected_value in data.items():
        assert lazy_dict[key] == expected_value


@given(st.dictionaries(st.text(), st.integers(), min_size=1))
def test_lazydict_deletion(data):
    """Deletion should work for both pending and computed values."""
    lazy_dict = _types.LazyDict({k: lambda v=v: v for k, v in data.items()})
    
    keys_list = list(data.keys())
    # Access some values (compute them)
    for key in keys_list[:len(keys_list)//2]:
        _ = lazy_dict[key]
    
    # Delete all keys
    for key in keys_list:
        del lazy_dict[key]
        assert key not in lazy_dict
        with pytest.raises(KeyError):
            _ = lazy_dict[key]
    
    assert len(lazy_dict) == 0


# Path Validator Tests
@given(st.text(min_size=1))
def test_path_validators_mutual_exclusion(path_str):
    """A path cannot be both absolute and relative."""
    # Clean up the path string to avoid invalid paths
    path_str = path_str.replace('\x00', '').strip()
    assume(path_str and not path_str.isspace())
    
    try:
        path = Path(path_str)
    except (ValueError, OSError):
        # Skip invalid paths
        return
    
    # Check if path is absolute or relative
    is_absolute = path.is_absolute()
    
    if is_absolute:
        # Should pass absolute validator, fail relative validator
        assert _types.path_is_absolute(path) == path
        with pytest.raises(PathNotRelativeError):
            _types.path_is_relative(path)
    else:
        # Should pass relative validator, fail absolute validator
        assert _types.path_is_relative(path) == path
        with pytest.raises(PathNotAbsoluteError):
            _types.path_is_absolute(path)


@given(st.lists(st.sampled_from(['/', 'home', 'user', 'dir', 'file.txt']), min_size=1, max_size=5))
def test_absolute_path_validator(path_parts):
    """Test absolute path validator with constructed paths."""
    if path_parts[0] == '/':
        # Absolute path
        path = Path('/'.join(path_parts))
        assert _types.path_is_absolute(path) == path
    else:
        # Relative path
        path = Path('/'.join(path_parts))
        with pytest.raises(PathNotAbsoluteError):
            _types.path_is_absolute(path)


# Phase Context Manager Tests
@given(st.sampled_from(list(_types.Phase)))
def test_phase_context_manager_restoration(phase):
    """Phase context manager should restore previous phase."""
    # Get initial phase
    initial_phase = _types.Phase.current()
    
    # Use context manager
    with _types.Phase.use(phase):
        assert _types.Phase.current() == phase
    
    # Should be restored
    assert _types.Phase.current() == initial_phase


@given(
    st.sampled_from(list(_types.Phase)),
    st.sampled_from(list(_types.Phase)),
    st.sampled_from(list(_types.Phase))
)
def test_phase_nested_contexts(phase1, phase2, phase3):
    """Nested phase contexts should work correctly."""
    initial_phase = _types.Phase.current()
    
    with _types.Phase.use(phase1):
        assert _types.Phase.current() == phase1
        
        with _types.Phase.use(phase2):
            assert _types.Phase.current() == phase2
            
            with _types.Phase.use(phase3):
                assert _types.Phase.current() == phase3
            
            # Back to phase2
            assert _types.Phase.current() == phase2
        
        # Back to phase1
        assert _types.Phase.current() == phase1
    
    # Back to initial
    assert _types.Phase.current() == initial_phase


@given(st.sampled_from(list(_types.Phase)))
def test_phase_context_manager_exception_handling(phase):
    """Phase should be restored even if exception occurs in context."""
    initial_phase = _types.Phase.current()
    
    try:
        with _types.Phase.use(phase):
            assert _types.Phase.current() == phase
            raise ValueError("Test exception")
    except ValueError:
        pass
    
    # Should still be restored despite exception
    assert _types.Phase.current() == initial_phase