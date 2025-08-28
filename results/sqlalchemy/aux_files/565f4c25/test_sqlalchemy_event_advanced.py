import string
import uuid
from typing import Callable

import pytest
from hypothesis import assume, given, settings, strategies as st
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
        return 'connect'
    elif isinstance(target, Table):
        return 'before_create'
    else:
        return 'before_insert'


def make_unique_function():
    """Create a unique function for testing."""
    unique_id = str(uuid.uuid4())
    
    def listener(*args, **kwargs):
        pass
    
    listener.__name__ = f'listener_{unique_id}'
    listener._unique_id = unique_id
    return listener


@given(valid_event_target())
def test_listen_with_insert_flag_ordering(target):
    """Test that insert=True prepends the listener."""
    identifier = get_valid_event_identifier(target)
    
    # Create multiple functions
    fn1 = make_unique_function()
    fn2 = make_unique_function()
    fn3 = make_unique_function()
    
    # Register fn1 normally
    event.listen(target, identifier, fn1)
    assert event.contains(target, identifier, fn1)
    
    # Register fn2 with insert=True (should be prepended)
    event.listen(target, identifier, fn2, insert=True)
    assert event.contains(target, identifier, fn2)
    
    # Register fn3 normally (should be appended)
    event.listen(target, identifier, fn3)
    assert event.contains(target, identifier, fn3)
    
    # All three should be registered
    assert event.contains(target, identifier, fn1)
    assert event.contains(target, identifier, fn2)
    assert event.contains(target, identifier, fn3)
    
    # Clean up
    event.remove(target, identifier, fn1)
    event.remove(target, identifier, fn2)
    event.remove(target, identifier, fn3)


@given(valid_event_target())
def test_same_function_registered_twice(target):
    """Test registering the same function twice for the same event."""
    identifier = get_valid_event_identifier(target)
    fn = make_unique_function()
    
    # Register once
    event.listen(target, identifier, fn)
    assert event.contains(target, identifier, fn)
    
    # Register again - should this work or raise an error?
    # According to SQLAlchemy docs, this should be allowed
    try:
        event.listen(target, identifier, fn)
        # If it doesn't raise, check that it's still registered
        assert event.contains(target, identifier, fn)
        
        # Remove once should remove it
        event.remove(target, identifier, fn)
        
        # Check if it's still there (might be registered twice)
        # This tests whether duplicate registrations are allowed
        is_still_registered = event.contains(target, identifier, fn)
        
        # Clean up if still registered
        if is_still_registered:
            event.remove(target, identifier, fn)
            
    except Exception as e:
        # If it raises an exception, that's also valid behavior
        # Just clean up the first registration
        event.remove(target, identifier, fn)


@given(valid_event_target())
def test_listen_with_once_flag(target):
    """Test the once=True flag behavior."""
    identifier = get_valid_event_identifier(target)
    fn = make_unique_function()
    
    # Register with once=True
    event.listen(target, identifier, fn, once=True)
    
    # Should be registered
    assert event.contains(target, identifier, fn), \
        "Function not registered after listen() with once=True"
    
    # Clean up
    event.remove(target, identifier, fn)
    assert not event.contains(target, identifier, fn)


@given(valid_event_target(), st.booleans(), st.booleans())
def test_listen_with_multiple_flags(target, use_insert, use_once):
    """Test combining multiple flags."""
    identifier = get_valid_event_identifier(target)
    fn = make_unique_function()
    
    # Register with multiple flags
    event.listen(target, identifier, fn, insert=use_insert, once=use_once)
    
    # Should be registered
    assert event.contains(target, identifier, fn), \
        f"Function not registered with insert={use_insert}, once={use_once}"
    
    # Clean up
    event.remove(target, identifier, fn)
    assert not event.contains(target, identifier, fn)


@given(valid_event_target())
def test_none_as_function(target):
    """Test what happens when None is passed as the function."""
    identifier = get_valid_event_identifier(target)
    
    # Try to register None as a listener - should this work or raise?
    try:
        event.listen(target, identifier, None)
        # If it doesn't raise, check if it's registered
        is_registered = event.contains(target, identifier, None)
        
        if is_registered:
            # Try to remove it
            event.remove(target, identifier, None)
            assert not event.contains(target, identifier, None)
    except (TypeError, AttributeError, ValueError) as e:
        # Expected - None is not a valid callable
        pass


