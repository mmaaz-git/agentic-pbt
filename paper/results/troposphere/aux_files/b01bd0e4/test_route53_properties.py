"""
Property-based tests for troposphere.route53 module
Testing for round-trip properties, serialization consistency, and validation behavior
"""

import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.route53 as r53
from troposphere.validators import integer, boolean
import math


# Strategy for valid DNS names
dns_names = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-.",
    min_size=1,
    max_size=253
).filter(lambda x: not x.startswith('-') and not x.endswith('-') and '..' not in x)

# Strategy for record types
record_types = st.sampled_from(['A', 'AAAA', 'CAA', 'CNAME', 'MX', 'NS', 'PTR', 'SOA', 'SPF', 'SRV', 'TXT'])

# Strategy for TTL values as strings
ttl_values = st.integers(min_value=0, max_value=2147483647).map(str)

# Strategy for IP addresses (simplified)
ip_addresses = st.lists(
    st.tuples(
        st.integers(0, 255),
        st.integers(0, 255),
        st.integers(0, 255),
        st.integers(0, 255)
    ).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}.{t[3]}"),
    min_size=1,
    max_size=5
)


@given(
    name=dns_names,
    record_type=record_types,
    ttl=ttl_values,
    records=ip_addresses
)
def test_recordset_round_trip(name, record_type, ttl, records):
    """Test that RecordSet survives to_dict -> from_dict round trip"""
    # Create a RecordSet
    rs1 = r53.RecordSet(
        Name=name,
        Type=record_type,
        TTL=ttl,
        ResourceRecords=records
    )
    
    # Convert to dict
    dict1 = rs1.to_dict()
    
    # Create from dict
    rs2 = r53.RecordSet.from_dict('TestRecord', dict1)
    dict2 = rs2.to_dict()
    
    # Property: round-trip should preserve data
    assert dict1 == dict2


@given(
    name=dns_names,
    record_type=record_types,
    ttl=st.one_of(st.none(), ttl_values),
    weight=st.one_of(st.none(), st.integers(0, 255)),
    set_identifier=st.one_of(st.none(), st.text(min_size=1, max_size=128))
)
def test_recordset_json_serialization(name, record_type, ttl, weight, set_identifier):
    """Test that JSON serialization is consistent with to_dict"""
    kwargs = {'Name': name, 'Type': record_type}
    if ttl is not None:
        kwargs['TTL'] = ttl
    if weight is not None:
        kwargs['Weight'] = weight
    if set_identifier is not None:
        kwargs['SetIdentifier'] = set_identifier
    
    rs = r53.RecordSet(**kwargs)
    
    # Get dict and JSON representations
    dict_repr = rs.to_dict()
    json_str = rs.to_json()
    json_parsed = json.loads(json_str)
    
    # Property: JSON serialization should match dict representation
    assert dict_repr == json_parsed


@given(
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text()
    )
)
def test_integer_validator_consistency(value):
    """Test that integer validator behaves consistently"""
    try:
        result1 = integer(value)
        # If it succeeds once, it should succeed again with same result
        result2 = integer(value)
        assert result1 == result2
        
        # If it's a string representation of integer, it should stay string
        if isinstance(value, str):
            assert isinstance(result1, str)
        # Actual integers and floats pass through
        elif isinstance(value, (int, float)):
            assert result1 == value
    except (ValueError, TypeError) as e:
        # If it fails once, it should fail consistently
        try:
            integer(value)
            assert False, "Should have raised an error consistently"
        except (ValueError, TypeError):
            pass


@given(
    value=st.one_of(
        st.booleans(),
        st.sampled_from(['true', 'false', 'True', 'False', 'yes', 'no', 'Yes', 'No']),
        st.integers(0, 1),
        st.text()
    )
)
def test_boolean_validator_behavior(value):
    """Test boolean validator accepts various representations"""
    try:
        result = boolean(value)
        # Property: boolean validator should return actual boolean values
        assert isinstance(result, bool)
        
        # Test consistency
        result2 = boolean(value)
        assert result == result2
        
        # Test known conversions
        if value in [True, 'true', 'True', 'yes', 'Yes', 1]:
            assert result is True
        elif value in [False, 'false', 'False', 'no', 'No', 0]:
            assert result is False
    except (ValueError, TypeError):
        # For invalid inputs, should consistently fail
        try:
            boolean(value)
            assert False, "Should have raised an error consistently"
        except (ValueError, TypeError):
            pass


