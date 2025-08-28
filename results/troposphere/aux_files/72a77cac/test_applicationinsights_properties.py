#!/usr/bin/env python3
"""Property-based tests for troposphere.applicationinsights module."""

import string
from hypothesis import given, strategies as st, settings, assume
import troposphere.applicationinsights as appinsights
from troposphere import validators
from troposphere import AWSObject, AWSProperty


# Test 1: Boolean validator accepts documented valid inputs and rejects invalid ones
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
    st.text(min_size=1),
    st.integers(),
    st.floats(),
    st.none()
))
def test_boolean_validator(value):
    """Test that boolean validator accepts documented values and rejects others."""
    valid_true = [True, 1, "1", "true", "True"]
    valid_false = [False, 0, "0", "false", "False"]
    
    if value in valid_true:
        result = validators.boolean(value)
        assert result is True
    elif value in valid_false:
        result = validators.boolean(value)
        assert result is False
    else:
        try:
            validators.boolean(value)
            assert False, f"Should have raised ValueError for {value}"
        except ValueError:
            pass  # Expected


# Test 2: Integer validator accepts valid integers and rejects invalid ones
@given(st.one_of(
    st.integers(),
    st.text(alphabet=string.digits, min_size=1),
    st.floats(),
    st.text(min_size=1),
    st.none()
))
def test_integer_validator(value):
    """Test that integer validator accepts valid integers."""
    try:
        int(value)
        # If int() succeeds, validator should succeed
        result = validators.integer(value)
        assert result == value
    except (ValueError, TypeError):
        # If int() fails, validator should fail
        try:
            validators.integer(value)
            assert False, f"Should have raised ValueError for {value}"
        except ValueError:
            pass  # Expected


# Test 3: Required properties validation for Application class
@given(
    resource_group_name=st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=10),
    auto_config=st.booleans(),
    ops_center=st.booleans()
)
def test_application_required_properties(resource_group_name, auto_config, ops_center):
    """Test that Application enforces required ResourceGroupName property."""
    # Valid creation with required property
    app = appinsights.Application(
        "TestApp",
        ResourceGroupName=resource_group_name
    )
    
    # Verify the property was set
    assert app.ResourceGroupName == resource_group_name
    
    # Test validation - should succeed with required property present
    app._validate_props()
    
    # Optional properties should work
    app2 = appinsights.Application(
        "TestApp2",
        ResourceGroupName=resource_group_name,
        AutoConfigurationEnabled=auto_config,
        OpsCenterEnabled=ops_center
    )
    app2._validate_props()


# Test 4: Round-trip to_dict/from_dict for simple properties
@given(
    alarm_name=st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20),
    severity=st.one_of(st.none(), st.text(min_size=1, max_size=10))
)
def test_alarm_round_trip(alarm_name, severity):
    """Test that Alarm objects can round-trip through to_dict/from_dict."""
    # Create an Alarm object
    kwargs = {"AlarmName": alarm_name}
    if severity is not None:
        kwargs["Severity"] = severity
    
    alarm = appinsights.Alarm(**kwargs)
    
    # Convert to dict
    alarm_dict = alarm.to_dict()
    
    # Create new object from dict
    alarm2 = appinsights.Alarm._from_dict(**alarm_dict)
    
    # Verify properties match
    assert alarm2.AlarmName == alarm_name
    if severity is not None:
        assert alarm2.Severity == severity
    
    # Dicts should be equal
    assert alarm.to_dict() == alarm2.to_dict()


# Test 5: LogPattern rank property accepts integers
@given(
    pattern=st.text(min_size=1, max_size=50),
    pattern_name=st.text(alphabet=string.ascii_letters, min_size=1, max_size=20),
    rank=st.integers(min_value=-1000000, max_value=1000000)
)
def test_logpattern_rank_integer(pattern, pattern_name, rank):
    """Test that LogPattern rank property accepts integers."""
    log_pattern = appinsights.LogPattern(
        Pattern=pattern,
        PatternName=pattern_name,
        Rank=rank
    )
    
    # The rank should be stored and retrievable
    assert log_pattern.Rank == rank
    
    # Should be able to convert to dict
    pattern_dict = log_pattern.to_dict()
    assert pattern_dict["Rank"] == rank


