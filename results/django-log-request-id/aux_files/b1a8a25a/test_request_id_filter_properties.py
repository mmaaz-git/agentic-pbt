import logging
import sys
import os
import threading
from unittest.mock import MagicMock, patch

# Add the site-packages directory to Python path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')

# Setup Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'

# Create a minimal Django settings file
with open('test_settings.py', 'w') as f:
    f.write("""
SECRET_KEY = 'test-secret-key'
DEBUG = True
INSTALLED_APPS = []
""")

from hypothesis import given, strategies as st, settings, assume
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, Bundle

from log_request_id import local, DEFAULT_NO_REQUEST_ID
from log_request_id.filters import RequestIDFilter


# Property 1: Filter always returns True
@given(
    level=st.sampled_from([logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]),
    msg=st.text(),
    extra_attrs=st.dictionaries(
        keys=st.text(min_size=1).filter(lambda x: not x.startswith('_') and x != 'request_id'),
        values=st.one_of(st.text(), st.integers(), st.floats(allow_nan=False), st.none()),
        max_size=10
    )
)
def test_filter_always_returns_true(level, msg, extra_attrs):
    """The filter should never reject any log records."""
    filter_obj = RequestIDFilter()
    record = logging.LogRecord(
        name="test_logger",
        level=level,
        pathname="test.py",
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None
    )
    
    # Add extra attributes to the record
    for key, value in extra_attrs.items():
        setattr(record, key, value)
    
    # The filter should always return True
    assert filter_obj.filter(record) is True


# Property 2: Request ID attribute is always added
@given(
    level=st.sampled_from([logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]),
    msg=st.text(),
    request_id=st.one_of(st.none(), st.text(min_size=1), st.uuids().map(str))
)
def test_request_id_attribute_always_added(level, msg, request_id):
    """After filtering, every log record should have a request_id attribute."""
    filter_obj = RequestIDFilter()
    record = logging.LogRecord(
        name="test_logger",
        level=level,
        pathname="test.py",
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None
    )
    
    # Set or clear the local request_id
    if request_id is not None:
        local.request_id = request_id
    else:
        # Clear any existing request_id
        if hasattr(local, 'request_id'):
            del local.request_id
    
    filter_obj.filter(record)
    
    # The record should now have a request_id attribute
    assert hasattr(record, 'request_id')
    
    # Verify the value follows the expected behavior
    if request_id is not None:
        assert record.request_id == request_id
    else:
        # Should use the default value
        assert record.request_id == DEFAULT_NO_REQUEST_ID
    
    # Clean up
    if hasattr(local, 'request_id'):
        del local.request_id


# Property 3: Existing attributes are preserved
@given(
    extra_attrs=st.dictionaries(
        keys=st.text(min_size=1).filter(lambda x: not x.startswith('_') and x != 'request_id'),
        values=st.one_of(st.text(), st.integers(), st.floats(allow_nan=False), st.none()),
        min_size=1,
        max_size=10
    )
)
def test_existing_attributes_preserved(extra_attrs):
    """The filter should not modify any existing attributes of the log record."""
    filter_obj = RequestIDFilter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None
    )
    
    # Add extra attributes and store their values
    original_values = {}
    for key, value in extra_attrs.items():
        setattr(record, key, value)
        original_values[key] = value
    
    # Also store standard attributes
    standard_attrs = ['name', 'levelno', 'pathname', 'lineno', 'msg', 'args', 'exc_info']
    for attr in standard_attrs:
        original_values[attr] = getattr(record, attr)
    
    filter_obj.filter(record)
    
    # Check that all original attributes are unchanged
    for key, original_value in original_values.items():
        assert hasattr(record, key), f"Attribute {key} was removed"
        assert getattr(record, key) == original_value, f"Attribute {key} was modified"


