#!/usr/bin/env python3
"""Property-based tests for troposphere.lightsail module"""

import sys
import math
import random
import string
from datetime import datetime

# Add the environment packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import troposphere.lightsail as lightsail
from troposphere import Tags
from troposphere.validators import boolean, double, integer

# Test 1: Integer validator properties
@given(st.integers())
def test_integer_validator_accepts_valid_integers(x):
    """The integer validator should accept all integers"""
    result = integer(x)
    # Should not raise an exception and should return the input
    assert result == x

@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_validator_with_float_strings(x):
    """Integer validator should accept string representations of integers"""
    if x == int(x):  # If it's actually an integer value
        result = integer(str(int(x)))
        assert int(result) == int(x)

# Test 2: Boolean validator properties
@given(st.sampled_from([True, False, 1, 0, "true", "True", "false", "False"]))
def test_boolean_validator_accepts_valid_booleans(x):
    """Boolean validator should accept valid boolean representations"""
    result = boolean(x)
    assert isinstance(result, bool)
    if x in [True, 1, "true", "True"]:
        assert result is True
    else:
        assert result is False

# Test 3: Double validator properties
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_double_validator_accepts_floats(x):
    """Double validator should accept all finite floats"""
    result = double(x)
    assert result == x

# Test 4: Port range validation
@given(st.integers(min_value=0, max_value=65535))
def test_port_valid_range(port):
    """Port fields should accept valid port numbers"""
    p = lightsail.Port()
    p.FromPort = port
    p.ToPort = port
    assert p.FromPort == port
    assert p.ToPort == port

# Test 5: Required properties validation
@given(
    alarm_name=st.text(min_size=1, max_size=50, alphabet=string.ascii_letters + string.digits),
    comparison_operator=st.sampled_from(["GreaterThanThreshold", "LessThanThreshold", "GreaterThanOrEqualToThreshold", "LessThanOrEqualToThreshold"]),
    evaluation_periods=st.integers(min_value=1, max_value=100),
    metric_name=st.text(min_size=1, max_size=50, alphabet=string.ascii_letters),
    monitored_resource_name=st.text(min_size=1, max_size=50, alphabet=string.ascii_letters),
    threshold=st.floats(min_value=0.1, max_value=1000000, allow_nan=False, allow_infinity=False)
)
def test_alarm_required_properties(alarm_name, comparison_operator, evaluation_periods, metric_name, monitored_resource_name, threshold):
    """Alarm with all required properties should create valid dict"""
    alarm = lightsail.Alarm(
        title="TestAlarm",
        AlarmName=alarm_name,
        ComparisonOperator=comparison_operator,
        EvaluationPeriods=evaluation_periods,
        MetricName=metric_name,
        MonitoredResourceName=monitored_resource_name,
        Threshold=threshold
    )
    result = alarm.to_dict()
    assert result["Type"] == "AWS::Lightsail::Alarm"
    assert result["Properties"]["AlarmName"] == alarm_name
    assert result["Properties"]["Threshold"] == threshold

# Test 6: Instance hardware properties
@given(
    cpu_count=st.integers(min_value=1, max_value=96),
    ram_size=st.integers(min_value=1, max_value=768)
)
def test_hardware_properties(cpu_count, ram_size):
    """Hardware properties should accept valid values"""
    hw = lightsail.Hardware()
    hw.CpuCount = cpu_count
    hw.RamSizeInGb = ram_size
    
    assert hw.CpuCount == cpu_count
    assert hw.RamSizeInGb == ram_size

# Test 7: Container port property
@given(port=st.integers(min_value=1, max_value=65535))
def test_container_port_property(port):
    """Container PublicEndpoint should handle valid ports"""
    endpoint = lightsail.PublicEndpoint()
    endpoint.ContainerPort = port
    assert endpoint.ContainerPort == port

# Test 8: Health check config integer properties
@given(
    healthy_threshold=st.integers(min_value=2, max_value=10),
    unhealthy_threshold=st.integers(min_value=2, max_value=10),
    timeout_seconds=st.integers(min_value=2, max_value=60),
    interval_seconds=st.integers(min_value=5, max_value=300)
)
def test_health_check_config_integers(healthy_threshold, unhealthy_threshold, timeout_seconds, interval_seconds):
    """HealthCheckConfig should accept valid integer thresholds"""
    config = lightsail.HealthCheckConfig()
    config.HealthyThreshold = healthy_threshold
    config.UnhealthyThreshold = unhealthy_threshold
    config.TimeoutSeconds = timeout_seconds
    config.IntervalSeconds = interval_seconds
    
    assert config.HealthyThreshold == healthy_threshold
    assert config.UnhealthyThreshold == unhealthy_threshold
    assert config.TimeoutSeconds == timeout_seconds
    assert config.IntervalSeconds == interval_seconds

