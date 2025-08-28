import logging
import sys
import os
import traceback

# Add the site-packages directory to Python path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')

# Setup Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'

from log_request_id import DEFAULT_NO_REQUEST_ID
from log_request_id.filters import RequestIDFilter


def test_bug_exception_handling():
    """Confirm that RequestIDFilter doesn't handle exceptions from local object access."""
    
    from log_request_id import filters
    original_local = filters.local
    
    # Create a local object that raises exceptions
    class BrokenLocal:
        def __getattr__(self, name):
            if name == 'request_id':
                raise RuntimeError("Database connection lost")
            raise AttributeError(f"No attribute {name}")
    
    filters.local = BrokenLocal()
    
    filter_obj = RequestIDFilter()
    record = logging.LogRecord(
        name="app.views",
        level=logging.INFO,
        pathname="/app/views.py",
        lineno=42,
        msg="Processing user request",
        args=(),
        exc_info=None
    )
    
    try:
        # This will crash
        filter_obj.filter(record)
        filters.local = original_local
        return False, None
    except RuntimeError as e:
        error_info = {
            'exception_type': type(e).__name__,
            'exception_msg': str(e),
            'traceback': traceback.format_exc()
        }
        filters.local = original_local
        return True, error_info


def test_bug_property_exception():
    """Confirm that RequestIDFilter crashes when local.request_id property raises."""
    
    from log_request_id import filters
    original_local = filters.local
    
    class LocalWithFailingProperty:
        @property
        def request_id(self):
            # Simulate a scenario where accessing the property fails
            # This could happen if request_id computation involves external resources
            raise ValueError("Failed to compute request ID from session")
    
    filters.local = LocalWithFailingProperty()
    
    filter_obj = RequestIDFilter()
    record = logging.LogRecord(
        name="django.request",
        level=logging.ERROR,
        pathname="/django/core/handlers/base.py",
        lineno=123,
        msg="Internal Server Error",
        args=(),
        exc_info=None
    )
    
    try:
        filter_obj.filter(record)
        filters.local = original_local
        return False, None
    except ValueError as e:
        error_info = {
            'exception_type': type(e).__name__,
            'exception_msg': str(e),
            'traceback': traceback.format_exc()
        }
        filters.local = original_local
        return True, error_info


def reproduce_minimal():
    """Minimal reproduction of the bug."""
    from log_request_id import filters
    
    # Save original
    original_local = filters.local
    
    # Replace with problematic local
    class ProblematicLocal:
        @property
        def request_id(self):
            raise RuntimeError("Simulated failure")
    
    filters.local = ProblematicLocal()
    
    # Create filter and record
    filter_obj = RequestIDFilter()
    record = logging.LogRecord(
        name="test", level=20, pathname="test.py", 
        lineno=1, msg="test", args=(), exc_info=None
    )
    
    # This will raise RuntimeError
    filter_obj.filter(record)
    
    # Restore
    filters.local = original_local


if __name__ == "__main__":
    print("Confirming bugs in RequestIDFilter\n")
    print("=" * 60)
    
    print("\nBug 1: Exception from __getattr__")
    print("-" * 40)
    bug1_found, bug1_info = test_bug_exception_handling()
    if bug1_found:
        print(f"✓ CONFIRMED: {bug1_info['exception_type']}: {bug1_info['exception_msg']}")
    else:
        print("✗ Bug not reproduced")
    
    print("\nBug 2: Exception from property")
    print("-" * 40)
    bug2_found, bug2_info = test_bug_property_exception()
    if bug2_found:
        print(f"✓ CONFIRMED: {bug2_info['exception_type']}: {bug2_info['exception_msg']}")
    else:
        print("✗ Bug not reproduced")
    
    print("\n" + "=" * 60)
    print("\nMinimal Reproduction:")
    print("-" * 40)
    print("""
from log_request_id.filters import RequestIDFilter
from log_request_id import filters
import logging

class ProblematicLocal:
    @property
    def request_id(self):
        raise RuntimeError("Simulated failure")

filters.local = ProblematicLocal()

filter_obj = RequestIDFilter()
record = logging.LogRecord(
    name="test", level=20, pathname="test.py", 
    lineno=1, msg="test", args=(), exc_info=None
)

# This crashes with unhandled RuntimeError
filter_obj.filter(record)
""")