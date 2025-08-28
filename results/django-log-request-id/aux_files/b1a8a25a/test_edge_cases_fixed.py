import logging
import sys
import os
from unittest.mock import MagicMock, patch, PropertyMock

# Add the site-packages directory to Python path
sys.path.insert(0, '/root/hypothesis-llm/envs/django-log-request-id_env/lib/python3.13/site-packages')

# Setup Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'

from hypothesis import given, strategies as st, settings as hyp_settings, assume
from log_request_id import local, DEFAULT_NO_REQUEST_ID, LOG_REQUESTS_NO_SETTING
from log_request_id.filters import RequestIDFilter


# Test 1: Pre-existing request_id attribute behavior
@given(
    pre_existing_value=st.one_of(st.text(), st.integers(), st.none()),
    local_value=st.one_of(st.text(), st.none())
)
def test_pre_existing_request_id_attribute(pre_existing_value, local_value):
    """What happens if the LogRecord already has a request_id attribute?"""
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
    
    # Set a pre-existing request_id attribute
    record.request_id = pre_existing_value
    
    # Set or clear local request_id
    if local_value is not None:
        local.request_id = local_value
    elif hasattr(local, 'request_id'):
        del local.request_id
    
    filter_obj.filter(record)
    
    # The filter should override the pre-existing value
    if local_value is not None:
        assert record.request_id == local_value
    else:
        assert record.request_id == DEFAULT_NO_REQUEST_ID
    
    # Clean up
    if hasattr(local, 'request_id'):
        del local.request_id


# Test 2: Empty string as request_id
@given(use_empty_string=st.booleans())
def test_empty_string_request_id(use_empty_string):
    """Test behavior with empty string as request_id."""
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
    
    # Set empty string or regular value
    if use_empty_string:
        local.request_id = ""
    else:
        local.request_id = "normal_id"
    
    filter_obj.filter(record)
    
    # Should preserve the exact value, even if empty
    if use_empty_string:
        assert record.request_id == ""
    else:
        assert record.request_id == "normal_id"
    
    # Clean up
    del local.request_id


# Test 3: getattr behavior with AttributeError
def test_getattr_attribute_error():
    """Test what happens when getattr raises AttributeError."""
    
    # Create a mock local that raises AttributeError for request_id
    mock_local = MagicMock()
    mock_local.request_id = PropertyMock(side_effect=AttributeError("request_id not found"))
    
    with patch('log_request_id.filters.local', mock_local):
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
        
        # Should handle the AttributeError gracefully
        result = filter_obj.filter(record)
        assert result is True
        assert hasattr(record, 'request_id')
        # Should fall back to default
        assert record.request_id == DEFAULT_NO_REQUEST_ID


# Test 4: Settings with NO_REQUEST_ID set to various types
@given(
    setting_value=st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False),
        st.none(),
        st.just(0),
        st.just(""),
        st.just(False)
    )
)
def test_various_no_request_id_setting_types(setting_value):
    """Test with various types for the NO_REQUEST_ID setting."""
    
    # Clear local request_id
    if hasattr(local, 'request_id'):
        del local.request_id
    
    mock_settings = MagicMock()
    setattr(mock_settings, LOG_REQUESTS_NO_SETTING, setting_value)
    
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
        
        filter_obj.filter(record)
        
        # Should use the setting value as-is
        assert record.request_id == setting_value


# Test 5: Very long request_id values
@given(
    length=st.integers(min_value=1000, max_value=100000)
)
@hyp_settings(max_examples=10)  # Reduce examples for performance
def test_very_long_request_id(length):
    """Test with very long request_id strings."""
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
    
    # Create a very long request_id
    long_id = "x" * length
    local.request_id = long_id
    
    filter_obj.filter(record)
    
    # Should handle long strings without truncation
    assert record.request_id == long_id
    assert len(record.request_id) == length
    
    # Clean up
    del local.request_id


# Test 6: Unicode and special characters
@given(
    request_id=st.text(
        alphabet=st.characters(blacklist_categories=('Cs',)),  # All unicode except surrogates
        min_size=1
    )
)
def test_unicode_request_id(request_id):
    """Test with various unicode characters in request_id."""
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
    
    local.request_id = request_id
    
    filter_obj.filter(record)
    
    # Should preserve unicode characters exactly
    assert record.request_id == request_id
    
    # Clean up
    del local.request_id


# Test 7: Callable objects as request_id
def test_callable_as_request_id():
    """Test with callable objects as request_id."""
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
    
    # Use a function as request_id
    def my_function():
        return "function_result"
    
    local.request_id = my_function
    
    filter_obj.filter(record)
    
    # Should store the function object itself, not call it
    assert record.request_id == my_function
    assert callable(record.request_id)
    
    # Clean up
    del local.request_id


# Test 8: Class instances as request_id
@given(
    class_name=st.text(min_size=1, max_size=20).filter(lambda x: x.isidentifier()),
    attr_value=st.text()
)
def test_class_instance_as_request_id(class_name, attr_value):
    """Test with custom class instances as request_id."""
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
    
    # Create a dynamic class
    CustomClass = type(class_name, (), {'value': attr_value})
    instance = CustomClass()
    
    local.request_id = instance
    
    filter_obj.filter(record)
    
    # Should store the instance as-is
    assert record.request_id == instance
    assert isinstance(record.request_id, CustomClass)
    assert record.request_id.value == attr_value
    
    # Clean up
    del local.request_id


# Test 9: None as explicit value vs missing attribute
def test_none_vs_missing():
    """Test difference between None value and missing attribute."""
    filter_obj = RequestIDFilter()
    
    # Test 1: explicitly set to None
    record1 = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test",
        args=(),
        exc_info=None
    )
    
    local.request_id = None
    filter_obj.filter(record1)
    assert record1.request_id is None
    
    # Test 2: attribute doesn't exist
    del local.request_id
    record2 = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test",
        args=(),
        exc_info=None
    )
    
    filter_obj.filter(record2)
    assert record2.request_id == DEFAULT_NO_REQUEST_ID
    
    # Clean up
    if hasattr(local, 'request_id'):
        del local.request_id


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])