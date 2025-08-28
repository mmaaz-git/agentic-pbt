"""
Minimal reproduction of the bug: modifying event listeners during event execution
causes RuntimeError: deque mutated during iteration
"""

from sqlalchemy import create_engine, event


def test_self_removal_bug():
    """Minimal reproduction: listener removing itself causes RuntimeError."""
    
    engine = create_engine('sqlite:///:memory:')
    
    def self_removing_listener(dbapi_conn, connection_record):
        # This causes RuntimeError: deque mutated during iteration
        event.remove(engine, 'connect', self_removing_listener)
    
    event.listen(engine, 'connect', self_removing_listener)
    
    # This will raise RuntimeError
    with engine.connect() as conn:
        pass


def test_cross_removal_bug():
    """Minimal reproduction: one listener removing another causes RuntimeError."""
    
    engine = create_engine('sqlite:///:memory:')
    
    def victim_listener(dbapi_conn, connection_record):
        pass
    
    def removing_listener(dbapi_conn, connection_record):
        # This causes RuntimeError: deque mutated during iteration
        event.remove(engine, 'connect', victim_listener)
    
    event.listen(engine, 'connect', removing_listener)
    event.listen(engine, 'connect', victim_listener)
    
    # This will raise RuntimeError
    with engine.connect() as conn:
        pass


def test_registration_during_execution_bug():
    """Minimal reproduction: registering new listener during execution causes RuntimeError."""
    
    engine = create_engine('sqlite:///:memory:')
    
    def registering_listener(dbapi_conn, connection_record):
        def new_listener(dbapi_conn, connection_record):
            pass
        # This causes RuntimeError: deque mutated during iteration
        event.listen(engine, 'connect', new_listener)
    
    event.listen(engine, 'connect', registering_listener)
    
    # This will raise RuntimeError
    with engine.connect() as conn:
        pass


if __name__ == "__main__":
    print("Testing self-removal bug...")
    try:
        test_self_removal_bug()
        print("No error - unexpected!")
    except RuntimeError as e:
        print(f"RuntimeError: {e}")
    
    print("\nTesting cross-removal bug...")
    try:
        test_cross_removal_bug()
        print("No error - unexpected!")
    except RuntimeError as e:
        print(f"RuntimeError: {e}")
    
    print("\nTesting registration during execution bug...")
    try:
        test_registration_during_execution_bug()
        print("No error - unexpected!")
    except RuntimeError as e:
        print(f"RuntimeError: {e}")