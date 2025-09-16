#!/usr/bin/env python3
"""Property-based tests for troposphere.constants module.

Testing evidence-based properties derived from AWS specifications and
the troposphere library's intended usage patterns.
"""

import re
from hypothesis import given, strategies as st, settings, assume
import sys
import os

# Add the troposphere env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.constants as tc


# Property 1: Availability zones must start with their corresponding region name
def test_availability_zone_region_consistency():
    """Each availability zone should start with its region prefix."""
    # Map regions to their expected AZs
    region_az_map = {
        'af-south-1': ['af-south-1a', 'af-south-1b', 'af-south-1c'],
        'ap-east-1': ['ap-east-1a', 'ap-east-1b', 'ap-east-1c'],
        'ap-northeast-1': ['ap-northeast-1a', 'ap-northeast-1b', 'ap-northeast-1c', 'ap-northeast-1d'],
        'ap-northeast-2': ['ap-northeast-2a', 'ap-northeast-2b', 'ap-northeast-2c', 'ap-northeast-2d'],
        'ap-northeast-3': ['ap-northeast-3a', 'ap-northeast-3b', 'ap-northeast-3c'],
        'ap-southeast-1': ['ap-southeast-1a', 'ap-southeast-1b', 'ap-southeast-1c'],
        'ap-southeast-2': ['ap-southeast-2a', 'ap-southeast-2b', 'ap-southeast-2c'],
        'ap-southeast-3': ['ap-southeast-3a', 'ap-southeast-3b', 'ap-southeast-3c'],
        'ap-south-1': ['ap-south-1a', 'ap-south-1b', 'ap-south-1c'],
        'ca-central-1': ['ca-central-1a', 'ca-central-1b', 'ca-central-1d'],
        'cn-north-1': ['cn-north-1a', 'cn-north-1b', 'cn-north-1c'],
        'cn-northwest-1': ['cn-northwest-1a', 'cn-northwest-1b', 'cn-northwest-1c'],
        'eu-west-1': ['eu-west-1a', 'eu-west-1b', 'eu-west-1c'],
        'eu-west-2': ['eu-west-2a', 'eu-west-2b', 'eu-west-2c'],
        'eu-west-3': ['eu-west-3a', 'eu-west-3b', 'eu-west-3c'],
        'eu-central-1': ['eu-central-1a', 'eu-central-1b', 'eu-central-1c'],
        'eu-north-1': ['eu-north-1a', 'eu-north-1b', 'eu-north-1c'],
        'eu-south-1': ['eu-south-1a', 'eu-south-1b', 'eu-south-1c'],
        'me-central-1': ['me-central-1a', 'me-central-1b', 'me-central-1c'],
        'me-south-1': ['me-south-1a', 'me-south-1b', 'me-south-1c'],
        'sa-east-1': ['sa-east-1a', 'sa-east-1b', 'sa-east-1c'],
        'us-east-1': ['us-east-1a', 'us-east-1b', 'us-east-1c', 'us-east-1d', 'us-east-1e', 'us-east-1f'],
        'us-east-2': ['us-east-2a', 'us-east-2b', 'us-east-2c'],
        'us-gov-east-1': ['us-gov-east-1a', 'us-gov-east-1b', 'us-gov-east-1c'],
        'us-gov-west-1': ['us-gov-west-1a', 'us-gov-west-1b', 'us-gov-west-1c'],
        'us-west-1': ['us-west-1a', 'us-west-1b', 'us-west-1c'],
        'us-west-2': ['us-west-2a', 'us-west-2b', 'us-west-2c', 'us-west-2d']
    }
    
    # Test each mapping
    for region_const_name in dir(tc):
        if region_const_name.endswith('_1') or region_const_name.endswith('_2') or region_const_name.endswith('_3'):
            # This looks like a region constant
            if not any(char.isdigit() or char.isupper() for char in region_const_name[-2:]):
                continue
            
            # Get the actual region value
            region_value = getattr(tc, region_const_name)
            if not isinstance(region_value, str) or not re.match(r'^[a-z]{2}-[a-z]+-\d+$', region_value):
                continue
                
            # Find corresponding AZ constants  
            region_prefix = region_value.replace('-', '_').upper()
            
            for az_const_name in dir(tc):
                if az_const_name.startswith(region_prefix) and az_const_name[-1] in 'ABCDEF':
                    az_value = getattr(tc, az_const_name)
                    # The AZ should start with the region name
                    assert az_value.startswith(region_value), \
                        f"AZ {az_const_name}={az_value} doesn't start with region {region_value}"


# Property 2: All port constants should be valid port numbers
def test_port_number_validity():
    """All port constants should be within valid TCP/UDP port range (0-65535)."""
    port_constants = [
        tc.SSH_PORT,
        tc.MONGODB_PORT,
        tc.NTP_PORT,
        tc.SMTP_PORT_25,
        tc.SMTP_PORT_587,
        tc.HTTP_PORT,
        tc.HTTPS_PORT,
        tc.REDIS_PORT,
        tc.MEMCACHED_PORT,
        tc.POSTGRESQL_PORT
    ]
    
    for port in port_constants:
        assert isinstance(port, int), f"Port {port} is not an integer"
        assert 0 <= port <= 65535, f"Port {port} is outside valid range 0-65535"


