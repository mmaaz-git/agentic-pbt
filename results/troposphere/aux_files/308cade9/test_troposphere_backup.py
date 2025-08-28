#!/usr/bin/env python3
"""Property-based tests for troposphere.backup module"""

import json
import re
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the module under test
from troposphere.backup import (
    BackupSelectionResourceType,
    BackupVault,
    BackupPlan,
    BackupPlanResourceType,
    BackupRuleResourceType,
)
from troposphere.validators.backup import (
    backup_vault_name,
    validate_backup_selection, 
    validate_json_checker
)
from troposphere.validators import (
    boolean,
    integer,
    double,
    json_checker,
    exactly_one
)


# Test 1: backup_vault_name regex validator properties
@given(st.text(min_size=1, max_size=50))
def test_backup_vault_name_idempotence(name):
    """Valid vault names should be idempotent through the validator"""
    # Filter to only test valid names according to the regex pattern
    vault_name_re = re.compile(r"^[a-zA-Z0-9\-\_\.]{1,50}$")
    assume(vault_name_re.match(name))
    
    # Property: validating a valid name returns the same name
    result = backup_vault_name(name)
    assert result == name
    
    # Property: re-validating should also return the same name (idempotence)
    result2 = backup_vault_name(result)
    assert result2 == name


@given(st.text(min_size=0))
def test_backup_vault_name_invalid_patterns(name):
    """Invalid vault names should raise ValueError"""
    vault_name_re = re.compile(r"^[a-zA-Z0-9\-\_\.]{1,50}$")
    
    # Only test names that DON'T match the pattern
    assume(not vault_name_re.match(name))
    
    with pytest.raises(ValueError, match="is not a valid backup vault name"):
        backup_vault_name(name)


@given(
    st.from_regex(r"[a-zA-Z0-9\-\_\.]{1,50}", fullmatch=True)
)
def test_backup_vault_name_valid_generated(name):
    """All regex-generated valid names should pass validation"""
    result = backup_vault_name(name)
    assert result == name


# Test 2: json_checker round-trip properties
@given(
    st.dictionaries(
        st.text(min_size=1),
        st.recursive(
            st.one_of(
                st.none(),
                st.booleans(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text()
            ),
            lambda children: st.one_of(
                st.lists(children),
                st.dictionaries(st.text(min_size=1), children)
            ),
            max_leaves=10
        ),
        max_size=10
    )
)
def test_json_checker_dict_round_trip(data):
    """json_checker should convert dicts to JSON strings and be consistent"""
    # First conversion: dict -> json string
    json_str = json_checker(data)
    assert isinstance(json_str, str)
    
    # Verify it's valid JSON
    parsed = json.loads(json_str)
    assert parsed == data
    
    # Property: re-checking the JSON string should return the same string
    json_str2 = json_checker(json_str)
    assert json_str2 == json_str


@given(
    st.dictionaries(
        st.text(min_size=1),
        st.recursive(
            st.one_of(
                st.none(),
                st.booleans(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text()
            ),
            lambda children: st.one_of(
                st.lists(children),
                st.dictionaries(st.text(min_size=1), children)
            ),
            max_leaves=5
        ),
        max_size=5
    )
)
def test_json_checker_string_round_trip(data):
    """json_checker should validate JSON strings and preserve them"""
    # Convert dict to JSON string
    json_str = json.dumps(data)
    
    # Property: valid JSON strings should pass through unchanged
    result = json_checker(json_str)
    assert result == json_str
    
    # Verify it's still valid JSON
    assert json.loads(result) == data


# Test 3: boolean validator type conversion properties
@given(st.sampled_from([True, 1, "1", "true", "True"]))
def test_boolean_true_values(value):
    """All truthy values should convert to True"""
    result = boolean(value)
    assert result is True


@given(st.sampled_from([False, 0, "0", "false", "False"]))
def test_boolean_false_values(value):
    """All falsy values should convert to False"""
    result = boolean(value)
    assert result is False


@given(st.one_of(
    st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_invalid_values(value):
    """Invalid boolean values should raise ValueError"""
    with pytest.raises(ValueError):
        boolean(value)


# Test 4: integer validator properties
@given(st.integers())
def test_integer_valid_integers(value):
    """Valid integers should pass validation"""
    result = integer(value)
    assert result == value
    assert int(result) == value


@given(st.text(min_size=1).map(str))
def test_integer_string_integers(value):
    """String representations of integers should validate if valid"""
    try:
        int_val = int(value)
        result = integer(value)
        assert result == value
        assert int(result) == int_val
    except (ValueError, TypeError):
        # Should raise the same error through validator
        with pytest.raises(ValueError, match="is not a valid integer"):
            integer(value)


# Test 5: double validator properties  
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_valid_floats(value):
    """Valid floats should pass validation"""
    result = double(value)
    assert result == value
    assert float(result) == value


@given(st.integers())
def test_double_integers_as_floats(value):
    """Integers should be valid doubles"""
    result = double(value)
    assert result == value
    assert float(result) == float(value)


# Test 6: BackupSelectionResourceType validation
@given(
    st.booleans(),
    st.booleans()
)
def test_backup_selection_exactly_one(has_list_of_tags, has_resources):
    """BackupSelection should have exactly one of ListOfTags or Resources"""
    
    # Create a minimal BackupSelectionResourceType
    props = {
        "IamRoleArn": "arn:aws:iam::123456789012:role/BackupRole",
        "SelectionName": "TestSelection"
    }
    
    if has_list_of_tags:
        props["ListOfTags"] = []
    if has_resources:
        props["Resources"] = []
    
    selection = BackupSelectionResourceType(**props)
    
    # The validate method should enforce exactly one
    if has_list_of_tags and has_resources:
        # Both present - should fail
        with pytest.raises(ValueError, match="one of the following must be specified"):
            selection.validate()
    elif not has_list_of_tags and not has_resources:
        # Neither present - should fail
        with pytest.raises(ValueError, match="one of the following must be specified"):
            selection.validate()
    else:
        # Exactly one present - should succeed
        selection.validate()  # Should not raise


# Test 7: Test edge cases for vault name length
@given(st.integers(min_value=51, max_value=1000))
def test_backup_vault_name_too_long(length):
    """Names longer than 50 characters should fail"""
    name = "a" * length
    with pytest.raises(ValueError, match="is not a valid backup vault name"):
        backup_vault_name(name)


@given(st.sampled_from(["", "a" * 51, "test@vault", "test vault", "test#vault"]))
def test_backup_vault_name_known_invalid(name):
    """Known invalid patterns should fail"""
    with pytest.raises(ValueError, match="is not a valid backup vault name"):
        backup_vault_name(name)


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])