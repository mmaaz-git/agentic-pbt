#!/usr/bin/env python3
"""Advanced property-based tests for troposphere.lightsail module"""

import sys
import json

# Add the environment packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from hypothesis.strategies import composite
import troposphere.lightsail as lightsail
from troposphere import Tags, Ref, GetAtt
from troposphere.validators import boolean, double, integer

# Test round-trip serialization
@given(
    bucket_name=st.text(min_size=3, max_size=63, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-"),
    bundle_id=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz_0123456789"),
    object_versioning=st.booleans()
)
def test_bucket_round_trip(bucket_name, bundle_id, object_versioning):
    """Test round-trip from_dict(to_dict()) for Bucket"""
    # Ensure bucket name doesn't start or end with dash and doesn't have consecutive dots
    assume(not bucket_name.startswith("-") and not bucket_name.endswith("-"))
    assume(".." not in bucket_name)
    
    bucket = lightsail.Bucket(
        title="TestBucket",
        BucketName=bucket_name,
        BundleId=bundle_id,
        ObjectVersioning=object_versioning
    )
    
    # Convert to dict and back
    bucket_dict = bucket.to_dict()
    new_bucket = lightsail.Bucket.from_dict("TestBucket", bucket_dict["Properties"])
    
    # Should be equal
    assert new_bucket.to_dict() == bucket_dict

# Test property type validation
@given(invalid_value=st.one_of(
    st.text(),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
def test_integer_property_type_validation(invalid_value):
    """Setting non-integer to integer property should handle properly"""
    assume(not isinstance(invalid_value, (int, bool)))  # These would be valid
    
    endpoint = lightsail.PublicEndpoint()
    try:
        endpoint.ContainerPort = invalid_value
        # If it didn't raise, check if value was converted
        if hasattr(endpoint, 'ContainerPort'):
            # Try to convert to int - should work if assignment succeeded
            int(endpoint.ContainerPort)
    except (TypeError, ValueError):
        # Expected for invalid types
        pass

# Test AccessRules with various combinations
@given(
    allow_public=st.booleans(),
    get_object=st.sampled_from(["private", "public-read"])
)
def test_access_rules_properties(allow_public, get_object):
    """AccessRules should accept valid property combinations"""
    rules = lightsail.AccessRules()
    rules.AllowPublicOverrides = allow_public
    rules.GetObject = get_object
    
    bucket = lightsail.Bucket(
        title="TestBucket",
        BucketName="test-bucket",
        BundleId="small_1_0",
        AccessRules=rules
    )
    
    result = bucket.to_dict()
    assert result["Properties"]["AccessRules"]["AllowPublicOverrides"] == allow_public
    assert result["Properties"]["AccessRules"]["GetObject"] == get_object

# Test HealthCheckConfig edge cases
@given(
    healthy=st.integers(min_value=2, max_value=10),
    unhealthy=st.integers(min_value=2, max_value=10),
    path=st.text(min_size=0, max_size=2048)
)
def test_health_check_with_path(healthy, unhealthy, path):
    """HealthCheckConfig should handle various path formats"""
    config = lightsail.HealthCheckConfig()
    config.HealthyThreshold = healthy
    config.UnhealthyThreshold = unhealthy
    config.Path = path
    
    # Should accept any string for path
    assert config.Path == path

# Test Container with nested properties
@given(
    container_names=st.lists(
        st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-"),
        min_size=1,
        max_size=5,
        unique=True
    ),
    scale=st.integers(min_value=1, max_value=20)
)
def test_container_nested_properties(container_names, scale):
    """Container should handle nested container properties"""
    containers = []
    for name in container_names:
        container_prop = lightsail.ContainerProperty()
        container_prop.ContainerName = name
        container_prop.Image = f"nginx:latest"
        containers.append(container_prop)
    
    deployment = lightsail.ContainerServiceDeployment()
    deployment.Containers = containers
    
    container_service = lightsail.Container(
        title="TestContainer",
        Power="nano",
        Scale=scale,
        ServiceName="test-service",
        ContainerServiceDeployment=deployment
    )
    
    result = container_service.to_dict()
    assert len(result["Properties"]["ContainerServiceDeployment"]["Containers"]) == len(container_names)
    assert result["Properties"]["Scale"] == scale

# Test Database parameter validation
@given(
    param_name=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz_"),
    param_value=st.text(min_size=0, max_size=1000),
    is_modifiable=st.booleans()
)
def test_database_parameter_properties(param_name, param_value, is_modifiable):
    """RelationalDatabaseParameter should accept various configurations"""
    param = lightsail.RelationalDatabaseParameter()
    param.ParameterName = param_name
    param.ParameterValue = param_value
    param.IsModifiable = is_modifiable
    
    db = lightsail.Database(
        title="TestDB",
        MasterDatabaseName="testdb",
        MasterUsername="admin",
        RelationalDatabaseBlueprintId="mysql_8_0",
        RelationalDatabaseBundleId="micro_2_0",
        RelationalDatabaseName="mydb",
        RelationalDatabaseParameters=[param]
    )
    
    result = db.to_dict()
    params = result["Properties"]["RelationalDatabaseParameters"]
    assert len(params) == 1
    assert params[0]["ParameterName"] == param_name
    assert params[0]["ParameterValue"] == param_value
    assert params[0]["IsModifiable"] == is_modifiable

# Test LoadBalancer session stickiness
@given(
    enabled=st.booleans(),
    duration=st.integers(min_value=1, max_value=604800)  # 1 second to 7 days
)
def test_load_balancer_session_stickiness(enabled, duration):
    """LoadBalancer session stickiness should accept valid durations"""
    lb = lightsail.LoadBalancer(
        title="TestLB",
        LoadBalancerName="mylb",
        InstancePort=80,
        SessionStickinessEnabled=enabled,
        SessionStickinessLBCookieDurationSeconds=str(duration)
    )
    
    result = lb.to_dict()
    assert result["Properties"]["SessionStickinessEnabled"] == enabled
    assert result["Properties"]["SessionStickinessLBCookieDurationSeconds"] == str(duration)

# Test Port CIDR lists
@given(
    cidrs=st.lists(
        st.text(min_size=7, max_size=18).filter(
            lambda x: all(c in "0123456789./" for c in x)
        ),
        min_size=0,
        max_size=10
    )
)
def test_port_cidr_lists(cidrs):
    """Port should accept CIDR lists"""
    # Filter to make valid-looking CIDRs
    valid_cidrs = []
    for cidr in cidrs:
        parts = cidr.split(".")
        if len(parts) >= 4 and "/" in cidr:
            valid_cidrs.append(cidr)
    
    port = lightsail.Port()
    port.Cidrs = valid_cidrs
    assert port.Cidrs == valid_cidrs

# Test Distribution cache settings
@given(
    default_ttl=st.integers(min_value=0, max_value=31536000),
    minimum_ttl=st.integers(min_value=0, max_value=31536000),
    maximum_ttl=st.integers(min_value=0, max_value=31536000)
)
def test_distribution_cache_ttl(default_ttl, minimum_ttl, maximum_ttl):
    """CacheSettings TTL values should be accepted"""
    # Ensure logical constraints
    assume(minimum_ttl <= default_ttl <= maximum_ttl)
    
    settings = lightsail.CacheSettings()
    settings.DefaultTTL = default_ttl
    settings.MinimumTTL = minimum_ttl
    settings.MaximumTTL = maximum_ttl
    
    assert settings.DefaultTTL == default_ttl
    assert settings.MinimumTTL == minimum_ttl
    assert settings.MaximumTTL == maximum_ttl

# Test Instance hardware disk properties
@given(
    disk_names=st.lists(
        st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789-"),
        min_size=1,
        max_size=5,
        unique=True
    ),
    paths=st.lists(
        st.text(min_size=1, max_size=100),
        min_size=1,
        max_size=5
    )
)
def test_instance_hardware_disks(disk_names, paths):
    """Hardware should accept multiple disk configurations"""
    # Make sure we have same number of paths as disk names
    paths = paths[:len(disk_names)]
    if len(paths) < len(disk_names):
        paths.extend([f"/dev/xvd{chr(97+i)}" for i in range(len(disk_names) - len(paths))])
    
    disks = []
    for name, path in zip(disk_names, paths):
        disk = lightsail.DiskProperty()
        disk.DiskName = name
        disk.Path = path
        disks.append(disk)
    
    hardware = lightsail.Hardware()
    hardware.Disks = disks
    
    assert len(hardware.Disks) == len(disk_names)
    for i, disk in enumerate(hardware.Disks):
        assert disk.DiskName == disk_names[i]
        assert disk.Path == paths[i]

# Test edge case: empty strings for optional properties
def test_empty_strings_in_optional_properties():
    """Optional string properties should accept empty strings"""
    cert = lightsail.Certificate(
        title="TestCert",
        CertificateName="",  # Empty string
        DomainName=""  # Empty string
    )
    
    # Should accept empty strings
    assert cert.CertificateName == ""
    assert cert.DomainName == ""
    
    # Should be able to convert to dict
    result = cert.to_dict()
    assert result["Properties"]["CertificateName"] == ""
    assert result["Properties"]["DomainName"] == ""

# Test Ref and GetAtt helper functions
def test_resource_references():
    """Resources should support Ref and GetAtt functions"""
    instance = lightsail.Instance(
        title="MyInstance",
        BlueprintId="amazon_linux_2",
        BundleId="nano_2_0",
        InstanceName="test"
    )
    
    # Test Ref
    ref = instance.ref()
    assert isinstance(ref, Ref)
    ref_dict = ref.to_dict()
    assert ref_dict == {"Ref": "MyInstance"}
    
    # Test GetAtt
    get_att = instance.get_att("PublicIpAddress")
    assert isinstance(get_att, GetAtt)
    get_att_dict = get_att.to_dict()
    assert get_att_dict == {"Fn::GetAtt": ["MyInstance", "PublicIpAddress"]}

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])