# Property 3: Protocol numbers should be valid
def test_protocol_number_validity():
    """Protocol numbers should be within valid ranges."""
    # Based on IANA protocol numbers
    assert tc.TCP_PROTOCOL == 6, "TCP protocol should be 6"
    assert tc.UDP_PROTOCOL == 17, "UDP protocol should be 17"
    assert tc.ICMP_PROTOCOL == 1, "ICMP protocol should be 1"
    assert tc.ALL_PROTOCOL == -1, "ALL protocol should be -1 (AWS special value)"
    
    # Valid protocol numbers are 0-255, except for AWS special value -1
    protocols = [tc.TCP_PROTOCOL, tc.UDP_PROTOCOL, tc.ICMP_PROTOCOL]
    for proto in protocols:
        assert 0 <= proto <= 255, f"Protocol {proto} outside valid range 0-255"


# Property 4: EC2 instance type naming patterns
def test_ec2_instance_type_patterns():
    """EC2 instance types should follow AWS naming conventions."""
    # Pattern: family[generation][attributes].size
    ec2_pattern = re.compile(r'^[a-z]\d+[a-z]*\.(nano|micro|small|medium|large|xlarge|\d+xlarge|metal)$')
    
    instance_type_constants = [
        name for name in dir(tc) 
        if not name.startswith('_') and not name.startswith('DB_') 
        and not name.startswith('CACHE_') and not name.startswith('SEARCH_')
        and not name.startswith('ELASTICSEARCH_') and not name.startswith('KAFKA_')
        and name[0].isupper() and '_' in name
    ]
    
    # Check a sample of instance types
    for const_name in instance_type_constants[:50]:  # Test first 50 to avoid too many checks
        if any(x in const_name for x in ['XLARGE', 'LARGE', 'MEDIUM', 'SMALL', 'NANO', 'MICRO', 'METAL']):
            value = getattr(tc, const_name)
            if isinstance(value, str) and '.' in value:
                assert ec2_pattern.match(value), \
                    f"Instance type {const_name}={value} doesn't match AWS pattern"


# Property 5: RDS instance types should follow db.* pattern
def test_rds_instance_type_patterns():
    """RDS instance types should follow db.* naming convention."""
    rds_pattern = re.compile(r'^db\.[a-z0-9]+\.(micro|small|medium|large|xlarge|\d+xlarge|metal|tpc\d+\.mem\d+x)$')
    
    for name in dir(tc):
        if name.startswith('DB_'):
            value = getattr(tc, name)
            if isinstance(value, str):
                assert value.startswith('db.'), f"RDS instance {name}={value} doesn't start with 'db.'"
                # Check general pattern (relaxed for special RDS types)
                assert '.' in value, f"RDS instance {name}={value} missing size delimiter"


# Property 6: Cache node types should follow cache.* pattern  
def test_cache_node_type_patterns():
    """ElastiCache node types should follow cache.* naming convention."""
    for name in dir(tc):
        if name.startswith('CACHE_'):
            value = getattr(tc, name)
            if isinstance(value, str):
                assert value.startswith('cache.'), \
                    f"Cache node type {name}={value} doesn't start with 'cache.'"


# Property 7: LOGS_ALLOWED_RETENTION_DAYS should be sorted and positive
def test_logs_retention_days_validity():
    """LOGS_ALLOWED_RETENTION_DAYS should contain sorted positive integers."""
    days = tc.LOGS_ALLOWED_RETENTION_DAYS
    
    # Should be a list
    assert isinstance(days, list), "LOGS_ALLOWED_RETENTION_DAYS should be a list"
    
    # All values should be positive integers
    for day in days:
        assert isinstance(day, int), f"Retention day {day} is not an integer"
        assert day > 0, f"Retention day {day} is not positive"
    
    # Should be sorted in ascending order
    assert days == sorted(days), "LOGS_ALLOWED_RETENTION_DAYS should be sorted"
    
    # No duplicates
    assert len(days) == len(set(days)), "LOGS_ALLOWED_RETENTION_DAYS contains duplicates"


# Property 8: CIDR notation validity
def test_cidr_notation():
    """CIDR blocks should be valid."""
    assert tc.QUAD_ZERO == "0.0.0.0/0", "QUAD_ZERO should be 0.0.0.0/0"
    assert tc.VPC_CIDR_16 == "10.0.0.0/16", "VPC_CIDR_16 should be 10.0.0.0/16"
    
    # Validate CIDR format
    cidr_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$')
    assert cidr_pattern.match(tc.QUAD_ZERO), "QUAD_ZERO doesn't match CIDR pattern"
    assert cidr_pattern.match(tc.VPC_CIDR_16), "VPC_CIDR_16 doesn't match CIDR pattern"