# Test 6: Title validation for Application objects
@given(
    title=st.text(min_size=1, max_size=50)
)
def test_application_title_validation(title):
    """Test that Application title validation follows documented rules."""
    # Title must be alphanumeric only
    is_valid_title = bool(title and title.replace('_', '').isalnum() and title.isalnum())
    
    if is_valid_title:
        # Should succeed
        app = appinsights.Application(
            title,
            ResourceGroupName="TestGroup"
        )
        app.validate_title()
        assert app.title == title
    else:
        # Should fail with invalid title
        try:
            app = appinsights.Application(
                title,
                ResourceGroupName="TestGroup"
            )
            if app.title:  # Only validates if title is not None/empty
                app.validate_title()
                # If we get here, the title was accepted when it shouldn't have been
                assert title == "" or title.isalnum(), f"Invalid title {title!r} was accepted"
        except ValueError as e:
            assert "not alphanumeric" in str(e)


# Test 7: HANAPrometheusExporter required properties
@given(
    agree=st.booleans(),
    port=st.text(min_size=1, max_size=10),
    sid=st.text(min_size=1, max_size=10),
    secret=st.text(min_size=1, max_size=20)
)
def test_hana_exporter_required_properties(agree, port, sid, secret):
    """Test HANAPrometheusExporter enforces all required properties."""
    exporter = appinsights.HANAPrometheusExporter(
        AgreeToInstallHANADBClient=agree,
        HANAPort=port,
        HANASID=sid,
        HANASecretName=secret
    )
    
    # Should validate successfully with all required properties
    exporter._validate_props()
    
    # Verify properties
    assert exporter.AgreeToInstallHANADBClient == agree
    assert exporter.HANAPort == port
    assert exporter.HANASID == sid
    assert exporter.HANASecretName == secret


# Test 8: SubComponentTypeConfiguration nested properties
@given(
    sub_type=st.text(alphabet=string.ascii_letters, min_size=1, max_size=20)
)
def test_subcomponent_nested_properties(sub_type):
    """Test that SubComponentTypeConfiguration handles nested properties correctly."""
    # Create nested SubComponentConfigurationDetails
    details = appinsights.SubComponentConfigurationDetails()
    
    # Create SubComponentTypeConfiguration with nested object
    config = appinsights.SubComponentTypeConfiguration(
        SubComponentType=sub_type,
        SubComponentConfigurationDetails=details
    )
    
    # Should validate and convert to dict correctly
    config._validate_props()
    config_dict = config.to_dict()
    
    assert config.SubComponentType == sub_type
    assert "SubComponentConfigurationDetails" in config_dict
    assert "SubComponentType" in config_dict


# Test 9: WindowsEvent EventLevels list property
@given(
    event_levels=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5),
    event_name=st.text(min_size=1, max_size=20),
    log_group=st.text(min_size=1, max_size=20)
)
def test_windows_event_list_property(event_levels, event_name, log_group):
    """Test that WindowsEvent accepts list of strings for EventLevels."""
    event = appinsights.WindowsEvent(
        EventLevels=event_levels,
        EventName=event_name,
        LogGroupName=log_group
    )
    
    # Properties should be stored correctly
    assert event.EventLevels == event_levels
    assert event.EventName == event_name
    assert event.LogGroupName == log_group
    
    # Should convert to dict correctly
    event_dict = event.to_dict()
    assert event_dict["EventLevels"] == event_levels


# Test 10: Process AlarmMetrics list of objects property
@given(
    process_name=st.text(min_size=1, max_size=20),
    metric_names=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=3)
)
def test_process_alarm_metrics_list(process_name, metric_names):
    """Test that Process accepts list of AlarmMetric objects."""
    # Create list of AlarmMetric objects
    metrics = [appinsights.AlarmMetric(AlarmMetricName=name) for name in metric_names]
    
    # Create Process with list of objects
    process = appinsights.Process(
        ProcessName=process_name,
        AlarmMetrics=metrics
    )
    
    # Should validate and store correctly
    process._validate_props()
    assert process.ProcessName == process_name
    assert len(process.AlarmMetrics) == len(metrics)
    
    # Convert to dict and verify structure
    process_dict = process.to_dict()
    assert "AlarmMetrics" in process_dict
    assert len(process_dict["AlarmMetrics"]) == len(metric_names)


if __name__ == "__main__":
    print("Running property-based tests for troposphere.applicationinsights...")
    import pytest
    pytest.main([__file__, "-v"])