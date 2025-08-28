#!/usr/bin/env python3
"""Advanced property-based tests using Hypothesis for troposphere.constants."""

import re
import sys
from hypothesis import given, strategies as st, settings, assume, note

# Add the troposphere env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.constants as tc


# Strategy to generate all constant names and values from the module
@st.composite
def constant_from_module(draw):
    """Generate a constant name and value from troposphere.constants."""
    all_constants = []
    for name in dir(tc):
        if not name.startswith('_'):
            value = getattr(tc, name)
            if isinstance(value, (str, int)):
                all_constants.append((name, value))
    
    if not all_constants:
        assume(False)
    
    return draw(st.sampled_from(all_constants))


# Property: Instance type size ordering should be consistent
@given(constant_from_module())
def test_instance_type_size_ordering_property(const):
    """Instance types within same family should have consistent size ordering."""
    name, value = const
    
    # Skip if not an instance type
    if not isinstance(value, str) or '.' not in value:
        assume(False)
    
    # Focus on EC2, RDS, Cache instance types
    if not any(name.startswith(prefix) for prefix in ['T', 'M', 'C', 'R', 'DB_', 'CACHE_']):
        assume(False)
    
    # Extract the size part
    parts = value.split('.')
    if len(parts) < 2:
        assume(False)
    
    size = parts[-1]
    
    # Define expected size ordering
    size_order = ['nano', 'micro', 'small', 'medium', 'large', 'xlarge']
    
    # Check xlarge variants
    if 'xlarge' in size:
        if size != 'xlarge' and size != 'metal':
            # Should be NUMBERxlarge format
            xlarge_match = re.match(r'^(\d+)xlarge$', size)
            if xlarge_match:
                num = int(xlarge_match.group(1))
                # Number should be reasonable (2-48 are common)
                assert 2 <= num <= 48, f"Unusual xlarge multiplier {num} in {value}"
    
    # If it's a standard size, it should be in our known list
    if not re.match(r'^\d+xlarge$', size) and size != 'metal' and not 'tpc' in size and not 'mem' in size:
        assert size in size_order, f"Unknown size '{size}' in instance type {value}"


# Property: Region names should follow consistent pattern
@given(constant_from_module())
def test_region_naming_pattern(const):
    """All region constants should follow consistent naming patterns."""
    name, value = const
    
    # Skip if not a string
    if not isinstance(value, str):
        assume(False)
    
    # Check if this looks like a region (e.g., us-east-1)
    region_pattern = re.compile(r'^[a-z]{2,3}-[a-z]+-\d+$')
    if region_pattern.match(value):
        # The constant name should be the uppercase version with underscores
        expected_name = value.replace('-', '_').upper()
        assert name == expected_name, f"Region constant {name} doesn't match value {value}"
        
        # Region prefix should be from known set
        prefix = value.split('-')[0]
        known_prefixes = ['us', 'eu', 'ap', 'ca', 'sa', 'me', 'af', 'cn']
        assert prefix in known_prefixes, f"Unknown region prefix '{prefix}' in {value}"


# Property: AZ letters should be sequential within a region
@given(constant_from_module())  
def test_az_letter_sequencing(const):
    """Availability zones within a region should use sequential letters."""
    name, value = const
    
    # Skip if not an AZ
    if not isinstance(value, str):
        assume(False)
    
    az_pattern = re.compile(r'^([a-z]{2,3}-[a-z]+-\d+)([a-z])$')
    match = az_pattern.match(value)
    if not match:
        assume(False)
    
    region = match.group(1)
    az_letter = match.group(2)
    
    # AZ letters should be from a-f range typically
    assert 'a' <= az_letter <= 'f', f"Unusual AZ letter '{az_letter}' in {value}"
    
    # Collect all AZs for this region
    region_azs = []
    for n in dir(tc):
        v = getattr(tc, n)
        if isinstance(v, str) and v.startswith(region):
            m = az_pattern.match(v)
            if m:
                region_azs.append(m.group(2))
    
    # AZs should start from 'a' and be mostly sequential
    if region_azs:
        region_azs = sorted(set(region_azs))
        # First AZ should be 'a'
        assert region_azs[0] == 'a', f"Region {region} doesn't start with AZ 'a'"
        
        # Check for large gaps (more than 1 letter skip)
        for i in range(len(region_azs) - 1):
            gap = ord(region_azs[i+1]) - ord(region_azs[i])
            # Allow skip of 'c' to 'd' (1 letter gap) but flag larger gaps
            assert gap <= 2, f"Large gap in AZ letters for {region}: {region_azs}"


