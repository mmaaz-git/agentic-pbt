import string
import uuid
from typing import Callable

import pytest
from hypothesis import assume, given, settings, strategies as st
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from sqlalchemy import event


def make_unique_function():
    """Create a unique function for testing."""
    unique_id = str(uuid.uuid4())
    
    def listener(*args, **kwargs):
        pass
    
    listener.__name__ = f'listener_{unique_id}'
    listener._unique_id = unique_id
    return listener


@given(st.integers(2, 10))
def test_duplicate_registration_behavior(num_duplicates):
    """Test what happens when the same function is registered multiple times."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    fn = make_unique_function()
    
    # Register the same function multiple times
    for _ in range(num_duplicates):
        event.listen(target, identifier, fn)
    
    # Check it's registered
    assert event.contains(target, identifier, fn), \
        f"Function not registered after {num_duplicates} listen() calls"
    
    # Now test removal behavior
    # According to the docs, remove() should revert ALL registrations
    # that proceeded from the listen() call
    
    # Remove once
    event.remove(target, identifier, fn)
    
    # Check if it's still registered
    # If SQLAlchemy allows duplicate registrations, it might still be there
    is_still_registered = event.contains(target, identifier, fn)
    
    if is_still_registered:
        # Try removing again multiple times to clean up
        for _ in range(num_duplicates - 1):
            try:
                event.remove(target, identifier, fn)
                if not event.contains(target, identifier, fn):
                    break
            except:
                break
    
    # Final check - should not be registered anymore
    # This tests whether remove() properly handles duplicate registrations
    final_registered = event.contains(target, identifier, fn)
    
    # The behavior should be consistent: duplicates are ignored,
    # so one remove() should remove the single registration
    assert not final_registered, \
        f"Function still registered after remove() despite {num_duplicates} duplicate listen() calls"


def test_duplicate_registration_specific():
    """Specific test for duplicate registration behavior."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    fn = make_unique_function()
    
    # Register the same function 3 times
    event.listen(target, identifier, fn)
    event.listen(target, identifier, fn)
    event.listen(target, identifier, fn)
    
    # Check it's registered
    assert event.contains(target, identifier, fn), \
        "Function not registered after multiple listen() calls"
    
    # Remove once
    event.remove(target, identifier, fn)
    
    # Check if it's still registered
    still_registered = event.contains(target, identifier, fn)
    print(f"After one remove: still_registered = {still_registered}")
    
    # If still registered, try to remove again
    if still_registered:
        event.remove(target, identifier, fn)
        still_registered_2 = event.contains(target, identifier, fn)
        print(f"After two removes: still_registered = {still_registered_2}")
        
        if still_registered_2:
            event.remove(target, identifier, fn)
            still_registered_3 = event.contains(target, identifier, fn)
            print(f"After three removes: still_registered = {still_registered_3}")


def test_listen_remove_asymmetry():
    """Test if there's asymmetry between listen() and remove() for duplicates."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    fn = make_unique_function()
    
    # Scenario 1: Multiple listens, one remove
    event.listen(target, identifier, fn)
    event.listen(target, identifier, fn)
    assert event.contains(target, identifier, fn)
    
    event.remove(target, identifier, fn)
    scenario1_result = event.contains(target, identifier, fn)
    
    # Clean up if needed
    while event.contains(target, identifier, fn):
        try:
            event.remove(target, identifier, fn)
        except:
            break
    
    # Scenario 2: One listen, multiple removes
    event.listen(target, identifier, fn)
    assert event.contains(target, identifier, fn)
    
    event.remove(target, identifier, fn)
    assert not event.contains(target, identifier, fn)
    
    # Try to remove again - should this raise an error?
    try:
        event.remove(target, identifier, fn)
        scenario2_raises = False
    except Exception as e:
        scenario2_raises = True
        scenario2_error = str(e)
    
    print(f"Scenario 1 (2 listens, 1 remove): still registered = {scenario1_result}")
    print(f"Scenario 2 (1 listen, 2 removes): raises exception = {scenario2_raises}")
    
    # This reveals the actual behavior of SQLAlchemy's event system
    # regarding duplicate registrations


def test_contains_with_unregistered_function():
    """Test contains() behavior with functions that were never registered."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    
    fn1 = make_unique_function()
    fn2 = make_unique_function()
    
    # Register only fn1
    event.listen(target, identifier, fn1)
    
    # Check contains for both
    assert event.contains(target, identifier, fn1), "Registered function not found"
    assert not event.contains(target, identifier, fn2), "Unregistered function reported as registered"
    
    # Clean up
    event.remove(target, identifier, fn1)


def test_remove_order_independence():
    """Test if removal order matters for multiple listeners."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    
    fn1 = make_unique_function()
    fn2 = make_unique_function()
    fn3 = make_unique_function()
    
    # Register in order: fn1, fn2, fn3
    event.listen(target, identifier, fn1)
    event.listen(target, identifier, fn2)
    event.listen(target, identifier, fn3)
    
    # Remove in different order: fn2, fn3, fn1
    event.remove(target, identifier, fn2)
    assert not event.contains(target, identifier, fn2)
    assert event.contains(target, identifier, fn1)
    assert event.contains(target, identifier, fn3)
    
    event.remove(target, identifier, fn3)
    assert not event.contains(target, identifier, fn3)
    assert event.contains(target, identifier, fn1)
    
    event.remove(target, identifier, fn1)
    assert not event.contains(target, identifier, fn1)
    
    # All should be gone
    assert not event.contains(target, identifier, fn1)
    assert not event.contains(target, identifier, fn2)
    assert not event.contains(target, identifier, fn3)


def test_insert_flag_with_duplicates():
    """Test insert flag behavior with duplicate registrations."""
    target = create_engine('sqlite:///:memory:')
    identifier = 'connect'
    fn = make_unique_function()
    
    # Register normally
    event.listen(target, identifier, fn)
    assert event.contains(target, identifier, fn)
    
    # Register same function with insert=True
    event.listen(target, identifier, fn, insert=True)
    assert event.contains(target, identifier, fn)
    
    # Remove once
    event.remove(target, identifier, fn)
    
    # Check if still registered (might be if duplicates are allowed)
    is_registered = event.contains(target, identifier, fn)
    
    # Clean up if needed
    if is_registered:
        event.remove(target, identifier, fn)
    
    print(f"After registering with and without insert, then one remove: {is_registered}")


if __name__ == "__main__":
    print("Testing duplicate registration behavior...")
    test_duplicate_registration_specific()
    print("\nTesting listen/remove asymmetry...")
    test_listen_remove_asymmetry()
    print("\nTesting insert flag with duplicates...")
    test_insert_flag_with_duplicates()