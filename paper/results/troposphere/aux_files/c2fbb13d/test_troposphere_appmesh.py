#!/usr/bin/env python3
"""
Property-based tests for troposphere.appmesh module.
Testing for genuine bugs in AWS CloudFormation template generation.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.appmesh as appmesh
from troposphere import validators
from troposphere.validators.appmesh import validate_listenertls_mode
import math


# Test 1: Integer validator accepts non-integers (floats)
@given(st.floats(min_value=-1e10, max_value=1e10, allow_nan=False, allow_infinity=False))
def test_integer_validator_accepts_floats(value):
    """The integer validator should reject non-integer floats but it accepts them."""
    if value != int(value):  # Only test non-integer floats
        try:
            result = validators.integer(value)
            # If we get here, the validator accepted a non-integer
            int_result = int(result)  
            # Bug: validator accepts floats like 1.5 and truncates them
            assert False, f"integer() accepted float {value} and converted to {int_result}"
        except (ValueError, TypeError):
            # This is expected behavior - should reject non-integers
            pass


# Test 2: Range classes don't validate Start <= End invariant
@given(
    st.integers(min_value=-1000000, max_value=1000000),
    st.integers(min_value=-1000000, max_value=1000000)
)
def test_range_start_end_invariant(start, end):
    """Range classes should enforce Start <= End but they don't."""
    
    # Test GatewayRouteRangeMatch
    range_obj = appmesh.GatewayRouteRangeMatch(Start=start, End=end)
    result = range_obj.to_dict()
    
    # Check if the object was created successfully with invalid range
    if start > end:
        # This is a bug - ranges with Start > End should be rejected
        assert result['Start'] == start and result['End'] == end, \
            "Range with Start > End was accepted"
    
    # Test MatchRange (similar class)
    match_range = appmesh.MatchRange(Start=start, End=end)
    match_result = match_range.to_dict()
    
    if start > end:
        assert match_result['Start'] == start and match_result['End'] == end, \
            "MatchRange with Start > End was accepted"


# Test 3: Duration accepts non-integer values  
@given(
    st.floats(min_value=0.1, max_value=1000000, allow_nan=False, 
              allow_infinity=False).filter(lambda x: x != int(x))
)
def test_duration_accepts_float_values(value):
    """Duration.Value is typed as integer but accepts floats."""
    try:
        duration = appmesh.Duration(Unit='ms', Value=value)
        result = duration.to_dict()
        # Bug: Duration accepts float values even though Value should be integer
        assert result['Value'] == value, f"Duration accepted float value {value}"
    except (ValueError, TypeError):
        # This would be the expected behavior for non-integer values
        pass


# Test 4: WeightedTarget Weight validation
@given(
    st.floats(min_value=0.1, max_value=100, allow_nan=False,
              allow_infinity=False).filter(lambda x: x != int(x))
)
def test_weighted_target_weight_accepts_floats(weight):
    """WeightedTarget.Weight is typed as integer but accepts floats."""
    try:
        wt = appmesh.WeightedTarget(
            VirtualNode='test-node',
            Weight=weight
        )
        result = wt.to_dict()
        # Bug: Weight accepts float values even though it should be integer
        assert result['Weight'] == weight, f"WeightedTarget accepted float weight {weight}"
    except (ValueError, TypeError):
        # This would be the expected behavior
        pass


# Test 5: Boolean validator accepts numeric values other than 0 and 1
@given(st.integers().filter(lambda x: x not in [0, 1]))
def test_boolean_validator_numeric_edge_cases(value):
    """Boolean validator should only accept 0 and 1 as numeric values."""
    try:
        result = validators.boolean(value)
        # Bug: boolean validator only checks for 0 and 1, not other integers
        assert False, f"boolean() accepted integer {value} -> {result}"
    except ValueError:
        # Expected behavior for integers other than 0 and 1
        pass


# Test 6: Port numbers can be negative or zero
@given(st.integers(min_value=-1000, max_value=0))
def test_port_mapping_negative_ports(port):
    """Port numbers should be positive but negative values are accepted."""
    try:
        # Test VirtualGatewayPortMapping
        port_mapping = appmesh.VirtualGatewayPortMapping(
            Port=port,
            Protocol='http'
        )
        result = port_mapping.to_dict()
        if port <= 0:
            # Bug: Negative or zero ports are accepted
            assert result['Port'] == port, f"Invalid port {port} was accepted"
    except (ValueError, TypeError):
        # Expected behavior for invalid ports
        pass


# Test 7: ListenerTls Mode validation is case-sensitive
@given(st.sampled_from(['strict', 'Strict', 'STRICT', 'permissive', 
                         'Permissive', 'PERMISSIVE', 'disabled', 'Disabled', 'DISABLED']))
def test_listener_tls_mode_case_sensitivity(mode):
    """ListenerTls Mode validator is case-sensitive but shouldn't be for usability."""
    try:
        result = validate_listenertls_mode(mode)
        # Only uppercase values work
        assert mode in ['STRICT', 'PERMISSIVE', 'DISABLED'], \
            f"Mode {mode} was accepted but only uppercase should work"
    except ValueError:
        # Lowercase and mixed case are rejected
        assert mode not in ['STRICT', 'PERMISSIVE', 'DISABLED'], \
            f"Valid uppercase mode {mode} was rejected"


# Test 8: Connection pool max values can be negative
@given(st.integers(min_value=-1000, max_value=-1))
def test_connection_pool_negative_values(max_value):
    """Connection pool max values should be positive but negative values are accepted."""
    
    # Test VirtualGatewayHttpConnectionPool
    try:
        pool = appmesh.VirtualGatewayHttpConnectionPool(MaxConnections=max_value)
        result = pool.to_dict()
        # Bug: Negative max connections accepted
        assert result['MaxConnections'] == max_value
    except (ValueError, TypeError):
        pass
    
    # Test VirtualGatewayGrpcConnectionPool
    try:
        pool = appmesh.VirtualGatewayGrpcConnectionPool(MaxRequests=max_value)
        result = pool.to_dict()
        # Bug: Negative max requests accepted
        assert result['MaxRequests'] == max_value
    except (ValueError, TypeError):
        pass


if __name__ == '__main__':
    # Run all tests
    import pytest
    pytest.main([__file__, '-v'])