# Property: Database instance types should have corresponding EC2 types
@given(constant_from_module())
def test_db_ec2_instance_correspondence(const):
    """Many DB instance types should have corresponding EC2 instance types."""
    name, value = const
    
    # Focus on DB instances
    if not name.startswith('DB_'):
        assume(False)
    
    if not isinstance(value, str) or not value.startswith('db.'):
        assume(False)
    
    # Extract the instance family and size
    # Format: db.FAMILY.SIZE
    parts = value.split('.')
    if len(parts) < 3:
        assume(False)
    
    family_size = '.'.join(parts[1:])
    
    # Skip special RDS-only types
    if 'tpc' in family_size or 'mem' in family_size:
        assume(False)
    
    # Common families that should have EC2 equivalents
    common_families = ['t2', 't3', 't4g', 'm5', 'm6g', 'r5', 'r6g', 'c5', 'c6g']
    family = parts[1]
    
    if any(family.startswith(f) for f in common_families):
        # Look for corresponding EC2 instance type
        # The EC2 constant name pattern would be like: M5_LARGE for m5.large
        ec2_const_name = f"{family.upper()}_{parts[2].upper()}"
        ec2_const_name = ec2_const_name.replace('.', '_')
        
        # Check if corresponding EC2 constant exists
        if hasattr(tc, ec2_const_name):
            ec2_value = getattr(tc, ec2_const_name)
            expected_ec2 = family_size
            # note(f"Checking DB {value} -> EC2 {ec2_const_name}={ec2_value}")
            # They should be similar (db. prefix vs no prefix)
            assert ec2_value == expected_ec2, \
                f"DB instance {value} and EC2 {ec2_const_name}={ec2_value} mismatch"


# Property: Port numbers should be standard for known services
@given(constant_from_module())
def test_standard_port_assignments(const):
    """Known services should use their standard port numbers."""
    name, value = const
    
    # Skip if not a port constant
    if '_PORT' not in name:
        assume(False)
    
    if not isinstance(value, int):
        assume(False)
    
    # Define standard ports
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
    
    if name in standard_ports:
        expected = standard_ports[name]
        assert value == expected, f"{name} should be {expected}, got {value}"


# Property: LIST_OF_* parameter types should correspond to singular versions
@given(constant_from_module())
def test_list_parameter_correspondence(const):
    """LIST_OF_* parameter types should wrap their singular counterparts."""
    name, value = const
    
    if not name.startswith('LIST_OF_'):
        assume(False)
    
    if not isinstance(value, str):
        assume(False)
    
    # Extract the singular form
    singular_name = name[8:]  # Remove 'LIST_OF_'
    
    # Handle special cases
    if singular_name.endswith('S'):
        # Could be plural - try without S
        potential_singular = singular_name[:-1]
        if hasattr(tc, potential_singular):
            singular_value = getattr(tc, potential_singular)
            expected = f"List<{singular_value}>"
            assert value == expected, \
                f"{name}={value} doesn't match List<{singular_value}>"
    
    # Try exact match
    if hasattr(tc, singular_name):
        singular_value = getattr(tc, singular_name)
        expected = f"List<{singular_value}>"
        assert value == expected, \
            f"{name}={value} doesn't match List<{singular_value}>"


# Property: ElastiCache and RDS should have overlapping instance families
@given(constant_from_module())
def test_cache_rds_family_overlap(const):
    """Cache and RDS should share many instance type families."""
    name, value = const
    
    if not isinstance(value, str):
        assume(False)
    
    # Check cache instances
    if name.startswith('CACHE_') and value.startswith('cache.'):
        parts = value.split('.')
        if len(parts) >= 3:
            family = parts[1]
            size = parts[2]
            
            # Common families between cache and RDS
            shared_families = ['t2', 't3', 't4g', 'm5', 'm6g', 'r5', 'r6g']
            
            if family in shared_families:
                # Look for corresponding RDS instance
                rds_value = f"db.{family}.{size}"
                # Check if this RDS instance exists in constants
                rds_exists = any(
                    getattr(tc, n) == rds_value 
                    for n in dir(tc) 
                    if n.startswith('DB_')
                )
                # Note: We're not asserting here as not all combinations exist
                # This is more of an observation than a hard requirement


# Property: LOGS_ALLOWED_RETENTION_DAYS should have reasonable progression
@given(st.integers(0, len(tc.LOGS_ALLOWED_RETENTION_DAYS) - 2))
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
    # Larger values can have bigger jumps (365 -> 400, etc.)


# Property: Deprecated Elasticsearch types should have OpenSearch equivalents
@given(constant_from_module())
def test_elasticsearch_to_opensearch_migration(const):
    """Deprecated Elasticsearch types should have OpenSearch equivalents."""
    name, value = const
    
    if not name.startswith('ELASTICSEARCH_'):
        assume(False)
    
    if not isinstance(value, str):
        assume(False)
    
    # Extract the base type (without elasticsearch suffix)
    if value.endswith('.elasticsearch'):
        base = value[:-len('.elasticsearch')]
        # There should be a corresponding .search version
        search_version = f"{base}.search"
        
        # Check if the search version exists
        search_exists = any(
            getattr(tc, n) == search_version
            for n in dir(tc)
            if n.startswith('SEARCH_')
        )
        
        # Most elasticsearch types should have search equivalents
        # Note: Not asserting as this is a migration path, not a hard requirement


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])