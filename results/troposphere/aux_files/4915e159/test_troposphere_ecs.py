import troposphere.ecs as ecs
import troposphere.validators as validators
from hypothesis import given, strategies as st, assume
import pytest


# Test 1: integer_range validator boundary conditions
@given(st.integers())
def test_ephemeral_storage_size_validator(size):
    """Test that validate_ephemeral_storage_size correctly validates 21-200 range"""
    try:
        result = ecs.validate_ephemeral_storage_size(size)
        # If it succeeds, size should be in valid range
        assert 21 <= int(size) <= 200
        # Should return the original value
        assert result == size
    except ValueError as e:
        # If it fails, size should be outside valid range
        assert int(size) < 21 or int(size) > 200
        assert "Integer must be between 21 and 200" in str(e)


# Test 2: Validator string case sensitivity
@given(st.text())
def test_placement_constraint_validator_case_sensitivity(value):
    """Test if placement_constraint_validator handles case variations"""
    valid_values = ["distinctInstance", "memberOf"]
    
    try:
        result = ecs.placement_constraint_validator(value)
        # If it succeeds, should be exact match
        assert value in valid_values
        assert result == value
    except ValueError:
        # If it fails, should not be in valid values
        assert value not in valid_values


@given(st.text())
def test_placement_strategy_validator_case_sensitivity(value):
    """Test if placement_strategy_validator handles case variations"""
    valid_values = ["random", "spread", "binpack"]
    
    try:
        result = ecs.placement_strategy_validator(value)
        assert value in valid_values
        assert result == value
    except ValueError:
        assert value not in valid_values


@given(st.text())
def test_launch_type_validator_values(value):
    """Test launch_type_validator accepts only EC2 and FARGATE"""
    valid_values = ["EC2", "FARGATE"]
    
    try:
        result = ecs.launch_type_validator(value)
        assert value in valid_values
        assert result == value
    except ValueError:
        assert value not in valid_values


@given(st.text())  
def test_ecs_proxy_type_validator(value):
    """Test ecs_proxy_type accepts only APPMESH"""
    valid_values = ["APPMESH"]
    
    try:
        result = ecs.ecs_proxy_type(value)
        assert value in valid_values
        assert result == value
    except ValueError:
        assert value not in valid_values


@given(st.text())
def test_ecs_efs_encryption_status_validator(value):
    """Test ecs_efs_encryption_status accepts only ENABLED and DISABLED"""
    valid_values = ["ENABLED", "DISABLED"]
    
    try:
        result = ecs.ecs_efs_encryption_status(value)
        assert value in valid_values
        assert result == value
    except ValueError:
        assert value not in valid_values


# Test 3: Round-trip property for PlacementConstraint
@given(
    st.sampled_from(["distinctInstance", "memberOf"]),
    st.text(min_size=1)
)
def test_placement_constraint_round_trip(type_val, expression):
    """Test PlacementConstraint to_dict preserves data"""
    pc = ecs.PlacementConstraint(Type=type_val, Expression=expression)
    dict_repr = pc.to_dict()
    
    # Should preserve Type and Expression
    assert dict_repr["Type"] == type_val
    assert dict_repr["Expression"] == expression
    
    # Create new object from dict values
    pc2 = ecs.PlacementConstraint(**dict_repr)
    dict_repr2 = pc2.to_dict()
    
    # Round-trip should be identical
    assert dict_repr == dict_repr2


# Test 4: ProxyConfiguration round-trip
@given(st.sampled_from(["APPMESH"]))
def test_proxy_configuration_round_trip(proxy_type):
    """Test ProxyConfiguration to_dict preserves data"""
    proxy = ecs.ProxyConfiguration(Type=proxy_type)
    dict_repr = proxy.to_dict()
    
    assert dict_repr["Type"] == proxy_type
    
    # Round-trip
    proxy2 = ecs.ProxyConfiguration(**dict_repr)
    dict_repr2 = proxy2.to_dict()
    
    assert dict_repr == dict_repr2


# Test 5: Integer range edge cases with float-like strings
@given(st.floats(min_value=20, max_value=201))
def test_ephemeral_storage_float_conversion(size):
    """Test validate_ephemeral_storage_size with float inputs"""
    try:
        result = ecs.validate_ephemeral_storage_size(size)
        # Should convert to int and validate range
        int_size = int(size)
        assert 21 <= int_size <= 200
        # Result should be original value (not converted)
        assert result == size
    except (ValueError, TypeError):
        # Should fail if outside range or can't convert
        try:
            int_size = int(size)
            assert int_size < 21 or int_size > 200
        except (ValueError, TypeError):
            pass  # Expected for NaN or inf


# Test 6: Scope validator
@given(st.text())
def test_scope_validator(value):
    """Test scope_validator accepts only shared and task"""
    valid_values = ["shared", "task"]
    
    try:
        result = ecs.scope_validator(value)
        assert value in valid_values
        assert result == value
    except ValueError:
        assert value not in valid_values


# Test 7: Check error messages format consistency
@given(st.text())
def test_validator_error_message_format(value):
    """Test that validator error messages follow consistent format"""
    validators_to_test = [
        (ecs.placement_constraint_validator, "Placement Constraint type must be one of:"),
        (ecs.placement_strategy_validator, "Placement Strategy type must be one of:"),
        (ecs.launch_type_validator, "Launch Type must be one of:"),
        (ecs.scope_validator, "Scope type must be one of:"),
        (ecs.ecs_proxy_type, 'Type must be one of:'),
        (ecs.ecs_efs_encryption_status, 'ECS EFS Encryption in transit can only be one of:')
    ]
    
    for validator, expected_prefix in validators_to_test:
        try:
            validator(value)
        except ValueError as e:
            # Error message should contain the expected prefix
            error_msg = str(e)
            if not (expected_prefix in error_msg or expected_prefix.strip('"') in error_msg):
                # Found inconsistency in error message format
                assert False, f"Unexpected error format for {validator.__name__}: {error_msg}"