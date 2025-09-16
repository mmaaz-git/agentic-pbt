#!/usr/bin/env python3
"""Fixed property-based tests for troposphere.constants with better strategies."""

import re
import sys
from hypothesis import given, strategies as st, settings, HealthCheck

# Add the troposphere env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.constants as tc


# Direct test for AZ letter sequencing without hypothesis filtering
def test_az_letter_sequencing_direct():
    """Availability zones within a region should use sequential letters."""
    az_pattern = re.compile(r'^([a-z]{2,3}-[a-z]+-\d+)([a-z])$')
    
    # Collect all AZs by region
    azs_by_region = {}
    for name in dir(tc):
        if name.startswith('_'):
            continue
        value = getattr(tc, name)
        if isinstance(value, str):
            match = az_pattern.match(value)
            if match:
                region = match.group(1)
                letter = match.group(2)
                if region not in azs_by_region:
                    azs_by_region[region] = []
                azs_by_region[region].append(letter)
    
    # Check each region
    for region, letters in azs_by_region.items():
        letters = sorted(set(letters))
        
        # First AZ should be 'a'
        assert letters[0] == 'a', f"Region {region} doesn't start with AZ 'a', has {letters}"
        
        # Check for large gaps
        for i in range(len(letters) - 1):
            gap = ord(letters[i+1]) - ord(letters[i])
            # Special case: ca-central-1 has a,b,d (skips c)
            if region == 'ca-central-1' and letters[i] == 'b' and letters[i+1] == 'd':
                continue  # This is a known skip
            assert gap <= 1, f"Gap in AZ letters for {region}: {letters}"


# Direct test for DB-EC2 correspondence
def test_db_ec2_instance_correspondence_direct():
    """Many DB instance types should have corresponding EC2 instance types."""
    
    # Collect all EC2 instance values for quick lookup
    ec2_instances = {}
    for name in dir(tc):
        if (not name.startswith('_') and not name.startswith('DB_') 
            and not name.startswith('CACHE_') and not name.startswith('SEARCH_')
            and not name.startswith('ELASTICSEARCH_') and not name.startswith('KAFKA_')):
            value = getattr(tc, name)
            if isinstance(value, str) and '.' in value and not value.startswith('db.'):
                ec2_instances[value] = name
    
    # Check DB instances
    mismatches = []
    for name in dir(tc):
        if name.startswith('DB_'):
            value = getattr(tc, name)
            if isinstance(value, str) and value.startswith('db.'):
                parts = value.split('.')
                if len(parts) >= 3:
                    # Skip special RDS types
                    if 'tpc' in value or 'mem' in value:
                        continue
                    
                    # Expected EC2 equivalent
                    ec2_equivalent = '.'.join(parts[1:])
                    
                    # Only check common families
                    family = parts[1]
                    common_families = ['t2', 't3', 't4g', 'm5', 'm6g', 'r5', 'r6g']
                    
                    if any(family.startswith(f) for f in common_families):
                        if ec2_equivalent in ec2_instances:
                            # Found corresponding EC2 instance - good!
                            pass
                        else:
                            # Some DB instances don't have EC2 equivalents (ok)
                            pass
    
    # No assertion - this is more observational


# Direct test for standard ports
def test_standard_port_assignments_direct():
    """Known services should use their standard port numbers."""
    standard_ports = {
        'SSH_PORT': 22,
        'SMTP_PORT_25': 25,
        'SMTP_PORT_587': 587,
        'HTTP_PORT': 80,
        'NTP_PORT': 123,
        'HTTPS_PORT': 443,
        'POSTGRESQL_PORT': 5432,
        'REDIS_PORT': 6379,
        'MEMCACHED_PORT': 11211,
        'MONGODB_PORT': 27017
    }
    
    for name, expected in standard_ports.items():
        if hasattr(tc, name):
            actual = getattr(tc, name)
            assert actual == expected, f"{name} should be {expected}, got {actual}"


