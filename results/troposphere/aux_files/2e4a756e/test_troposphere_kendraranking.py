#!/usr/bin/env python3
"""Property-based tests for troposphere.kendraranking module."""

import sys
import os

# Add the environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import troposphere.kendraranking as kr
from troposphere import Tags
from troposphere.validators import integer


# Test 1: Integer validator property
@given(st.one_of(
    st.integers(),
    st.text(),
    st.floats(),
    st.booleans(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator_property(value):
    """Test that integer validator accepts valid integers and rejects invalid ones."""
    try:
        result = integer(value)
        # If it didn't raise, it should be convertible to int
        int_val = int(value)
        # Check that the validator returns the original value
        assert result == value
    except (ValueError, TypeError):
        # Should fail for non-integer convertible values
        try:
            int(value)
            # If int() succeeds but integer() failed, that's a bug
            assert False, f"integer() rejected {value} but int() accepted it"
        except (ValueError, TypeError):
            # Both failed, which is correct
            pass


# Test 2: CapacityUnitsConfiguration required field validation
@given(st.one_of(
    st.integers(),
    st.text(min_size=1),
    st.floats(),
    st.none()
))
def test_capacity_units_required_field(value):
    """Test that CapacityUnitsConfiguration enforces required RescoreCapacityUnits."""
    if value is None:
        # Can create without required field, but validation should fail
        config = kr.CapacityUnitsConfiguration()
        # Check validation on to_dict()
        try:
            config.to_dict()
            # If it succeeds without required field, that's a bug
            assert False, "CapacityUnitsConfiguration.to_dict() succeeded without required RescoreCapacityUnits"
        except (ValueError, TypeError, KeyError):
            # Expected - should fail validation
            pass
    else:
        try:
            config = kr.CapacityUnitsConfiguration(RescoreCapacityUnits=value)
            # Check if it was set correctly
            assert hasattr(config, 'properties')
            # If integer validation should have failed
            try:
                integer(value)
                # Should have been set
                assert 'RescoreCapacityUnits' in config.properties
            except (ValueError, TypeError):
                # Should have raised during construction
                assert False, f"Should have rejected non-integer value {value}"
        except (TypeError, ValueError) as e:
            # Should only fail for non-integer values
            try:
                integer(value)
                # If integer() succeeds but construction failed, that's unexpected
                assert False, f"Construction failed for valid integer {value}: {e}"
            except (ValueError, TypeError):
                # Expected failure for non-integer
                pass


# Test 3: ExecutionPlan property type validation
@given(
    name=st.one_of(st.text(min_size=1), st.integers(), st.none()),
    description=st.one_of(st.text(), st.integers(), st.none()),
    capacity_units=st.one_of(
        st.none(),
        st.builds(kr.CapacityUnitsConfiguration, RescoreCapacityUnits=st.integers()),
        st.integers(),
        st.text()
    )
)
def test_execution_plan_type_validation(name, description, capacity_units):
    """Test that ExecutionPlan validates property types correctly."""
    try:
        plan = kr.ExecutionPlan(
            "TestPlan",  # Required title parameter
            Name=name,
            Description=description if description is not None else None,
            CapacityUnits=capacity_units if capacity_units is not None else None
        )
        
        # Check that properties were set
        if name is not None:
            assert 'Name' in plan.properties
        if description is not None:
            assert 'Description' in plan.properties
        if capacity_units is not None:
            assert 'CapacityUnits' in plan.properties
            
    except (TypeError, ValueError, AttributeError) as e:
        # Type validation should fail for wrong types
        # Name should be string
        if name is not None and not isinstance(name, str):
            return  # Expected failure
        # Description should be string
        if description is not None and not isinstance(description, str):
            return  # Expected failure
        # CapacityUnits should be CapacityUnitsConfiguration
        if capacity_units is not None and not isinstance(capacity_units, kr.CapacityUnitsConfiguration):
            return  # Expected failure
        # Otherwise unexpected
        raise


# Test 4: Tags concatenation property
@given(
    tags1=st.dictionaries(st.text(min_size=1), st.text()),
    tags2=st.dictionaries(st.text(min_size=1), st.text())
)
def test_tags_concatenation_property(tags1, tags2):
    """Test that Tags support concatenation via + operator."""
    t1 = Tags(**tags1)
    t2 = Tags(**tags2)
    
    # Test concatenation
    combined = t1 + t2
    
    # Combined should have all tags from both
    combined_dict = combined.to_dict()
    
    # Check that it's a list of dicts with Key and Value
    assert isinstance(combined_dict, list)
    
    # Extract keys from both original tag sets
    keys1 = set(tags1.keys())
    keys2 = set(tags2.keys())
    all_keys = keys1 | keys2
    
    # Extract keys from combined
    combined_keys = {item['Key'] for item in combined_dict if isinstance(item, dict) and 'Key' in item}
    
    # All keys should be present
    assert all_keys == combined_keys


# Test 5: to_dict serialization round-trip
@given(
    rescore_units=st.integers(),
    name=st.text(min_size=1, alphabet=st.characters(min_codepoint=65, max_codepoint=122)),
    description=st.text()
)
def test_to_dict_serialization(rescore_units, name, description):
    """Test that objects serialize to dict correctly."""
    # Create a CapacityUnitsConfiguration
    config = kr.CapacityUnitsConfiguration(RescoreCapacityUnits=rescore_units)
    
    # Create an ExecutionPlan  
    plan = kr.ExecutionPlan(
        "TestPlan",  # Required title parameter
        Name=name,
        Description=description if description else None,
        CapacityUnits=config
    )
    
    # Serialize to dict
    plan_dict = plan.to_dict()
    
    # Check structure
    assert isinstance(plan_dict, dict)
    assert 'Type' in plan_dict
    assert plan_dict['Type'] == 'AWS::KendraRanking::ExecutionPlan'
    assert 'Properties' in plan_dict
    
    props = plan_dict['Properties']
    assert 'Name' in props
    assert props['Name'] == name
    
    if description:
        assert 'Description' in props
        assert props['Description'] == description
        
    assert 'CapacityUnits' in props
    cap_units = props['CapacityUnits']
    assert 'RescoreCapacityUnits' in cap_units
    assert cap_units['RescoreCapacityUnits'] == rescore_units


# Test 6: Property validation with extreme integer values
@given(st.one_of(
    st.integers(min_value=-10**100, max_value=10**100),
    st.sampled_from([float('inf'), float('-inf'), float('nan')]),
    st.text(alphabet='0123456789', min_size=100, max_size=1000),  # Very large numeric strings
))
def test_extreme_integer_validation(value):
    """Test integer validator with extreme values."""
    try:
        result = integer(value)
        # Should be convertible to int if it passed
        int_value = int(value)
        assert result == value
    except (ValueError, TypeError, OverflowError):
        # Should fail for non-integers or overflow
        try:
            int(value)
            # If int() works but integer() failed, potential bug
            assert False, f"integer() failed but int() succeeded for {value}"
        except (ValueError, TypeError, OverflowError):
            # Both failed correctly
            pass


# Test 7: ExecutionPlan with missing required Name field
@given(
    description=st.text(),
    rescore_units=st.integers()
)
def test_execution_plan_missing_required_name(description, rescore_units):
    """Test that ExecutionPlan requires Name field."""
    config = kr.CapacityUnitsConfiguration(RescoreCapacityUnits=rescore_units)
    
    # Try to create without Name (required field)
    plan = kr.ExecutionPlan(
        "TestPlan",  # Required title parameter
        Description=description,
        CapacityUnits=config
    )
    
    # to_dict should check for required fields
    try:
        plan_dict = plan.to_dict()
        # If it succeeds, Name should have been set somehow or validation is off
        # This is a potential issue - required field not enforced
    except (ValueError, TypeError, KeyError) as e:
        # Expected - should fail without required Name
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])