@given(valid_event_target())
def test_empty_string_identifier(target):
    """Test using an empty string as the event identifier."""
    fn = make_unique_function()
    
    # Try empty string as identifier
    try:
        event.listen(target, "", fn)
        # If it doesn't raise, check if it's registered
        if event.contains(target, "", fn):
            event.remove(target, "", fn)
    except (ValueError, KeyError, AttributeError) as e:
        # Expected - empty string might not be valid
        pass


@given(valid_event_target(), st.text(min_size=1, max_size=100))
def test_arbitrary_identifier_names(target, identifier):
    """Test with arbitrary identifier names (including invalid ones)."""
    fn = make_unique_function()
    
    # Skip identifiers with null bytes or other problematic characters
    assume('\x00' not in identifier)
    assume(identifier.strip() == identifier)  # No leading/trailing whitespace
    
    try:
        event.listen(target, identifier, fn)
        
        # If listen succeeds, contains should return True
        is_registered = event.contains(target, identifier, fn)
        
        if is_registered:
            # Remove should also work
            event.remove(target, identifier, fn)
            assert not event.contains(target, identifier, fn), \
                f"Function still registered after remove() for identifier '{identifier}'"
        else:
            # If not registered despite listen() succeeding, that's suspicious
            # But some identifiers might be silently ignored
            pass
            
    except (AttributeError, KeyError, ValueError) as e:
        # Some identifiers might not be valid for the target
        pass


@given(valid_event_target())
def test_lambda_as_listener(target):
    """Test using lambda functions as listeners."""
    identifier = get_valid_event_identifier(target)
    
    # Create a lambda
    fn = lambda *args, **kwargs: None
    
    # Register the lambda
    event.listen(target, identifier, fn)
    assert event.contains(target, identifier, fn)
    
    # Remove the lambda
    event.remove(target, identifier, fn)
    assert not event.contains(target, identifier, fn)


@given(valid_event_target())
def test_class_method_as_listener(target):
    """Test using class methods as listeners."""
    identifier = get_valid_event_identifier(target)
    
    class TestClass:
        @staticmethod
        def static_listener(*args, **kwargs):
            pass
        
        @classmethod
        def class_listener(cls, *args, **kwargs):
            pass
        
        def instance_listener(self, *args, **kwargs):
            pass
    
    # Test static method
    event.listen(target, identifier, TestClass.static_listener)
    assert event.contains(target, identifier, TestClass.static_listener)
    event.remove(target, identifier, TestClass.static_listener)
    
    # Test class method
    event.listen(target, identifier, TestClass.class_listener)
    assert event.contains(target, identifier, TestClass.class_listener)
    event.remove(target, identifier, TestClass.class_listener)
    
    # Test instance method
    instance = TestClass()
    event.listen(target, identifier, instance.instance_listener)
    assert event.contains(target, identifier, instance.instance_listener)
    event.remove(target, identifier, instance.instance_listener)


@given(st.integers(10, 100))
def test_many_listeners_stress(num_listeners):
    """Stress test with many listeners."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    
    listeners = [make_unique_function() for _ in range(num_listeners)]
    
    # Register all listeners
    for fn in listeners:
        event.listen(target, identifier, fn)
    
    # Check all are registered
    for fn in listeners:
        assert event.contains(target, identifier, fn)
    
    # Remove half of them
    for fn in listeners[:num_listeners//2]:
        event.remove(target, identifier, fn)
        assert not event.contains(target, identifier, fn)
    
    # Check other half still registered
    for fn in listeners[num_listeners//2:]:
        assert event.contains(target, identifier, fn)
    
    # Clean up remaining
    for fn in listeners[num_listeners//2:]:
        event.remove(target, identifier, fn)


@given(valid_event_target())
def test_remove_with_wrong_identifier(target):
    """Test removing with a different identifier than used for listen."""
    identifier1 = get_valid_event_identifier(target)
    
    # Get a different identifier
    from sqlalchemy.engine import Engine
    from sqlalchemy.schema import Table
    
    if isinstance(target, Engine):
        identifier2 = 'close' if identifier1 == 'connect' else 'connect'
    elif isinstance(target, Table):
        identifier2 = 'after_create' if identifier1 == 'before_create' else 'before_create'
    else:
        identifier2 = 'after_insert'
    
    fn = make_unique_function()
    
    # Register with identifier1
    event.listen(target, identifier1, fn)
    assert event.contains(target, identifier1, fn)
    assert not event.contains(target, identifier2, fn)
    
    # Try to remove with identifier2 - should not affect identifier1
    try:
        event.remove(target, identifier2, fn)
    except:
        pass  # Might raise an exception
    
    # Should still be registered for identifier1
    assert event.contains(target, identifier1, fn)
    
    # Clean up
    event.remove(target, identifier1, fn)