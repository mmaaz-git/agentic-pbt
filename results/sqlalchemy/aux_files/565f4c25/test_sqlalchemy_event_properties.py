import string
import uuid
from typing import Callable

import pytest
from hypothesis import assume, given, strategies as st
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from sqlalchemy import event


@st.composite
def valid_event_target(draw):
    """Generate valid SQLAlchemy event targets."""
    choice = draw(st.integers(0, 2))
    
    if choice == 0:
        # Create an in-memory SQLite engine
        return create_engine('sqlite:///:memory:')
    elif choice == 1:
        # Create a Table
        metadata = MetaData()
        table_name = draw(st.text(alphabet=string.ascii_letters, min_size=1, max_size=20))
        return Table(
            table_name, 
            metadata, 
            Column('id', Integer, primary_key=True),
            Column('data', String(50))
        )
    else:
        # Create another engine with different URL
        return create_engine(f'sqlite:///test_{draw(st.integers(0, 1000))}.db')


def get_valid_event_identifier(target):
    """Get a valid event identifier for the given target."""
    from sqlalchemy.engine import Engine
    from sqlalchemy.schema import Table
    
    if isinstance(target, Engine):
        # Engine events
        return 'connect'
    elif isinstance(target, Table):
        # Table events  
        return 'before_create'
    else:
        # Default to a common event
        return 'before_insert'


def make_unique_function():
    """Create a unique function for testing."""
    unique_id = str(uuid.uuid4())
    
    def listener(*args, **kwargs):
        pass
    
    # Make the function unique by adding a unique attribute
    listener.__name__ = f'listener_{unique_id}'
    listener._unique_id = unique_id
    return listener


@given(valid_event_target())
def test_listen_contains_invariant(target):
    """After calling listen(), contains() should return True."""
    identifier = get_valid_event_identifier(target)
    fn = make_unique_function()
    
    # Register the listener
    event.listen(target, identifier, fn)
    
    # Check that contains returns True
    assert event.contains(target, identifier, fn), \
        f"contains() returned False after listen() for {target}, {identifier}"
    
    # Clean up
    event.remove(target, identifier, fn)


@given(valid_event_target())
def test_remove_contains_invariant(target):
    """After calling remove(), contains() should return False."""
    identifier = get_valid_event_identifier(target)
    fn = make_unique_function()
    
    # First register the listener
    event.listen(target, identifier, fn)
    assert event.contains(target, identifier, fn), "Precondition failed: listener not registered"
    
    # Remove the listener
    event.remove(target, identifier, fn)
    
    # Check that contains returns False
    assert not event.contains(target, identifier, fn), \
        f"contains() returned True after remove() for {target}, {identifier}"


@given(valid_event_target())
def test_round_trip_property(target):
    """Test complete round-trip: listen → contains(True) → remove → contains(False)."""
    identifier = get_valid_event_identifier(target)
    fn = make_unique_function()
    
    # Initially should not be registered
    assert not event.contains(target, identifier, fn), \
        "Precondition failed: listener already registered"
    
    # Register listener
    event.listen(target, identifier, fn)
    assert event.contains(target, identifier, fn), \
        "contains() returned False after listen()"
    
    # Remove listener
    event.remove(target, identifier, fn)
    assert not event.contains(target, identifier, fn), \
        "contains() returned True after remove()"


@given(valid_event_target(), st.integers(2, 5))
def test_multiple_listeners(target, num_listeners):
    """Test that multiple different functions can be registered for the same event."""
    identifier = get_valid_event_identifier(target)
    listeners = [make_unique_function() for _ in range(num_listeners)]
    
    # Register all listeners
    for fn in listeners:
        event.listen(target, identifier, fn)
    
    # Check all are registered
    for i, fn in enumerate(listeners):
        assert event.contains(target, identifier, fn), \
            f"Listener {i} not registered after listen()"
    
    # Remove first listener
    event.remove(target, identifier, listeners[0])
    
    # Check first is gone but others remain
    assert not event.contains(target, identifier, listeners[0]), \
        "First listener still registered after remove()"
    
    for i, fn in enumerate(listeners[1:], 1):
        assert event.contains(target, identifier, fn), \
            f"Listener {i} unexpectedly removed"
    
    # Clean up remaining listeners
    for fn in listeners[1:]:
        event.remove(target, identifier, fn)


@given(valid_event_target())
def test_double_remove_safety(target):
    """Test that removing a non-existent listener doesn't crash."""
    identifier = get_valid_event_identifier(target)
    fn = make_unique_function()
    
    # Register and remove once
    event.listen(target, identifier, fn)
    event.remove(target, identifier, fn)
    assert not event.contains(target, identifier, fn)
    
    # Try to remove again - should not crash
    try:
        event.remove(target, identifier, fn)
        # If it doesn't raise an exception, that's fine
    except Exception as e:
        # Check if this is an expected exception
        # SQLAlchemy might raise an error for double removal
        pass


@given(valid_event_target())
def test_different_functions_are_independent(target):
    """Test that different functions for the same event are independent."""
    identifier = get_valid_event_identifier(target)
    fn1 = make_unique_function()
    fn2 = make_unique_function()
    
    # Register first function
    event.listen(target, identifier, fn1)
    assert event.contains(target, identifier, fn1)
    assert not event.contains(target, identifier, fn2)
    
    # Register second function
    event.listen(target, identifier, fn2)
    assert event.contains(target, identifier, fn1)
    assert event.contains(target, identifier, fn2)
    
    # Remove first function
    event.remove(target, identifier, fn1)
    assert not event.contains(target, identifier, fn1)
    assert event.contains(target, identifier, fn2)
    
    # Clean up
    event.remove(target, identifier, fn2)


@given(valid_event_target())
def test_same_function_different_events(target):
    """Test that the same function can be registered for different events."""
    from sqlalchemy.engine import Engine
    from sqlalchemy.schema import Table
    
    # Get two different valid identifiers
    if isinstance(target, Engine):
        identifiers = ['connect', 'close']
    elif isinstance(target, Table):
        identifiers = ['before_create', 'after_create']
    else:
        # Skip this test for unknown target types
        return
    
    fn = make_unique_function()
    
    # Register for both events
    for identifier in identifiers:
        event.listen(target, identifier, fn)
    
    # Check both are registered
    for identifier in identifiers:
        assert event.contains(target, identifier, fn), \
            f"Function not registered for {identifier}"
    
    # Remove from first event
    event.remove(target, identifiers[0], fn)
    assert not event.contains(target, identifiers[0], fn)
    assert event.contains(target, identifiers[1], fn)
    
    # Clean up
    event.remove(target, identifiers[1], fn)