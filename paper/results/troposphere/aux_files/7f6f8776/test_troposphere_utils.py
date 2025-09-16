"""Property-based tests for troposphere.utils module"""

import pytest
from hypothesis import given, strategies as st, assume
from unittest.mock import MagicMock, Mock
import troposphere.utils as utils


# Test the sum() function behavior used in get_events for list flattening
@given(st.lists(st.lists(st.integers())))
def test_sum_list_flattening_property(nested_lists):
    """Test that sum() with [] as start value correctly flattens lists"""
    # This is what the code does: sum(event_list, [])
    try:
        result = sum(nested_lists, [])
        # Verify it actually flattens the list
        expected = []
        for sublist in nested_lists:
            expected.extend(sublist)
        assert result == expected
    except TypeError as e:
        # sum() might fail with certain inputs
        pytest.fail(f"sum() failed to flatten list: {e}")


# Test with event-like objects to match real usage
class MockEvent:
    def __init__(self, event_id, resource_status=None, resource_type=None):
        self.event_id = event_id
        self.resource_status = resource_status
        self.resource_type = resource_type
    
    def __eq__(self, other):
        return self.event_id == other.event_id
    
    def __hash__(self):
        return hash(self.event_id)


@given(st.lists(st.lists(st.integers(min_value=0, max_value=1000), min_size=0, max_size=10), min_size=0, max_size=10))
def test_get_events_list_operations(event_batches):
    """Test get_events list operations with mock connection"""
    # Create mock events from the integer data
    mock_batches = []
    for batch in event_batches:
        mock_batch = [MockEvent(event_id=f"event-{i}") for i in batch]
        mock_batches.append(mock_batch)
    
    # Create mock connection that returns batches
    mock_conn = MagicMock()
    batch_iter = iter(mock_batches)
    
    def describe_side_effect(stackname, next_token):
        try:
            batch = next(batch_iter)
            result = MagicMock()
            result.__iter__ = lambda self: iter(batch)
            result.next_token = None if batch == mock_batches[-1] else "token"
            return result
        except StopIteration:
            result = MagicMock()
            result.__iter__ = lambda self: iter([])
            result.next_token = None
            return result
    
    mock_conn.describe_stack_events.side_effect = describe_side_effect
    
    # Test the actual function
    if mock_batches:  # Only test if we have batches
        try:
            result = list(utils.get_events(mock_conn, "test-stack"))
            
            # Verify the flattening worked
            expected = []
            for batch in mock_batches:
                expected.extend(batch)
            expected = list(reversed(expected))
            
            assert len(result) == len(expected)
            for r, e in zip(result, expected):
                assert r.event_id == e.event_id
        except Exception as e:
            pytest.fail(f"get_events failed: {e}")


# Test edge case: what happens with non-list items?
@given(st.lists(st.one_of(
    st.lists(st.integers()),
    st.integers(),  # Non-list items
    st.none(),      # None values
)))
def test_sum_with_mixed_types(mixed_list):
    """Test sum() behavior with mixed types (lists and non-lists)"""
    # Filter to only include cases that would break
    has_non_list = any(not isinstance(item, list) for item in mixed_list)
    assume(has_non_list)
    
    try:
        result = sum(mixed_list, [])
        # If it succeeds, all items must have been lists
        assert all(isinstance(item, list) for item in mixed_list)
    except TypeError:
        # This is expected when non-list items are present
        assert any(not isinstance(item, list) for item in mixed_list)


# Test the tail function's event tracking
@given(
    st.lists(st.integers(min_value=0, max_value=100), min_size=1, max_size=20, unique=True),
    st.booleans()
)
def test_tail_event_tracking(event_ids, include_initial):
    """Test that tail correctly tracks seen events"""
    # Create mock events
    initial_events = [MockEvent(f"event-{i}") for i in event_ids[:len(event_ids)//2]]
    
    # Mock connection
    mock_conn = MagicMock()
    call_count = [0]
    
    def get_events_side_effect(conn, stackname):
        if call_count[0] == 0:
            call_count[0] += 1
            return initial_events
        else:
            # Return empty after first call to avoid infinite loop
            raise KeyboardInterrupt("Breaking infinite loop for test")
    
    # Monkey patch get_events
    original_get_events = utils.get_events
    utils.get_events = get_events_side_effect
    
    # Track logged events
    logged_events = []
    def log_func(e):
        logged_events.append(e)
    
    try:
        utils.tail(mock_conn, "test-stack", log_func=log_func, include_initial=include_initial)
    except KeyboardInterrupt:
        pass  # Expected - we break the infinite loop
    finally:
        # Restore original function
        utils.get_events = original_get_events
    
    # Verify initial events were logged correctly
    if include_initial:
        assert len(logged_events) == len(initial_events)
        for logged, expected in zip(logged_events, initial_events):
            assert logged.event_id == expected.event_id
    else:
        assert len(logged_events) == 0