#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python
"""Property-based tests for troposphere.lookoutmetrics module"""

import sys
import json
from hypothesis import given, strategies as st, assume, settings
import pytest

sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import lookoutmetrics
from troposphere.validators import boolean, integer


# Test 1: Boolean validator properties
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_validator_valid_inputs(value):
    """boolean() should accept documented valid values"""
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["true", "True", "false", "False", "1", "0"]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """boolean() should raise ValueError for non-boolean inputs"""
    with pytest.raises(ValueError):
        boolean(value)


# Test 2: Integer validator properties
@given(st.one_of(
    st.integers(),
    st.text(min_size=1).map(lambda x: str(st.integers().example())),
))
def test_integer_validator_valid(value):
    """integer() should accept valid integer representations"""
    try:
        int(value)
        can_convert = True
    except (ValueError, TypeError):
        can_convert = False
    
    if can_convert:
        result = integer(value)
        assert result == value
    else:
        with pytest.raises(ValueError):
            integer(value)


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_validator_floats(value):
    """integer() should handle float inputs correctly"""
    if value.is_integer():
        result = integer(value)
        assert result == value
    else:
        with pytest.raises(ValueError):
            integer(value)


# Test 3: Round-trip properties for AWS objects
@given(
    action_dict=st.fixed_dictionaries({
        "SNSConfiguration": st.fixed_dictionaries({
            "RoleArn": st.text(min_size=1, max_size=100),
            "SnsTopicArn": st.text(min_size=1, max_size=100)
        })
    }),
    alert_sensitivity=st.integers(min_value=0, max_value=100),
    detector_arn=st.text(min_size=1, max_size=200)
)
def test_alert_to_dict_from_dict_roundtrip(action_dict, alert_sensitivity, detector_arn):
    """Alert objects should round-trip through to_dict and from_dict"""
    # Create an Alert with required properties
    alert = lookoutmetrics.Alert(
        "TestAlert",
        Action=lookoutmetrics.Action(**action_dict),
        AlertSensitivityThreshold=alert_sensitivity,
        AnomalyDetectorArn=detector_arn
    )
    
    # Convert to dict
    alert_dict = alert.to_dict(validation=False)
    
    # Extract properties
    props = alert_dict.get("Properties", {})
    
    # Create new alert from dict
    alert2 = lookoutmetrics.Alert.from_dict("TestAlert", props)
    
    # Compare
    assert alert.title == alert2.title
    assert alert.to_json(validation=False) == alert2.to_json(validation=False)


# Test 4: Required property validation
@given(
    role_arn=st.text(min_size=1, max_size=100),
    sns_topic=st.text(min_size=1, max_size=100)
)
def test_sns_configuration_required_properties(role_arn, sns_topic):
    """SNSConfiguration should enforce required properties"""
    # Valid creation with all required properties
    config = lookoutmetrics.SNSConfiguration(
        RoleArn=role_arn,
        SnsTopicArn=sns_topic
    )
    config_dict = config.to_dict(validation=True)
    assert "RoleArn" in config_dict
    assert "SnsTopicArn" in config_dict
    
    # Missing required property should fail validation
    partial_config = lookoutmetrics.SNSConfiguration()
    partial_config.RoleArn = role_arn
    # Don't set SnsTopicArn
    with pytest.raises(ValueError, match="required"):
        partial_config.to_dict(validation=True)


# Test 5: Property type validation
@given(
    port_value=st.one_of(
        st.integers(min_value=-2, max_value=100000),
        st.text(min_size=1, max_size=10),
        st.floats()
    )
)
def test_database_port_type_validation(port_value):
    """Database port properties should validate integer types"""
    config = lookoutmetrics.RDSSourceConfig()
    
    # Try to set DatabasePort
    try:
        int(port_value)
        is_valid_int = True
    except (ValueError, TypeError):
        is_valid_int = False
    
    if is_valid_int:
        config.DatabasePort = port_value
        # Should accept valid integer representations
        assert config.DatabasePort == port_value
    else:
        # Should reject non-integer values
        config.DatabasePort = port_value
        # The value is set but validation should fail when converting to dict
        # if validators are properly applied


# Test 6: VpcConfiguration list properties
@given(
    security_groups=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5),
    subnet_ids=st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=5)
)
def test_vpc_configuration_list_properties(security_groups, subnet_ids):
    """VpcConfiguration should handle list properties correctly"""
    vpc_config = lookoutmetrics.VpcConfiguration(
        SecurityGroupIdList=security_groups,
        SubnetIdList=subnet_ids
    )
    
    vpc_dict = vpc_config.to_dict(validation=False)
    assert vpc_dict["SecurityGroupIdList"] == security_groups
    assert vpc_dict["SubnetIdList"] == subnet_ids
    
    # Lists should be preserved in round-trip
    vpc_config2 = lookoutmetrics.VpcConfiguration._from_dict(**vpc_dict)
    assert vpc_config2.SecurityGroupIdList == security_groups
    assert vpc_config2.SubnetIdList == subnet_ids


# Test 7: MetricSet complex nested properties
@given(
    metric_name=st.text(min_size=1, max_size=50),
    agg_function=st.sampled_from(["SUM", "AVG", "MIN", "MAX", "COUNT"]),
    metric_set_name=st.text(min_size=1, max_size=50),
    s3_role_arn=st.text(min_size=20, max_size=100)
)
def test_metric_set_nested_properties(metric_name, agg_function, metric_set_name, s3_role_arn):
    """MetricSet should handle deeply nested properties correctly"""
    metric = lookoutmetrics.Metric(
        MetricName=metric_name,
        AggregationFunction=agg_function
    )
    
    file_format = lookoutmetrics.FileFormatDescriptor(
        CsvFormatDescriptor=lookoutmetrics.CsvFormatDescriptor(
            ContainsHeader=True,
            Delimiter=","
        )
    )
    
    s3_config = lookoutmetrics.S3SourceConfig(
        FileFormatDescriptor=file_format,
        RoleArn=s3_role_arn
    )
    
    metric_source = lookoutmetrics.MetricSource(
        S3SourceConfig=s3_config
    )
    
    metric_set = lookoutmetrics.MetricSet(
        MetricSetName=metric_set_name,
        MetricList=[metric],
        MetricSource=metric_source
    )
    
    # Verify nested structure is preserved
    metric_dict = metric_set.to_dict(validation=False)
    assert metric_dict["MetricSetName"] == metric_set_name
    assert len(metric_dict["MetricList"]) == 1
    assert metric_dict["MetricList"][0]["MetricName"] == metric_name
    assert metric_dict["MetricSource"]["S3SourceConfig"]["RoleArn"] == s3_role_arn


# Test 8: Alert sensitivity threshold bounds
@given(threshold=st.integers(min_value=-1000, max_value=1000))
def test_alert_sensitivity_threshold_integer_validation(threshold):
    """AlertSensitivityThreshold should use integer validator"""
    action = lookoutmetrics.Action(
        SNSConfiguration=lookoutmetrics.SNSConfiguration(
            RoleArn="test-role",
            SnsTopicArn="test-topic"
        )
    )
    
    alert = lookoutmetrics.Alert(
        "TestAlert",
        Action=action,
        AlertSensitivityThreshold=threshold,
        AnomalyDetectorArn="test-arn"
    )
    
    # Should accept any integer value
    alert_dict = alert.to_dict(validation=False)
    assert alert_dict["Properties"]["AlertSensitivityThreshold"] == threshold


if __name__ == "__main__":
    pytest.main([__file__, "-v"])