"""Property-based tests for troposphere.codedeploy module."""

import pytest
from hypothesis import given, strategies as st, assume
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import codedeploy
from troposphere.validators.codedeploy import (
    deployment_option_validator, 
    deployment_type_validator,
    validate_load_balancer_info,
    validate_deployment_group
)
from troposphere.validators import boolean, integer


# Test 1: deployment_option_validator should only accept valid values
@given(st.text())
def test_deployment_option_validator_invalid_input(value):
    """deployment_option_validator should reject anything other than the two valid options."""
    assume(value not in ["WITH_TRAFFIC_CONTROL", "WITHOUT_TRAFFIC_CONTROL"])
    with pytest.raises(ValueError, match="Deployment Option value must be one of"):
        deployment_option_validator(value)


# Test 2: deployment_type_validator should only accept valid values  
@given(st.text())
def test_deployment_type_validator_invalid_input(value):
    """deployment_type_validator should reject anything other than the two valid options."""
    assume(value not in ["IN_PLACE", "BLUE_GREEN"])
    with pytest.raises(ValueError, match="Deployment Type value must be one of"):
        deployment_type_validator(value)


# Test 3: boolean validator property - should handle various representations correctly
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_validator_valid_inputs(value):
    """Boolean validator should correctly convert valid boolean representations."""
    result = boolean(value)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


# Test 4: integer validator should accept valid integers
@given(st.integers())
def test_integer_validator_with_integers(value):
    """Integer validator should accept any integer."""
    result = integer(value)
    assert result == value


# Test 5: integer validator should accept string representations of integers
@given(st.integers())
def test_integer_validator_with_string_integers(value):
    """Integer validator should accept string representations of integers."""
    str_value = str(value)
    result = integer(str_value)
    assert result == str_value
    # Should be convertible back to int
    assert int(result) == value


# Test 6: LoadBalancerInfo exactly_one constraint
def test_load_balancer_info_exactly_one():
    """LoadBalancerInfo should have exactly one of the three list types."""
    # Test with none - should raise
    lb = codedeploy.LoadBalancerInfo()
    with pytest.raises(ValueError, match="one of the following must be specified"):
        lb.validate()
    
    # Test with multiple - should raise
    lb = codedeploy.LoadBalancerInfo(
        ElbInfoList=[codedeploy.ElbInfoList(Name="elb1")],
        TargetGroupInfoList=[codedeploy.TargetGroupInfo(Name="tg1")]
    )
    with pytest.raises(ValueError, match="only one of the following can be specified"):
        lb.validate()
    
    # Test with exactly one - should pass
    lb = codedeploy.LoadBalancerInfo(
        ElbInfoList=[codedeploy.ElbInfoList(Name="elb1")]
    )
    lb.validate()  # Should not raise


# Test 7: DeploymentGroup mutually exclusive properties
@given(
    st.booleans(),
    st.booleans(),
    st.booleans(),
    st.booleans()
)
def test_deployment_group_mutually_exclusive(has_ec2_filters, has_ec2_set, has_on_prem_filters, has_on_prem_set):
    """DeploymentGroup should enforce mutual exclusivity constraints."""
    kwargs = {
        "ApplicationName": "TestApp",
        "ServiceRoleArn": "arn:aws:iam::123456789012:role/CodeDeployRole"
    }
    
    if has_ec2_filters:
        kwargs["Ec2TagFilters"] = [codedeploy.Ec2TagFilters(Key="Name", Value="Test")]
    if has_ec2_set:
        kwargs["Ec2TagSet"] = codedeploy.Ec2TagSet()
    if has_on_prem_filters:
        kwargs["OnPremisesInstanceTagFilters"] = [codedeploy.OnPremisesInstanceTagFilters(Key="Name", Value="Test")]
    if has_on_prem_set:
        kwargs["OnPremisesTagSet"] = codedeploy.OnPremisesTagSet()
    
    dg = codedeploy.DeploymentGroup("TestDG", **kwargs)
    
    # Check if we expect validation to fail
    should_fail = (has_ec2_filters and has_ec2_set) or (has_on_prem_filters and has_on_prem_set)
    
    if should_fail:
        with pytest.raises(ValueError, match="only one of the following can be specified"):
            dg.validate()
    else:
        dg.validate()  # Should not raise


# Test 8: MinimumHealthyHosts required properties
def test_minimum_healthy_hosts_required_properties():
    """MinimumHealthyHosts should require Type and Value properties."""
    # Missing both required properties
    with pytest.raises(ValueError, match="Resource Type required"):
        mhh = codedeploy.MinimumHealthyHosts()
        mhh.to_dict()
    
    # Missing Value property
    with pytest.raises(ValueError, match="Resource Value required"):
        mhh = codedeploy.MinimumHealthyHosts(Type="FLEET_PERCENT")
        mhh.to_dict()
    
    # Both properties present
    mhh = codedeploy.MinimumHealthyHosts(Type="FLEET_PERCENT", Value=50)
    result = mhh.to_dict()
    assert result == {"Type": "FLEET_PERCENT", "Value": 50}


# Test 9: Round-trip property for simple objects
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),  # Valid CloudFormation names
    st.text(min_size=1, max_size=100),
    st.one_of(st.sampled_from(["Server", "Lambda", "ECS"]), st.none())
)
def test_application_round_trip(name, app_name, platform):
    """Application objects should survive round-trip to_dict/from_dict."""
    kwargs = {"ApplicationName": app_name}
    if platform is not None:
        kwargs["ComputePlatform"] = platform
    
    app1 = codedeploy.Application(name, **kwargs)
    dict1 = app1.to_dict()
    
    # Extract properties from the dict
    props = dict1.get("Properties", {})
    app2 = codedeploy.Application.from_dict(name, props)
    dict2 = app2.to_dict()
    
    assert dict1 == dict2


# Test 10: S3Location round-trip with all properties
@given(
    st.text(min_size=1, max_size=50),  # Bucket
    st.text(min_size=1, max_size=100),  # Key
    st.one_of(st.sampled_from(["zip", "tar", "tgz", "YAML", "JSON"]), st.none()),  # BundleType
    st.one_of(st.text(min_size=1, max_size=50), st.none()),  # ETag
    st.one_of(st.text(min_size=1, max_size=50), st.none())  # Version
)
def test_s3_location_round_trip(bucket, key, bundle_type, etag, version):
    """S3Location should preserve all properties in round-trip."""
    kwargs = {"Bucket": bucket, "Key": key}
    if bundle_type:
        kwargs["BundleType"] = bundle_type
    if etag:
        kwargs["ETag"] = etag
    if version:
        kwargs["Version"] = version
    
    s3_1 = codedeploy.S3Location(**kwargs)
    dict1 = s3_1.to_dict()
    
    # S3Location is an AWSProperty, so we can create a new one from the dict
    s3_2 = codedeploy.S3Location(**dict1)
    dict2 = s3_2.to_dict()
    
    assert dict1 == dict2


# Test 11: Test property type validation
@given(st.one_of(st.floats(), st.text(), st.lists(st.integers())))
def test_integer_property_type_checking(invalid_value):
    """Integer properties should reject non-integer values."""
    assume(not isinstance(invalid_value, int))
    assume(not (isinstance(invalid_value, str) and invalid_value.lstrip('-').isdigit()))
    
    # TimeBasedCanary requires integer values
    with pytest.raises((TypeError, ValueError)):
        tbc = codedeploy.TimeBasedCanary(
            CanaryInterval=invalid_value,  
            CanaryPercentage=50
        )
        tbc.to_dict()