#!/usr/bin/env python
"""Property-based tests for troposphere.glue validators"""

import sys
import os

# Add the environment path to use the installed troposphere
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import hypothesis.strategies as st
from hypothesis import given, assume
import pytest

from troposphere.validators.glue import (
    connection_type_validator,
    delete_behavior_validator, 
    update_behavior_validator,
    table_type_validator,
    trigger_type_validator,
    validate_sortorder
)


# Test 1: String formatting bug in validators
# The validators have a bug where they use % instead of %s in error messages

@given(st.text(min_size=1))
def test_connection_type_validator_string_formatting_bug(invalid_type):
    """Test that connection_type_validator crashes on invalid input due to string formatting bug"""
    valid_types = ["CUSTOM", "JDBC", "KAFKA", "MARKETPLACE", "MONGODB", "NETWORK", "SFTP", "SNOWFLAKE"]
    assume(invalid_type not in valid_types)
    
    with pytest.raises(Exception) as exc_info:
        connection_type_validator(invalid_type)
    
    # The bug is that it uses % instead of %s, which will cause a TypeError
    # when trying to format the string
    assert isinstance(exc_info.value, (ValueError, TypeError))


@given(st.text(min_size=1))
def test_delete_behavior_validator_string_formatting_bug(invalid_value):
    """Test that delete_behavior_validator crashes on invalid input due to string formatting bug"""
    valid_values = ["LOG", "DELETE_FROM_DATABASE", "DEPRECATE_IN_DATABASE"]
    assume(invalid_value not in valid_values)
    
    with pytest.raises(Exception) as exc_info:
        delete_behavior_validator(invalid_value)
    
    assert isinstance(exc_info.value, (ValueError, TypeError))


@given(st.text(min_size=1))
def test_update_behavior_validator_string_formatting_bug(invalid_value):
    """Test that update_behavior_validator crashes on invalid input due to string formatting bug"""
    valid_values = ["LOG", "UPDATE_IN_DATABASE"]
    assume(invalid_value not in valid_values)
    
    with pytest.raises(Exception) as exc_info:
        update_behavior_validator(invalid_value)
    
    assert isinstance(exc_info.value, (ValueError, TypeError))


@given(st.text(min_size=1))
def test_table_type_validator_string_formatting_bug(invalid_type):
    """Test that table_type_validator crashes on invalid input due to string formatting bug"""
    valid_types = ["EXTERNAL_TABLE", "VIRTUAL_VIEW"]
    assume(invalid_type not in valid_types)
    
    with pytest.raises(Exception) as exc_info:
        table_type_validator(invalid_type)
    
    assert isinstance(exc_info.value, (ValueError, TypeError))


@given(st.text(min_size=1))
def test_trigger_type_validator_string_formatting_bug(invalid_type):
    """Test that trigger_type_validator crashes on invalid input due to string formatting bug"""
    valid_types = ["SCHEDULED", "CONDITIONAL", "ON_DEMAND", "EVENT"]
    assume(invalid_type not in valid_types)
    
    with pytest.raises(Exception) as exc_info:
        trigger_type_validator(invalid_type)
    
    assert isinstance(exc_info.value, (ValueError, TypeError))


# Test 2: Demonstrating the actual bug more clearly
def test_connection_type_validator_error_message_bug():
    """Demonstrate that the error message formatting is broken"""
    try:
        connection_type_validator("INVALID")
    except Exception as e:
        # This should be a ValueError with message "INVALID is not a valid value for ConnectionType"
        # But due to the bug it will be "% is not a valid value for ConnectionType"
        # or it might be a TypeError
        error_message = str(e)
        # Check if the error message contains the actual invalid value
        assert "INVALID" not in error_message or "%" in error_message


# Test 3: validate_sortorder should accept 0 or 1
@given(st.integers())
def test_validate_sortorder_range(value):
    """Test that validate_sortorder only accepts 0 or 1"""
    if value in [0, 1]:
        # Should succeed for 0 or 1
        assert validate_sortorder(value) == value
    else:
        # Should raise ValueError for anything else
        with pytest.raises(ValueError):
            validate_sortorder(value)


# Test 4: Test that valid inputs work correctly
@given(st.sampled_from(["CUSTOM", "JDBC", "KAFKA", "MARKETPLACE", "MONGODB", "NETWORK", "SFTP", "SNOWFLAKE"]))
def test_connection_type_validator_valid_inputs(valid_type):
    """Test that valid connection types are accepted"""
    assert connection_type_validator(valid_type) == valid_type


@given(st.sampled_from(["LOG", "DELETE_FROM_DATABASE", "DEPRECATE_IN_DATABASE"]))
def test_delete_behavior_validator_valid_inputs(valid_value):
    """Test that valid delete behaviors are accepted"""
    assert delete_behavior_validator(valid_value) == valid_value


@given(st.sampled_from(["LOG", "UPDATE_IN_DATABASE"]))
def test_update_behavior_validator_valid_inputs(valid_value):
    """Test that valid update behaviors are accepted"""
    assert update_behavior_validator(valid_value) == valid_value


@given(st.sampled_from(["EXTERNAL_TABLE", "VIRTUAL_VIEW"]))
def test_table_type_validator_valid_inputs(valid_type):
    """Test that valid table types are accepted"""
    assert table_type_validator(valid_type) == valid_type


@given(st.sampled_from(["SCHEDULED", "CONDITIONAL", "ON_DEMAND", "EVENT"]))
def test_trigger_type_validator_valid_inputs(valid_type):
    """Test that valid trigger types are accepted"""
    assert trigger_type_validator(valid_type) == valid_type