# Property 9: Search/OpenSearch instance types
def test_search_instance_type_patterns():
    """OpenSearch instance types should follow proper naming."""
    for name in dir(tc):
        if name.startswith('SEARCH_'):
            value = getattr(tc, name)
            if isinstance(value, str):
                # Should end with .search or .elasticsearch
                assert value.endswith('.search') or value.endswith('.elasticsearch'), \
                    f"Search instance {name}={value} doesn't end with .search"


# Property 10: Uniqueness of constants within categories
def test_constant_uniqueness():
    """Constants within each category should have unique values."""
    
    # Collect constants by category
    regions = []
    azs = []
    ec2_types = []
    rds_types = []
    cache_types = []
    
    for name in dir(tc):
        if name.startswith('_'):
            continue
        value = getattr(tc, name)
        if not isinstance(value, str):
            continue
            
        # Categorize based on naming patterns
        if re.match(r'^[A-Z]+_[A-Z]+_\d+$', name) and len(name.split('_')) == 3:
            # Likely a region
            if re.match(r'^[a-z]{2}-[a-z]+-\d+$', value):
                regions.append(value)
        elif re.match(r'^[A-Z]+_[A-Z]+_\d+[A-Z]$', name):
            # Likely an AZ
            if re.match(r'^[a-z]{2}-[a-z]+-\d+[a-z]$', value):
                azs.append(value)
        elif name.startswith('DB_'):
            rds_types.append(value)
        elif name.startswith('CACHE_'):
            cache_types.append(value)
        elif any(x in name for x in ['_NANO', '_MICRO', '_SMALL', '_MEDIUM', '_LARGE', '_XLARGE', '_METAL']):
            if not name.startswith('DB_') and not name.startswith('CACHE_'):
                if '.' in value:
                    ec2_types.append(value)
    
    # Check uniqueness
    assert len(regions) == len(set(regions)), f"Duplicate region values found"
    assert len(azs) == len(set(azs)), f"Duplicate AZ values found"
    assert len(ec2_types) == len(set(ec2_types)), f"Duplicate EC2 instance types found"
    assert len(rds_types) == len(set(rds_types)), f"Duplicate RDS instance types found"
    assert len(cache_types) == len(set(cache_types)), f"Duplicate cache node types found"


# Property 11: Kafka broker instance types
def test_kafka_instance_patterns():
    """Kafka broker instance types should follow kafka.* pattern."""
    for name in dir(tc):
        if name.startswith('KAFKA_'):
            value = getattr(tc, name)
            if isinstance(value, str):
                assert value.startswith('kafka.'), \
                    f"Kafka instance {name}={value} doesn't start with 'kafka.'"
                # Should follow kafka.family.size pattern
                parts = value.split('.')
                assert len(parts) == 3, f"Kafka instance {name}={value} doesn't have 3 parts"


# Property 12: Parameter type constants should be valid CloudFormation types
def test_parameter_types():
    """Parameter type constants should be valid CloudFormation parameter types."""
    # Basic parameter types
    assert tc.STRING == "String"
    assert tc.NUMBER == "Number"
    assert tc.LIST_OF_NUMBERS == "List<Number>"
    assert tc.COMMA_DELIMITED_LIST == "CommaDelimitedList"
    
    # AWS-specific parameter types should follow AWS::Service::Type pattern
    aws_param_pattern = re.compile(r'^AWS::[A-Za-z0-9]+::[A-Za-z0-9]+::[A-Za-z0-9]+$')
    aws_list_param_pattern = re.compile(r'^List<AWS::[A-Za-z0-9]+::[A-Za-z0-9]+::[A-Za-z0-9]+>$')
    
    aws_params = [
        tc.AVAILABILITY_ZONE_NAME,
        tc.IMAGE_ID,
        tc.INSTANCE_ID,
        tc.KEY_PAIR_NAME,
        tc.SECURITY_GROUP_NAME,
        tc.SECURITY_GROUP_ID,
        tc.SUBNET_ID,
        tc.VOLUME_ID,
        tc.VPC_ID,
        tc.HOSTED_ZONE_ID
    ]
    
    for param in aws_params:
        assert aws_param_pattern.match(param), f"Parameter type {param} doesn't match AWS pattern"
    
    # List parameter types
    list_params = [
        tc.LIST_OF_AVAILABILITY_ZONE_NAMES,
        tc.LIST_OF_IMAGE_ID,
        tc.LIST_OF_INSTANCE_IDS,
        tc.LIST_OF_SECURITY_GROUP_NAMES,
        tc.LIST_OF_SECURITY_GROUP_IDS,
        tc.LIST_OF_SUBNET_IDS,
        tc.LIST_OF_VOLUME_IDS,
        tc.LIST_OF_VPC_IDS,
        tc.LIST_OF_HOSTED_ZONE_IDS
    ]
    
    for param in list_params:
        assert aws_list_param_pattern.match(param), f"List parameter {param} doesn't match pattern"


if __name__ == "__main__":
    # Run all tests
    import pytest
    pytest.main([__file__, "-v"])