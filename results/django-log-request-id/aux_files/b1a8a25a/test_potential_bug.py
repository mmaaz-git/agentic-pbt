import logging
import sys
import os

# Add the site-packages directory to Python path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')

# Setup Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'

from hypothesis import given, strategies as st
from log_request_id import local, DEFAULT_NO_REQUEST_ID
from log_request_id.filters import RequestIDFilter


# Test what happens when local object behaves unusually
def test_local_object_unusual_behavior():
    """Test behavior when the local object has unusual characteristics."""
    
    # Save original local
    from log_request_id import filters
    original_local = filters.local
    
    # Test 1: Create a class where accessing 'request_id' raises exception
    class WeirdLocal:
        def __getattr__(self, name):
            if name == 'request_id':
                raise RuntimeError("Cannot access request_id")
            raise AttributeError(f"No attribute {name}")
    
    filters.local = WeirdLocal()
    
    filter_obj = RequestIDFilter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test",
        args=(),
        exc_info=None
    )
    
    # This should handle the exception
    try:
        result = filter_obj.filter(record)
        print(f"Filter returned: {result}")
        print(f"Record request_id: {record.request_id}")
        # If we get here, it handled the exception
        assert False, "Expected RuntimeError but filter handled it somehow"
    except RuntimeError as e:
        print(f"BUG FOUND: Filter doesn't handle exceptions from local.__getattr__: {e}")
        # Restore original local
        filters.local = original_local
        return True
    
    # Restore original local
    filters.local = original_local
    return False


# Test with local that has a property that raises exception
def test_local_property_exception():
    """Test when local.request_id is a property that raises exception."""
    
    from log_request_id import filters
    original_local = filters.local
    
    class LocalWithBadProperty:
        @property
        def request_id(self):
            raise ValueError("Property access failed")
    
    filters.local = LocalWithBadProperty()
    
    filter_obj = RequestIDFilter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test",
        args=(),
        exc_info=None
    )
    
    try:
        result = filter_obj.filter(record)
        print(f"Filter returned: {result}")
        print(f"Record request_id: {record.request_id}")
        assert False, "Expected ValueError but filter handled it"
    except ValueError as e:
        print(f"BUG FOUND: Filter doesn't handle property exceptions: {e}")
        filters.local = original_local
        return True
    
    filters.local = original_local
    return False


# Test extreme recursion in getattr
def test_recursive_getattr():
    """Test when accessing request_id causes recursion."""
    
    from log_request_id import filters
    original_local = filters.local
    
    class RecursiveLocal:
        def __getattr__(self, name):
            if name == 'request_id':
                # This causes infinite recursion
                return self.request_id
            raise AttributeError(f"No attribute {name}")
    
    filters.local = RecursiveLocal()
    
    filter_obj = RequestIDFilter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test",
        args=(),
        exc_info=None
    )
    
    try:
        result = filter_obj.filter(record)
        print(f"Filter returned: {result}")
        print(f"Record request_id: {record.request_id}")
        assert False, "Expected RecursionError but filter handled it"
    except RecursionError as e:
        print(f"BUG FOUND: Filter doesn't handle recursive getattr: {e}")
        filters.local = original_local
        return True
    
    filters.local = original_local
    return False


if __name__ == "__main__":
    print("Testing potential bugs in RequestIDFilter...")
    print("-" * 50)
    
    print("\n1. Testing weird local object behavior:")
    bug1 = test_local_object_unusual_behavior()
    
    print("\n2. Testing local property exception:")
    bug2 = test_local_property_exception()
    
    print("\n3. Testing recursive getattr:")
    bug3 = test_recursive_getattr()
    
    print("\n" + "=" * 50)
    if bug1 or bug2 or bug3:
        print("BUGS FOUND! See details above.")
    else:
        print("No bugs found in these edge cases.")