import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/azure-mgmt-appconfiguration_env/lib/python3.13/site-packages')

import azure.common
from hypothesis import given, strategies as st, settings


# Test property 1: Status code 404 should return AzureMissingResourceHttpError
@given(st.text(min_size=1))  # Non-empty message
def test_status_404_returns_missing_resource_error(message):
    error = azure.common.AzureHttpError(message, 404)
    assert isinstance(error, azure.common.AzureMissingResourceHttpError)
    assert isinstance(error, azure.common.AzureHttpError)
    assert isinstance(error, azure.common.AzureException)
    assert error.status_code == 404
    assert str(error) == message


# Test property 2: Status code 409 should return AzureConflictHttpError  
@given(st.text(min_size=1))  # Non-empty message
def test_status_409_returns_conflict_error(message):
    error = azure.common.AzureHttpError(message, 409)
    assert isinstance(error, azure.common.AzureConflictHttpError)
    assert isinstance(error, azure.common.AzureHttpError)
    assert isinstance(error, azure.common.AzureException)
    assert error.status_code == 409
    assert str(error) == message


# Test property 3: Other status codes should return base AzureHttpError
@given(
    st.text(min_size=1),
    st.integers().filter(lambda x: x not in [404, 409])
)
def test_other_status_codes_return_base_http_error(message, status_code):
    error = azure.common.AzureHttpError(message, status_code)
    assert isinstance(error, azure.common.AzureHttpError)
    assert isinstance(error, azure.common.AzureException)
    # Should NOT be a more specific subclass
    assert not isinstance(error, azure.common.AzureMissingResourceHttpError)
    assert not isinstance(error, azure.common.AzureConflictHttpError)
    assert error.status_code == status_code
    assert str(error) == message


# Test property 4: Direct instantiation of subclasses should work
@given(
    st.text(min_size=1),
    st.integers()
)
def test_direct_subclass_instantiation(message, status_code):
    # Test AzureMissingResourceHttpError
    missing_error = azure.common.AzureMissingResourceHttpError(message, status_code)
    assert isinstance(missing_error, azure.common.AzureMissingResourceHttpError)
    assert missing_error.status_code == status_code
    assert str(missing_error) == message

    # Test AzureConflictHttpError
    conflict_error = azure.common.AzureConflictHttpError(message, status_code)
    assert isinstance(conflict_error, azure.common.AzureConflictHttpError)
    assert conflict_error.status_code == status_code
    assert str(conflict_error) == message


# Test property 5: Consistency property - creating the same error twice should produce equivalent objects
@given(
    st.text(min_size=1),
    st.integers()
)
def test_error_creation_consistency(message, status_code):
    error1 = azure.common.AzureHttpError(message, status_code)
    error2 = azure.common.AzureHttpError(message, status_code)
    assert type(error1) == type(error2)
    assert error1.status_code == error2.status_code
    assert str(error1) == str(error2)


# Test property 6: Message with special characters and Unicode
@given(
    st.text(min_size=1).filter(lambda x: x.strip()),  # Non-empty after stripping
    st.integers(min_value=100, max_value=599)  # Valid HTTP status codes
)
@settings(max_examples=1000)
def test_unicode_and_special_chars_in_message(message, status_code):
    error = azure.common.AzureHttpError(message, status_code)
    assert error.status_code == status_code
    assert str(error) == message
    
    # Check the type mapping still works correctly
    if status_code == 404:
        assert isinstance(error, azure.common.AzureMissingResourceHttpError)
    elif status_code == 409:
        assert isinstance(error, azure.common.AzureConflictHttpError)
    else:
        assert type(error) == azure.common.AzureHttpError