import json
import string
from hypothesis import given, strategies as st, assume, settings, example
import pytest
from troposphere.arczonalshift import (
    AutoshiftObserverNotificationStatus,
    ControlCondition,
    PracticeRunConfiguration,
    ZonalAutoshiftConfiguration,
)


# Edge case 1: Empty strings for required properties
def test_empty_string_for_required_property():
    """Empty strings should be allowed for required string properties"""
    obj = AutoshiftObserverNotificationStatus("ValidTitle", Status="")
    result = obj.to_dict(validation=True)
    assert result['Properties']['Status'] == ""


# Edge case 2: Test with None values
def test_none_values_for_optional_properties():
    """None values for optional properties should work correctly"""
    config = ZonalAutoshiftConfiguration(
        "TestConfig",
        ResourceIdentifier="test-resource",
        PracticeRunConfiguration=None,
        ZonalAutoshiftStatus=None
    )
    result = config.to_dict(validation=True)
    assert 'PracticeRunConfiguration' not in result['Properties']
    assert 'ZonalAutoshiftStatus' not in result['Properties']


# Edge case 3: Empty lists for list properties
def test_empty_lists():
    """Empty lists should be allowed for optional list properties"""
    cc = ControlCondition(AlarmIdentifier="test", Type="test")
    config = PracticeRunConfiguration(
        BlockedDates=[],
        BlockedWindows=[],
        BlockingAlarms=[],
        OutcomeAlarms=[cc]  # Required, must have at least one
    )
    result = config.to_dict(validation=True)
    assert result['BlockedDates'] == []
    assert result['BlockedWindows'] == []
    assert result['BlockingAlarms'] == []


# Edge case 4: Maximum length title
def test_max_length_title():
    """Test maximum length titles (255 characters)"""
    max_title = "A" * 255
    obj = AutoshiftObserverNotificationStatus(max_title, Status="ENABLED")
    assert obj.title == max_title


# Edge case 5: Unicode in string properties
@given(unicode_str=st.text(alphabet=st.characters(min_codepoint=0x100, max_codepoint=0x1000), min_size=1))
def test_unicode_in_properties(unicode_str):
    """Unicode characters should be handled correctly in string properties"""
    obj = AutoshiftObserverNotificationStatus("ValidTitle", Status=unicode_str)
    result = obj.to_dict(validation=True)
    assert result['Properties']['Status'] == unicode_str


# Edge case 6: Very large lists
@settings(max_examples=10)
@given(
    dates=st.lists(st.text(min_size=1, max_size=10), min_size=100, max_size=1000)
)
def test_large_lists(dates):
    """Large lists should be handled correctly"""
    cc = ControlCondition(AlarmIdentifier="test", Type="test")
    config = PracticeRunConfiguration(
        BlockedDates=dates,
        OutcomeAlarms=[cc]
    )
    result = config.to_dict(validation=True)
    assert result['BlockedDates'] == dates
    assert len(result['BlockedDates']) == len(dates)


# Edge case 7: Special characters in property values (not titles)
@given(special_str=st.text(alphabet=string.printable, min_size=1))
def test_special_chars_in_values(special_str):
    """Special characters should be allowed in property values (not titles)"""
    obj = AutoshiftObserverNotificationStatus("ValidTitle", Status=special_str)
    result = obj.to_dict(validation=True)
    assert result['Properties']['Status'] == special_str


# Edge case 8: Test validation=False bypass
def test_validation_false_bypass():
    """validation=False should bypass required property checks"""
    obj = AutoshiftObserverNotificationStatus("ValidTitle")
    # Should not raise even though Status is missing
    result = obj.to_dict(validation=False)
    assert 'Status' not in result.get('Properties', {})


# Edge case 9: Deep nesting stress test
@settings(max_examples=10)
@given(
    num_blocking=st.integers(min_value=0, max_value=50),
    num_outcome=st.integers(min_value=1, max_value=50)
)
def test_deep_nesting(num_blocking, num_outcome):
    """Test deeply nested structures with many ControlConditions"""
    blocking_alarms = [
        ControlCondition(AlarmIdentifier=f"block_{i}", Type=f"type_{i}")
        for i in range(num_blocking)
    ]
    outcome_alarms = [
        ControlCondition(AlarmIdentifier=f"outcome_{i}", Type=f"type_{i}")
        for i in range(num_outcome)
    ]
    
    config = PracticeRunConfiguration(
        BlockingAlarms=blocking_alarms,
        OutcomeAlarms=outcome_alarms
    )
    
    result = config.to_dict(validation=True)
    assert len(result['BlockingAlarms']) == num_blocking
    assert len(result['OutcomeAlarms']) == num_outcome


# Edge case 10: Test no_validation() method
def test_no_validation_method():
    """no_validation() should disable validation permanently"""
    obj = AutoshiftObserverNotificationStatus("ValidTitle")
    obj.no_validation()
    
    # Should not raise even with validation=True because no_validation() was called
    result = obj.to_dict(validation=True)
    assert 'Status' not in result.get('Properties', {})


# Edge case 11: Test property overwriting
def test_property_overwriting():
    """Properties should be overwritable"""
    obj = AutoshiftObserverNotificationStatus("ValidTitle", Status="INITIAL")
    obj.Status = "UPDATED"
    result = obj.to_dict(validation=True)
    assert result['Properties']['Status'] == "UPDATED"


# Edge case 12: Test with AWS helper functions (simulated)
def test_with_aws_helper_fn():
    """Test that AWS helper functions bypass type validation"""
    from troposphere import Ref
    
    # Using Ref should bypass normal type validation
    obj = AutoshiftObserverNotificationStatus("ValidTitle", Status=Ref("SomeParameter"))
    result = obj.to_dict(validation=True)
    assert result['Properties']['Status']['Ref'] == "SomeParameter"


# Edge case 13: Test integer as string property
def test_integer_as_string():
    """Test that integers are rejected for string properties"""
    with pytest.raises(TypeError):
        AutoshiftObserverNotificationStatus("ValidTitle", Status=123)


# Edge case 14: Test from_dict with extra keys
def test_from_dict_extra_keys():
    """from_dict should reject unknown properties"""
    with pytest.raises(AttributeError):
        AutoshiftObserverNotificationStatus.from_dict(
            "TestTitle",
            {"Status": "ENABLED", "UnknownProperty": "value"}
        )


# Edge case 15: Test missing required nested property
def test_missing_required_nested_property():
    """Missing required properties in nested objects should be caught"""
    # Try to create PracticeRunConfiguration without required OutcomeAlarms
    config = PracticeRunConfiguration()
    with pytest.raises(ValueError, match="Resource OutcomeAlarms required"):
        config.to_dict(validation=True)