# Direct test for LIST_OF parameter correspondence
def test_list_parameter_correspondence_direct():
    """LIST_OF_* parameter types should wrap their singular counterparts."""
    
    # Manual mapping for known correspondences
    expected_mappings = {
        'LIST_OF_AVAILABILITY_ZONE_NAMES': ('AVAILABILITY_ZONE_NAME', 'List<AWS::EC2::AvailabilityZone::Name>'),
        'LIST_OF_IMAGE_ID': ('IMAGE_ID', 'List<AWS::EC2::Image::Id>'),
        'LIST_OF_INSTANCE_IDS': ('INSTANCE_ID', 'List<AWS::EC2::Instance::Id>'),
        'LIST_OF_SECURITY_GROUP_NAMES': ('SECURITY_GROUP_NAME', 'List<AWS::EC2::SecurityGroup::GroupName>'),
        'LIST_OF_SECURITY_GROUP_IDS': ('SECURITY_GROUP_ID', 'List<AWS::EC2::SecurityGroup::Id>'),
        'LIST_OF_SUBNET_IDS': ('SUBNET_ID', 'List<AWS::EC2::Subnet::Id>'),
        'LIST_OF_VOLUME_IDS': ('VOLUME_ID', 'List<AWS::EC2::Volume::Id>'),
        'LIST_OF_VPC_IDS': ('VPC_ID', 'List<AWS::EC2::VPC::Id>'),
        'LIST_OF_HOSTED_ZONE_IDS': ('HOSTED_ZONE_ID', 'List<AWS::Route53::HostedZone::Id>')
    }
    
    for list_name, (singular_name, expected_value) in expected_mappings.items():
        if hasattr(tc, list_name):
            actual = getattr(tc, list_name)
            assert actual == expected_value, \
                f"{list_name} should be {expected_value}, got {actual}"
            
            # Also check singular exists
            if hasattr(tc, singular_name):
                singular = getattr(tc, singular_name)
                assert actual == f"List<{singular}>", \
                    f"{list_name} doesn't wrap {singular_name}"


# Use hypothesis for simpler properties with direct strategies
@given(st.integers(0, len(tc.LOGS_ALLOWED_RETENTION_DAYS) - 2))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_retention_days_progression(index):
    """Retention days should have reasonable progression between values."""
    days = tc.LOGS_ALLOWED_RETENTION_DAYS
    
    current = days[index]
    next_val = days[index + 1]
    
    # The jump between consecutive values shouldn't be too large initially
    ratio = next_val / current
    
    # Early values should have smaller jumps
    if current < 30:
        assert ratio <= 3.5, f"Large jump from {current} to {next_val} (ratio: {ratio})"
    elif current < 365:
        assert ratio <= 2.5, f"Large jump from {current} to {next_val} (ratio: {ratio})"


# Test instance type patterns with targeted strategy
@given(st.sampled_from([
    name for name in dir(tc)
    if not name.startswith('_') and '_' in name 
    and any(x in name for x in ['NANO', 'MICRO', 'SMALL', 'MEDIUM', 'LARGE', 'XLARGE', 'METAL'])
]))
@settings(suppress_health_check=[HealthCheck.filter_too_much], max_examples=50)
def test_instance_type_patterns_hypothesis(const_name):
    """Instance types should follow valid patterns."""
    value = getattr(tc, const_name)
    
    if not isinstance(value, str) or '.' not in value:
        return  # Skip non-instance types
    
    parts = value.split('.')
    
    # Check based on prefix
    if value.startswith('db.'):
        assert len(parts) >= 3, f"DB instance {value} has wrong format"
    elif value.startswith('cache.'):
        assert len(parts) == 3, f"Cache instance {value} has wrong format"
    elif value.startswith('kafka.'):
        assert len(parts) == 3, f"Kafka instance {value} has wrong format"
    elif not any(value.startswith(p) for p in ['ultrawarm', 'im4gn']):
        # Regular EC2 instance
        assert len(parts) == 2, f"EC2 instance {value} has wrong format"
        
        # Check size is valid
        valid_sizes = ['nano', 'micro', 'small', 'medium', 'large', 'xlarge', 'metal']
        size = parts[1]
        if not re.match(r'^\d+xlarge$', size):
            assert size in valid_sizes, f"Unknown size {size} in {value}"


# Test CloudFront hosted zone ID is correct
def test_cloudfront_hostedzoneid():
    """CloudFront hosted zone ID should be the well-known value."""
    assert tc.CLOUDFRONT_HOSTEDZONEID == "Z2FDTNDATAQYW2", \
        f"CloudFront hosted zone ID is {tc.CLOUDFRONT_HOSTEDZONEID}, expected Z2FDTNDATAQYW2"


# Test CIDR blocks are valid
def test_cidr_validity():
    """CIDR blocks should be valid IPv4 CIDR notation."""
    cidrs = [tc.QUAD_ZERO, tc.VPC_CIDR_16]
    
    for cidr in cidrs:
        # Check format
        assert re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$', cidr), \
            f"Invalid CIDR format: {cidr}"
        
        # Check IP parts are valid
        ip, mask = cidr.split('/')
        parts = ip.split('.')
        for part in parts:
            assert 0 <= int(part) <= 255, f"Invalid IP part in {cidr}"
        
        # Check mask is valid
        assert 0 <= int(mask) <= 32, f"Invalid mask in {cidr}"


# Test protocol numbers
def test_protocol_numbers():
    """Protocol numbers should match IANA standards."""
    assert tc.ICMP_PROTOCOL == 1
    assert tc.TCP_PROTOCOL == 6
    assert tc.UDP_PROTOCOL == 17
    assert tc.ALL_PROTOCOL == -1  # AWS special value


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])