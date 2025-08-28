"""
Test for the documented limitation: "an event cannot be removed from inside 
the listener function for itself"
"""

from sqlalchemy import create_engine, event


def test_self_removal_during_execution():
    """Test that a listener cannot remove itself during execution."""
    
    # Create an engine with a real database to trigger events
    engine = create_engine('sqlite:///:memory:')
    removal_attempted = []
    error_caught = []
    
    def self_removing_listener(dbapi_conn, connection_record):
        """A listener that tries to remove itself when called."""
        removal_attempted.append(True)
        try:
            # Try to remove ourselves while we're executing
            event.remove(engine, 'connect', self_removing_listener)
        except Exception as e:
            error_caught.append(e)
    
    # Register the self-removing listener
    event.listen(engine, 'connect', self_removing_listener)
    assert event.contains(engine, 'connect', self_removing_listener)
    
    # Trigger the connect event by creating a connection
    try:
        with engine.connect() as conn:
            pass
    except Exception as e:
        print(f"Connection failed: {e}")
    
    # Check what happened
    print(f"Removal attempted: {bool(removal_attempted)}")
    print(f"Error caught during self-removal: {bool(error_caught)}")
    if error_caught:
        print(f"Error type: {type(error_caught[0]).__name__}")
        print(f"Error message: {error_caught[0]}")
    
    # Check if the listener is still registered
    still_registered = event.contains(engine, 'connect', self_removing_listener)
    print(f"Listener still registered after self-removal attempt: {still_registered}")
    
    # Clean up if needed
    if still_registered:
        event.remove(engine, 'connect', self_removing_listener)
    
    # This reveals whether SQLAlchemy properly prevents self-removal
    # as documented


def test_cross_removal_during_execution():
    """Test if one listener can remove another during execution."""
    
    engine = create_engine('sqlite:///:memory:')
    execution_order = []
    
    def listener_2(dbapi_conn, connection_record):
        """Second listener that gets removed by the first."""
        execution_order.append('listener_2')
    
    def listener_1(dbapi_conn, connection_record):
        """First listener that removes the second."""
        execution_order.append('listener_1')
        try:
            # Try to remove listener_2 while events are being processed
            event.remove(engine, 'connect', listener_2)
            execution_order.append('removal_succeeded')
        except Exception as e:
            execution_order.append(f'removal_failed: {e}')
    
    def listener_3(dbapi_conn, connection_record):
        """Third listener to see if execution continues."""
        execution_order.append('listener_3')
    
    # Register listeners
    event.listen(engine, 'connect', listener_1)
    event.listen(engine, 'connect', listener_2)
    event.listen(engine, 'connect', listener_3)
    
    # Trigger the event
    try:
        with engine.connect() as conn:
            pass
    except Exception as e:
        print(f"Connection failed: {e}")
    
    print(f"Execution order: {execution_order}")
    
    # Check final registration state
    print(f"listener_1 registered: {event.contains(engine, 'connect', listener_1)}")
    print(f"listener_2 registered: {event.contains(engine, 'connect', listener_2)}")
    print(f"listener_3 registered: {event.contains(engine, 'connect', listener_3)}")
    
    # Clean up
    for listener in [listener_1, listener_2, listener_3]:
        if event.contains(engine, 'connect', listener):
            event.remove(engine, 'connect', listener)


def test_recursive_event_registration():
    """Test if a listener can register new listeners during execution."""
    
    engine = create_engine('sqlite:///:memory:')
    registered_during_execution = []
    
    def recursive_listener(dbapi_conn, connection_record):
        """A listener that registers another listener when called."""
        if not registered_during_execution:
            def new_listener(dbapi_conn, connection_record):
                pass
            
            # Try to register a new listener during event execution
            try:
                event.listen(engine, 'connect', new_listener)
                registered_during_execution.append(new_listener)
                print("Successfully registered new listener during execution")
            except Exception as e:
                print(f"Failed to register during execution: {e}")
    
    # Register the recursive listener
    event.listen(engine, 'connect', recursive_listener)
    
    # Trigger the event
    with engine.connect() as conn:
        pass
    
    # Check if the new listener was registered
    if registered_during_execution:
        new_listener = registered_during_execution[0]
        is_registered = event.contains(engine, 'connect', new_listener)
        print(f"New listener registered: {is_registered}")
        
        # Clean up
        if is_registered:
            event.remove(engine, 'connect', new_listener)
    
    # Clean up original listener
    event.remove(engine, 'connect', recursive_listener)


if __name__ == "__main__":
    print("=== Testing self-removal during execution ===")
    test_self_removal_during_execution()
    print("\n=== Testing cross-removal during execution ===")
    test_cross_removal_during_execution()
    print("\n=== Testing recursive registration ===")
    test_recursive_event_registration()