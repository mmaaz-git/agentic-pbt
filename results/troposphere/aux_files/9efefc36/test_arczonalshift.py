import json
import string
from hypothesis import given, strategies as st, assume, settings
import pytest
from troposphere.arczonalshift import (
    AutoshiftObserverNotificationStatus,
    ControlCondition,
    PracticeRunConfiguration,
    ZonalAutoshiftConfiguration,
)


# Strategy for valid CloudFormation resource names (alphanumeric only)
valid_title_strategy = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=1,
    max_size=255
)

# Strategy for invalid titles with special characters
invalid_title_strategy = st.text(min_size=1, max_size=255).filter(
    lambda x: not x.replace(' ', '').isalnum() or ' ' in x or x == ''
)

# Property 1: Title validation - titles must be alphanumeric
@given(title=valid_title_strategy)
def test_valid_title_accepted(title):
    """Valid alphanumeric titles should be accepted"""
    obj = AutoshiftObserverNotificationStatus(title, Status="ENABLED")
    assert obj.title == title


@given(title=invalid_title_strategy)
def test_invalid_title_rejected(title):
    """Titles with non-alphanumeric characters should be rejected"""
    with pytest.raises(ValueError, match="not alphanumeric"):
        AutoshiftObserverNotificationStatus(title, Status="ENABLED")


# Property 2: Required properties validation
@given(title=valid_title_strategy)
def test_required_properties_enforced(title):
    """Required properties must be present when validation occurs"""
    # AutoshiftObserverNotificationStatus requires Status
    obj = AutoshiftObserverNotificationStatus(title)
    # Should raise error when converting to dict with validation
    with pytest.raises(ValueError, match="Resource Status required"):
        obj.to_dict(validation=True)


@given(title=valid_title_strategy, status=st.text(min_size=1))
def test_required_properties_satisfied(title, status):
    """Objects with all required properties should validate successfully"""
    obj = AutoshiftObserverNotificationStatus(title, Status=status)
    # Should not raise when all required properties are present
    result = obj.to_dict(validation=True)
    assert result['Properties']['Status'] == status


# Property 3: Type validation for properties
@given(
    title=valid_title_strategy,
    alarm_id=st.text(min_size=1),
    alarm_type=st.text(min_size=1)
)
def test_control_condition_properties(title, alarm_id, alarm_type):
    """ControlCondition should accept string properties"""
    cc = ControlCondition(AlarmIdentifier=alarm_id, Type=alarm_type)
    result = cc.to_dict(validation=True)
    assert result['AlarmIdentifier'] == alarm_id
    assert result['Type'] == alarm_type


# Property 4: to_dict/from_dict round-trip
@given(
    title=valid_title_strategy,
    status=st.text(min_size=1, max_size=50)
)
def test_to_dict_from_dict_roundtrip(title, status):
    """Objects should survive to_dict -> from_dict round-trip"""
    original = AutoshiftObserverNotificationStatus(title, Status=status)
    dict_repr = original.to_dict(validation=False)
    
    # Extract just the Properties part for from_dict
    reconstructed = AutoshiftObserverNotificationStatus.from_dict(
        title, dict_repr['Properties']
    )
    
    assert reconstructed.title == original.title
    assert reconstructed.Status == original.Status
    assert reconstructed.to_dict(validation=False) == original.to_dict(validation=False)


# Property 5: JSON serialization consistency
@given(
    title=valid_title_strategy,
    status=st.text(min_size=1)
)
def test_json_serialization_consistency(title, status):
    """JSON serialization should be consistent and parseable"""
    obj = AutoshiftObserverNotificationStatus(title, Status=status)
    json_str = obj.to_json(validation=False)
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    
    # Should contain expected structure
    assert 'Type' in parsed
    assert parsed['Type'] == 'AWS::ARCZonalShift::AutoshiftObserverNotificationStatus'
    assert 'Properties' in parsed
    assert parsed['Properties']['Status'] == status


