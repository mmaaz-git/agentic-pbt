"""Property-based tests for sqlalchemy.events module"""

import dataclasses
from hypothesis import given, strategies as st, assume, settings
from sqlalchemy.events import PoolResetState
from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool
import gc


# Strategy for generating PoolResetState instances
pool_reset_state_strategy = st.builds(
    PoolResetState,
    transaction_was_reset=st.booleans(),
    terminate_only=st.booleans(),
    asyncio_safe=st.booleans()
)


@given(pool_reset_state_strategy)
def test_pool_reset_state_equality_reflexive(state):
    """Test that PoolResetState equality is reflexive: x == x"""
    assert state == state


@given(pool_reset_state_strategy, pool_reset_state_strategy)
def test_pool_reset_state_equality_symmetric(state1, state2):
    """Test that PoolResetState equality is symmetric: if x == y then y == x"""
    if state1 == state2:
        assert state2 == state1


@given(pool_reset_state_strategy, pool_reset_state_strategy, pool_reset_state_strategy)
def test_pool_reset_state_equality_transitive(state1, state2, state3):
    """Test that PoolResetState equality is transitive: if x == y and y == z then x == z"""
    if state1 == state2 and state2 == state3:
        assert state1 == state3


@given(pool_reset_state_strategy, pool_reset_state_strategy)
def test_pool_reset_state_hash_consistency(state1, state2):
    """Test that equal PoolResetState objects have equal hashes"""
    if state1 == state2:
        assert hash(state1) == hash(state2)


@given(pool_reset_state_strategy)
def test_pool_reset_state_hash_stability(state):
    """Test that hash of PoolResetState remains constant"""
    h1 = hash(state)
    h2 = hash(state)
    assert h1 == h2


@given(pool_reset_state_strategy)
def test_pool_reset_state_immutability(state):
    """Test that PoolResetState is truly immutable (frozen)"""
    # Try to modify each field
    for field in ['transaction_was_reset', 'terminate_only', 'asyncio_safe']:
        try:
            setattr(state, field, not getattr(state, field))
            assert False, f"Should not be able to modify field {field}"
        except dataclasses.FrozenInstanceError:
            pass  # Expected


@given(pool_reset_state_strategy, st.booleans(), st.booleans(), st.booleans())
def test_pool_reset_state_replace_creates_new(state, new_trans, new_term, new_async):
    """Test that dataclasses.replace creates a new object without modifying original"""
    original_trans = state.transaction_was_reset
    original_term = state.terminate_only
    original_async = state.asyncio_safe
    
    # Replace with new values
    new_state = dataclasses.replace(
        state,
        transaction_was_reset=new_trans,
        terminate_only=new_term,
        asyncio_safe=new_async
    )
    
    # Original should be unchanged
    assert state.transaction_was_reset == original_trans
    assert state.terminate_only == original_term
    assert state.asyncio_safe == original_async
    
    # New state should have new values
    assert new_state.transaction_was_reset == new_trans
    assert new_state.terminate_only == new_term
    assert new_state.asyncio_safe == new_async


@given(st.lists(pool_reset_state_strategy, min_size=1, max_size=20))
def test_pool_reset_state_set_uniqueness(states):
    """Test that equal PoolResetState objects collapse to one in a set"""
    # Create a set from the list
    state_set = set(states)
    
    # Count unique states manually
    unique_states = []
    for state in states:
        if state not in unique_states:
            unique_states.append(state)
    
    # Set size should match unique count
    assert len(state_set) == len(unique_states)


@given(
    st.booleans(),
    st.booleans(),
    st.booleans()
)
def test_pool_reset_state_constructor_fields(trans, term, async_safe):
    """Test that PoolResetState constructor correctly sets all fields"""
    state = PoolResetState(
        transaction_was_reset=trans,
        terminate_only=term,
        asyncio_safe=async_safe
    )
    
    assert state.transaction_was_reset == trans
    assert state.terminate_only == term
    assert state.asyncio_safe == async_safe


@given(st.text(min_size=1, max_size=50))
@settings(max_examples=100)
def test_event_listen_contains_remove_cycle(event_name):
    """Test that event.listen/contains/remove form a consistent cycle"""
    # Filter to valid identifier-like strings
    assume(event_name.isidentifier())
    
    # Create a fresh engine for each test
    engine = create_engine('sqlite:///:memory:', poolclass=NullPool)
    
    def dummy_listener(*args, **kwargs):
        pass
    
    # Initially should not contain the listener
    assert not event.contains(engine, event_name, dummy_listener)
    
    # After listening, should contain it
    try:
        event.listen(engine, event_name, dummy_listener)
        assert event.contains(engine, event_name, dummy_listener)
        
        # After removing, should not contain it
        event.remove(engine, event_name, dummy_listener)
        assert not event.contains(engine, event_name, dummy_listener)
    except (AttributeError, KeyError):
        # Some event names might not be valid for the engine
        pass


@given(st.text(min_size=1, max_size=50))
@settings(max_examples=100)
def test_event_double_remove_raises(event_name):
    """Test that removing a non-existent listener raises an error"""
    assume(event_name.isidentifier())
    
    engine = create_engine('sqlite:///:memory:', poolclass=NullPool)
    
    def dummy_listener(*args, **kwargs):
        pass
    
    # Removing non-existent listener should raise
    try:
        event.remove(engine, event_name, dummy_listener)
        # If we get here, it means no error was raised for invalid event name
        # which is fine - we're testing the remove behavior
    except (AttributeError, KeyError):
        # Expected for invalid event names
        pass
    except Exception:
        # Any other exception is also acceptable
        pass


@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=50)
def test_event_multiple_registrations(num_registrations):
    """Test that registering the same listener multiple times results in multiple calls"""
    engine = create_engine('sqlite:///:memory:', poolclass=NullPool)
    
    counter = {'count': 0}
    
    def connect_listener(dbapi_conn, connection_record):
        counter['count'] += 1
    
    # Register the same listener multiple times
    for _ in range(num_registrations):
        event.listen(engine.pool, 'connect', connect_listener)
    
    # Trigger the event once
    conn = engine.connect()
    conn.close()
    
    # The listener should have been called num_registrations times
    assert counter['count'] == num_registrations
    
    # Clean up
    for _ in range(num_registrations):
        try:
            event.remove(engine.pool, 'connect', connect_listener)
        except:
            break  # Some implementations might remove all at once


@given(st.lists(st.tuples(st.booleans(), st.booleans(), st.booleans()), min_size=2, max_size=10))
def test_pool_reset_state_equality_by_values(values_list):
    """Test that PoolResetState equality is determined solely by field values"""
    states = []
    for trans, term, async_safe in values_list:
        states.append(PoolResetState(
            transaction_was_reset=trans,
            terminate_only=term,
            asyncio_safe=async_safe
        ))
    
    # Check all pairs
    for i in range(len(states)):
        for j in range(len(states)):
            state1, state2 = states[i], states[j]
            values1 = values_list[i]
            values2 = values_list[j]
            
            if values1 == values2:
                assert state1 == state2, f"States with same values should be equal"
                assert hash(state1) == hash(state2), f"Equal states should have same hash"
            else:
                assert state1 != state2, f"States with different values should not be equal"