# Test 9: Database backup retention boolean
@given(backup_retention=st.booleans())
def test_database_backup_retention(backup_retention):
    """Database BackupRetention should accept boolean values"""
    # Need all required properties
    db = lightsail.Database(
        title="TestDB",
        MasterDatabaseName="testdb",
        MasterUsername="admin",
        RelationalDatabaseBlueprintId="mysql_8_0",
        RelationalDatabaseBundleId="micro_2_0",
        RelationalDatabaseName="mydb"
    )
    db.BackupRetention = backup_retention
    assert db.BackupRetention == backup_retention

# Test 10: Certificate domain names list property
@given(domain_names=st.lists(
    st.text(min_size=1, max_size=50, alphabet=string.ascii_lowercase + string.digits + ".-"),
    min_size=0,
    max_size=10
))
def test_certificate_subject_alternative_names(domain_names):
    """Certificate should accept list of domain names"""
    cert = lightsail.Certificate(
        title="TestCert",
        CertificateName="mycert",
        DomainName="example.com"
    )
    cert.SubjectAlternativeNames = domain_names
    assert cert.SubjectAlternativeNames == domain_names

# Test 11: Tags property (common across many resources)
@given(
    tag_keys=st.lists(
        st.text(min_size=1, max_size=50, alphabet=string.ascii_letters),
        min_size=1,
        max_size=10,
        unique=True
    )
)
def test_tags_property(tag_keys):
    """Resources should accept Tags objects"""
    # Tags takes a dict in constructor
    tags_dict = {key: f"value-{key}" for key in tag_keys}
    tags = Tags(**tags_dict)
    
    instance = lightsail.Instance(
        title="TestInstance",
        BlueprintId="amazon_linux_2",
        BundleId="nano_2_0",
        InstanceName="test"
    )
    instance.Tags = tags
    assert instance.Tags == tags

# Test 12: Disk size property
@given(size_gb=st.integers(min_value=8, max_value=16384))
def test_disk_size_property(size_gb):
    """Disk SizeInGb should accept valid sizes"""
    disk = lightsail.Disk(
        title="TestDisk",
        DiskName="mydisk",
        SizeInGb=size_gb
    )
    assert disk.SizeInGb == size_gb
    result = disk.to_dict()
    assert result["Properties"]["SizeInGb"] == size_gb

# Test 13: Resource type format
def test_resource_types():
    """All resource classes should have proper resource_type format"""
    resource_classes = [
        lightsail.Alarm,
        lightsail.Bucket, 
        lightsail.Certificate,
        lightsail.Container,
        lightsail.Database,
        lightsail.Disk,
        lightsail.Distribution,
        lightsail.Instance,
        lightsail.InstanceSnapshot,
        lightsail.LoadBalancer,
        lightsail.LoadBalancerTlsCertificate,
        lightsail.StaticIp
    ]
    
    for cls in resource_classes:
        assert hasattr(cls, 'resource_type')
        assert cls.resource_type.startswith("AWS::Lightsail::")
        # Check it matches the expected pattern
        parts = cls.resource_type.split("::")
        assert len(parts) == 3
        assert parts[0] == "AWS"
        assert parts[1] == "Lightsail"

# Test 14: Property object creation without title
def test_property_objects_optional_title():
    """AWSProperty objects should work without title"""
    props = [
        lightsail.AccessRules(),
        lightsail.EnvironmentVariable(),
        lightsail.PortInfo(),
        lightsail.HealthCheckConfig(),
        lightsail.PublicEndpoint(),
        lightsail.Location(),
        lightsail.Hardware()
    ]
    for prop in props:
        # Should not raise exception
        assert prop.title is None

# Test 15: Integer list properties
@given(
    instances=st.lists(
        st.text(min_size=1, max_size=50, alphabet=string.ascii_letters),
        min_size=0,
        max_size=10
    )
)
def test_load_balancer_attached_instances(instances):
    """LoadBalancer should accept list of instance names"""
    lb = lightsail.LoadBalancer(
        title="TestLB",
        LoadBalancerName="mylb",
        InstancePort=80
    )
    lb.AttachedInstances = instances
    assert lb.AttachedInstances == instances

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])