# Property 4: Fallback chain for request_id
@given(
    has_local_id=st.booleans(),
    local_id_value=st.text(min_size=1),
    has_custom_default=st.booleans(),
    custom_default=st.text(min_size=1)
)
def test_request_id_fallback_chain(has_local_id, local_id_value, has_custom_default, custom_default):
    """Test the fallback chain: local.request_id → settings.NO_REQUEST_ID → DEFAULT_NO_REQUEST_ID"""
    
    # Clear any existing request_id
    if hasattr(local, 'request_id'):
        del local.request_id
    
    # Setup the mock settings
    mock_settings = MagicMock()
    if has_custom_default:
        mock_settings.NO_REQUEST_ID = custom_default
    else:
        # Simulate the setting not existing
        del mock_settings.NO_REQUEST_ID
    
    with patch('log_request_id.filters.settings', mock_settings):
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
        
        # Set local request_id if specified
        if has_local_id:
            local.request_id = local_id_value
        
        filter_obj.filter(record)
        
        # Verify the correct value is used based on the fallback chain
        if has_local_id:
            assert record.request_id == local_id_value
        elif has_custom_default:
            assert record.request_id == custom_default
        else:
            assert record.request_id == DEFAULT_NO_REQUEST_ID
    
    # Clean up
    if hasattr(local, 'request_id'):
        del local.request_id


# Property 5: Thread safety - each thread maintains its own request_id
@given(
    thread_count=st.integers(min_value=2, max_value=10),
    request_ids=st.lists(st.text(min_size=5, max_size=20), min_size=2, max_size=10, unique=True)
)
@settings(deadline=5000)  # Allow more time for thread operations
def test_thread_safety(thread_count, request_ids):
    """Different threads should maintain separate request IDs without interference."""
    assume(len(request_ids) >= thread_count)
    
    results = {}
    errors = []
    
    def thread_worker(thread_id, request_id):
        try:
            # Set the request_id for this thread
            local.request_id = request_id
            
            # Create a filter and process a record
            filter_obj = RequestIDFilter()
            record = logging.LogRecord(
                name=f"thread_{thread_id}",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg=f"Message from thread {thread_id}",
                args=(),
                exc_info=None
            )
            
            filter_obj.filter(record)
            
            # Store the result
            results[thread_id] = {
                'expected': request_id,
                'actual': record.request_id,
                'local_value': getattr(local, 'request_id', None)
            }
        except Exception as e:
            errors.append((thread_id, str(e)))
        finally:
            # Clean up
            if hasattr(local, 'request_id'):
                del local.request_id
    
    # Create and start threads
    threads = []
    for i in range(thread_count):
        thread = threading.Thread(target=thread_worker, args=(i, request_ids[i]))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check for errors
    assert len(errors) == 0, f"Thread errors occurred: {errors}"
    
    # Verify each thread got its own request_id
    for thread_id, result in results.items():
        assert result['actual'] == result['expected'], \
            f"Thread {thread_id} got wrong request_id: expected {result['expected']}, got {result['actual']}"


# Property 6: Record type handling - filter works with any LogRecord-like object
@given(
    has_standard_attrs=st.booleans(),
    extra_attrs=st.dictionaries(
        keys=st.text(min_size=1).filter(lambda x: not x.startswith('_')),
        values=st.one_of(st.text(), st.integers(), st.floats(allow_nan=False)),
        max_size=5
    )
)
def test_handles_various_record_types(has_standard_attrs, extra_attrs):
    """The filter should handle various types of log records correctly."""
    filter_obj = RequestIDFilter()
    
    # Create a mock object that simulates a LogRecord
    record = MagicMock()
    
    if has_standard_attrs:
        record.name = "test_logger"
        record.levelno = logging.INFO
        record.msg = "test message"
    
    # Add extra attributes
    for key, value in extra_attrs.items():
        setattr(record, key, value)
    
    # The filter should handle this without crashing
    result = filter_obj.filter(record)
    
    # Should still return True
    assert result is True
    
    # Should have added request_id
    assert hasattr(record, 'request_id')


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])