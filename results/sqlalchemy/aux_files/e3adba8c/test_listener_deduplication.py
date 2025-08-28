"""Test to demonstrate listener deduplication behavior in SQLAlchemy events"""

from sqlalchemy import create_engine, event
from sqlalchemy.pool import NullPool


def test_listener_deduplication_behavior():
    """
    This test demonstrates that SQLAlchemy silently deduplicates
    identical listener functions when registered multiple times.
    """
    
    engine = create_engine('sqlite:///:memory:', poolclass=NullPool)
    
    call_count = {'count': 0}
    
    def my_listener(dbapi_conn, connection_record):
        call_count['count'] += 1
    
    # Register the same listener 5 times
    for i in range(5):
        event.listen(engine.pool, 'connect', my_listener)
        print(f"Registration {i+1}: contains = {event.contains(engine.pool, 'connect', my_listener)}")
    
    # Trigger the event once
    conn = engine.connect()
    conn.close()
    
    print(f"\nListener registered 5 times, but called only {call_count['count']} time(s)")
    print(f"Expected if each registration was separate: 5")
    print(f"Actual: {call_count['count']}")
    
    # Try to remove the listener
    remove_count = 0
    while True:
        try:
            event.remove(engine.pool, 'connect', my_listener)
            remove_count += 1
            print(f"Successfully removed listener (removal #{remove_count})")
        except Exception as e:
            print(f"Cannot remove anymore after {remove_count} removal(s): {type(e).__name__}")
            break
    
    print(f"\nConclusion: Despite 5 registrations, only 1 removal was needed")
    return call_count['count'] == 1 and remove_count == 1


def test_listener_with_different_args():
    """Test if listeners with different registration args are deduplicated"""
    
    engine = create_engine('sqlite:///:memory:', poolclass=NullPool)
    
    call_count = {'count': 0}
    
    def my_listener(dbapi_conn, connection_record):
        call_count['count'] += 1
    
    # Register with different named args
    event.listen(engine.pool, 'connect', my_listener, once=False)
    event.listen(engine.pool, 'connect', my_listener, once=False, insert=False)
    event.listen(engine.pool, 'connect', my_listener, insert=True)
    
    # Trigger the event
    conn = engine.connect()
    conn.close()
    
    print(f"\nListener registered 3 times with different args")
    print(f"Call count: {call_count['count']}")
    
    # This could be 1 (full dedup) or 2 (insert=True might create separate registration)
    return call_count['count']


if __name__ == "__main__":
    print("=== Test 1: Basic Deduplication ===")
    result1 = test_listener_deduplication_behavior()
    
    print("\n=== Test 2: Deduplication with Different Args ===")
    result2 = test_listener_with_different_args()
    
    print("\n=== Summary ===")
    print(f"Deduplication confirmed: {result1}")
    print(f"Args affect deduplication: {result2 > 1}")