@given(
    weight_value=st.one_of(
        st.integers(0, 255),
        st.integers(0, 255).map(str),
        st.floats(min_value=0, max_value=255).filter(lambda x: x == int(x))
    )
)
def test_recordset_weight_type_handling(weight_value):
    """Test how RecordSet handles different types for Weight field"""
    # Weight is defined as integer type in props
    rs = r53.RecordSet(
        Name='test.example.com',
        Type='A',
        Weight=weight_value
    )
    
    dict_repr = rs.to_dict()
    weight_in_dict = dict_repr.get('Weight')
    
    # Property: Weight should be preserved (as string or number)
    if isinstance(weight_value, str):
        assert weight_in_dict == weight_value
    else:
        # Integer or float values might be converted
        assert weight_in_dict == weight_value or str(weight_in_dict) == str(int(weight_value))


@given(
    name=dns_names,
    hosted_zone_name=dns_names
)
def test_hosted_zone_configuration(name, hosted_zone_name):
    """Test HostedZone with configuration"""
    # Create with optional configuration
    config = r53.HostedZoneConfiguration(
        Comment=f"Test zone for {name}"
    )
    
    hz = r53.HostedZone(
        title='TestZone',
        Name=hosted_zone_name,
        HostedZoneConfig=config
    )
    
    dict_repr = hz.to_dict()
    
    # Property: Name should be preserved
    assert dict_repr['Name'] == hosted_zone_name
    
    # Property: Configuration should be serialized
    if 'HostedZoneConfig' in dict_repr:
        assert 'Comment' in dict_repr['HostedZoneConfig']


@given(
    continent_code=st.sampled_from(['AF', 'AN', 'AS', 'EU', 'OC', 'NA', 'SA', None]),
    country_code=st.one_of(st.none(), st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ', min_size=2, max_size=2)),
    subdivision_code=st.one_of(st.none(), st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=3))
)
def test_geolocation_validation(continent_code, country_code, subdivision_code):
    """Test GeoLocation accepts valid geographic codes"""
    kwargs = {}
    if continent_code:
        kwargs['ContinentCode'] = continent_code
    if country_code:
        kwargs['CountryCode'] = country_code
    if subdivision_code:
        kwargs['SubdivisionCode'] = subdivision_code
    
    # Should not raise for valid inputs
    if kwargs:  # Only create if we have at least one field
        geo = r53.GeoLocation(**kwargs)
        dict_repr = geo.to_dict()
        
        # Property: All provided fields should be in output
        for key, value in kwargs.items():
            assert key in dict_repr
            assert dict_repr[key] == value


@given(
    eval_target_health=st.one_of(
        st.booleans(),
        st.sampled_from(['true', 'false', 'True', 'False'])
    ),
    dns_name=dns_names,
    hosted_zone_id=st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=32)
)
def test_alias_target_boolean_handling(eval_target_health, dns_name, hosted_zone_id):
    """Test AliasTarget handles boolean EvaluateTargetHealth correctly"""
    alias = r53.AliasTarget(
        hostedzoneid=hosted_zone_id,
        dnsname=dns_name,
        evaluatetargethealth=eval_target_health
    )
    
    dict_repr = alias.to_dict()
    
    # Property: All fields should be present
    assert 'HostedZoneId' in dict_repr
    assert 'DNSName' in dict_repr
    
    # EvaluateTargetHealth handling depends on the validator
    if 'EvaluateTargetHealth' in dict_repr:
        eth = dict_repr['EvaluateTargetHealth']
        # Should be a boolean value
        assert isinstance(eth, bool)


@given(
    ipaddress=st.text(min_size=1, max_size=45),  # IPv4 or IPv6
    port=st.integers(1, 65535),
    protocol=st.sampled_from(['HTTP', 'HTTPS', 'TCP', 'CALCULATED']),
    resource_path=st.text(min_size=0, max_size=255)
)
def test_health_check_config(ipaddress, port, protocol, resource_path):
    """Test HealthCheckConfig validation"""
    config = r53.HealthCheckConfig(
        IPAddress=ipaddress,
        Port=port,
        Type=protocol,
        ResourcePath=resource_path if resource_path else None
    )
    
    dict_repr = config.to_dict()
    
    # Property: Required fields should be present
    assert 'IPAddress' in dict_repr
    assert 'Port' in dict_repr
    assert 'Type' in dict_repr
    
    # Property: Values should be preserved
    assert dict_repr['IPAddress'] == ipaddress
    assert dict_repr['Port'] == port
    assert dict_repr['Type'] == protocol


if __name__ == '__main__':
    # Run with pytest
    import pytest
    import sys
    
    # Run tests with higher example count for better coverage
    pytest.main([__file__, '-v', '--tb=short'])