# Property 6: List properties validation for PracticeRunConfiguration
@given(
    blocked_dates=st.lists(st.text(min_size=1, max_size=20), max_size=5),
    blocked_windows=st.lists(st.text(min_size=1, max_size=20), max_size=5),
    alarm_id=st.text(min_size=1, max_size=20),
    alarm_type=st.text(min_size=1, max_size=20)
)
def test_practice_run_list_properties(blocked_dates, blocked_windows, alarm_id, alarm_type):
    """PracticeRunConfiguration should handle list properties correctly"""
    # Create a control condition for required OutcomeAlarms
    cc = ControlCondition(AlarmIdentifier=alarm_id, Type=alarm_type)
    
    config = PracticeRunConfiguration(
        BlockedDates=blocked_dates,
        BlockedWindows=blocked_windows,
        OutcomeAlarms=[cc]
    )
    
    result = config.to_dict(validation=True)
    assert result['BlockedDates'] == blocked_dates
    assert result['BlockedWindows'] == blocked_windows
    assert len(result['OutcomeAlarms']) == 1


# Property 7: Complex nested structures
@given(
    title=valid_title_strategy,
    resource_id=st.text(min_size=1, max_size=100),
    autoshift_status=st.sampled_from(["ENABLED", "DISABLED"]),
    blocked_dates=st.lists(st.text(min_size=1, max_size=20), max_size=3),
    alarm_id=st.text(min_size=1, max_size=20),
    alarm_type=st.text(min_size=1, max_size=20)
)
def test_nested_structure_validation(title, resource_id, autoshift_status, 
                                      blocked_dates, alarm_id, alarm_type):
    """ZonalAutoshiftConfiguration should handle nested structures correctly"""
    cc = ControlCondition(AlarmIdentifier=alarm_id, Type=alarm_type)
    practice_config = PracticeRunConfiguration(
        BlockedDates=blocked_dates,
        OutcomeAlarms=[cc]
    )
    
    config = ZonalAutoshiftConfiguration(
        title,
        ResourceIdentifier=resource_id,
        ZonalAutoshiftStatus=autoshift_status,
        PracticeRunConfiguration=practice_config
    )
    
    result = config.to_dict(validation=True)
    assert result['Properties']['ResourceIdentifier'] == resource_id
    assert result['Properties']['ZonalAutoshiftStatus'] == autoshift_status
    assert 'PracticeRunConfiguration' in result['Properties']
    assert result['Properties']['PracticeRunConfiguration']['BlockedDates'] == blocked_dates


# Property 8: Equality and hashing
@given(
    title=valid_title_strategy,
    status=st.text(min_size=1, max_size=50)
)
def test_equality_and_hashing(title, status):
    """Equal objects should have equal hashes and compare as equal"""
    obj1 = AutoshiftObserverNotificationStatus(title, Status=status)
    obj2 = AutoshiftObserverNotificationStatus(title, Status=status)
    
    # Objects with same properties should be equal
    assert obj1 == obj2
    assert hash(obj1) == hash(obj2)
    
    # Different status should make them unequal
    obj3 = AutoshiftObserverNotificationStatus(title, Status=status + "DIFFERENT")
    assert obj1 != obj3
    assert hash(obj1) != hash(obj3)


# Property 9: Properties not in schema are rejected
@given(
    title=valid_title_strategy,
    status=st.text(min_size=1),
    invalid_prop=st.text(min_size=1)
)
def test_invalid_properties_rejected(title, status, invalid_prop):
    """Properties not defined in the schema should be rejected"""
    assume(invalid_prop not in ["Status", "title", "template", "validation"])
    
    with pytest.raises(AttributeError):
        AutoshiftObserverNotificationStatus(
            title, 
            Status=status,
            **{invalid_prop: "value"}
        )


# Property 10: Type enforcement for ControlCondition lists
@given(
    alarm_ids=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
    alarm_types=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5)
)
def test_control_condition_list_type_enforcement(alarm_ids, alarm_types):
    """Lists of ControlConditions should maintain type safety"""
    # Make lists same length
    min_len = min(len(alarm_ids), len(alarm_types))
    alarm_ids = alarm_ids[:min_len]
    alarm_types = alarm_types[:min_len]
    
    conditions = [
        ControlCondition(AlarmIdentifier=aid, Type=atype)
        for aid, atype in zip(alarm_ids, alarm_types)
    ]
    
    config = PracticeRunConfiguration(OutcomeAlarms=conditions)
    result = config.to_dict(validation=True)
    
    assert len(result['OutcomeAlarms']) == len(conditions)
    for i, alarm_dict in enumerate(result['OutcomeAlarms']):
        assert alarm_dict['AlarmIdentifier'] == alarm_ids[i]
        assert alarm_dict['Type'] == alarm_types[i]