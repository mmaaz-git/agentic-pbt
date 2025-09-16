import json
import math
from hypothesis import given, strategies as st, assume
from troposphere.servicediscovery import (
    DnsRecord, DnsConfig, SOA, Service, Instance,
    HealthCheckConfig, HealthCheckCustomConfig
)
from troposphere.validators import double


# Property 1: double validator should only accept finite values for CloudFormation
@given(st.floats())
def test_double_validator_accepts_non_finite_values(value):
    """Test that the double validator incorrectly accepts non-finite values.
    
    AWS CloudFormation TTL values must be finite positive integers between 0 and 2147483647.
    The double validator should reject inf, -inf, and nan values.
    """
    if not math.isfinite(value):
        # These should be rejected but aren't
        result = double(value)
        assert result == value  # Bug: accepts inf/-inf/nan


# Property 2: to_json should produce valid JSON
@given(st.floats())
def test_to_json_produces_invalid_json_with_special_floats(value):
    """Test that to_json can produce invalid JSON with inf/nan values.
    
    JSON specification (RFC 7159) does not allow Infinity, -Infinity, or NaN.
    CloudFormation will reject such JSON.
    """
    assume(not math.isfinite(value))  # Only test inf/-inf/nan
    
    # Create a DnsRecord with the problematic value
    dns_record = DnsRecord(TTL=value, Type='A')
    json_output = dns_record.to_json()
    
    # This JSON is invalid according to RFC 7159
    # Try to validate it's actually parseable (Python allows it, but it's still invalid)
    parsed = json.loads(json_output)
    assert parsed['TTL'] == value
    
    # The real issue: this would fail in strict JSON parsers and CloudFormation
    # CloudFormation expects valid JSON and finite TTL values


# Property 3: Boolean values shouldn't be accepted as TTL
@given(st.booleans())
def test_double_validator_accepts_booleans(value):
    """Test that the double validator incorrectly accepts boolean values.
    
    TTL should be a numeric value, not a boolean.
    """
    # This should fail but doesn't
    result = double(value)
    assert result == value  # Bug: accepts True/False as 1.0/0.0


# Property 4: Negative TTL values shouldn't be allowed
@given(st.floats(max_value=-0.01))
def test_negative_ttl_values_accepted(value):
    """Test that negative TTL values are incorrectly accepted.
    
    DNS TTL values must be non-negative. CloudFormation will reject negative TTLs.
    """
    assume(math.isfinite(value))
    
    # These should be rejected but aren't
    dns_record = DnsRecord(TTL=value, Type='A')
    assert dns_record.to_dict()['TTL'] == value  # Bug: accepts negative TTL


# Property 5: TTL values should have reasonable bounds
@given(st.integers(min_value=2147483648))  # Above 32-bit signed int max
def test_ttl_exceeds_reasonable_bounds(value):
    """Test that TTL values exceeding CloudFormation limits are accepted.
    
    AWS CloudFormation TTL must be between 0 and 2147483647 (32-bit signed int max).
    """
    # These should be rejected but aren't
    dns_record = DnsRecord(TTL=value, Type='A')
    assert dns_record.to_dict()['TTL'] == value  # Bug: accepts values > 2^31-1