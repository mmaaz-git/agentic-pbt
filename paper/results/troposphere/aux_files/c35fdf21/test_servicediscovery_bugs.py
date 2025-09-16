"""
Demonstration of bugs in troposphere.servicediscovery module.

These tests demonstrate actual bugs where the module accepts invalid values
that would be rejected by AWS CloudFormation.
"""

import json
import math
from hypothesis import given, strategies as st, settings, HealthCheck
from troposphere.servicediscovery import DnsRecord, SOA
from troposphere.validators import double


# Bug 1: double validator accepts infinity values
@given(st.sampled_from([float('inf'), float('-inf')]))
def test_double_accepts_infinity(value):
    """The double validator accepts infinity, which CloudFormation rejects."""
    result = double(value)
    assert result == value  # This passes, showing inf is accepted
    
    # This creates invalid CloudFormation templates
    dns_record = DnsRecord(TTL=value, Type='A')
    json_str = dns_record.to_json()
    assert 'Infinity' in json_str  # Invalid JSON for CloudFormation


# Bug 2: double validator accepts NaN
def test_double_accepts_nan():
    """The double validator accepts NaN, which CloudFormation rejects."""
    value = float('nan')
    result = double(value)
    assert math.isnan(result)  # This passes, showing nan is accepted
    
    # This creates invalid CloudFormation templates
    dns_record = DnsRecord(TTL=value, Type='A')
    json_str = dns_record.to_json()
    assert 'NaN' in json_str  # Invalid JSON for CloudFormation


# Bug 3: Boolean values are accepted as numeric TTL
@given(st.booleans())
def test_double_accepts_booleans(value):
    """Booleans are accepted as TTL values, which is semantically wrong."""
    result = double(value)
    assert result == value  # Passes - booleans accepted
    
    dns_record = DnsRecord(TTL=value, Type='A')
    dict_result = dns_record.to_dict()
    assert dict_result['TTL'] == value  # Boolean in TTL field!


# Bug 4: Negative TTL values are accepted
@given(st.integers(max_value=-1))
def test_negative_ttl_accepted(value):
    """Negative TTL values are accepted, but DNS TTL must be non-negative."""
    dns_record = DnsRecord(TTL=value, Type='A')
    dict_result = dns_record.to_dict()
    assert dict_result['TTL'] == value  # Negative TTL accepted!


# Bug 5: TTL values beyond CloudFormation limits
@given(st.integers(min_value=2147483648))  # 2^31, beyond CF limit
@settings(max_examples=10)  # Limit examples for performance
def test_ttl_exceeds_cloudformation_limit(value):
    """TTL values > 2147483647 are accepted but exceed CloudFormation's limit."""
    dns_record = DnsRecord(TTL=value, Type='A')
    dict_result = dns_record.to_dict()
    assert dict_result['TTL'] == value  # Value beyond CF limit accepted!