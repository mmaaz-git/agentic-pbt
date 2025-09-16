#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""Property-based tests for troposphere.omics module."""

import math
import sys
import traceback
from hypothesis import assume, given, strategies as st, settings

# Ensure we use the correct environment
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.omics as omics
from troposphere.validators import boolean, double


# Test 1: Boolean validator properly converts truthy/falsy values
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator correctly converts valid inputs."""
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator raises ValueError for invalid inputs."""
    # Skip valid values
    if value in [True, False, 1, 0, "1", "0", "true", "True", "false", "False"]:
        assume(False)
    
    try:
        boolean(value)
        assert False, f"Expected ValueError for {value!r}"
    except ValueError:
        pass  # Expected


# Test 2: Double validator accepts valid floating point values
@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False),
    st.integers(),
    st.text().filter(lambda x: x.replace('.', '', 1).replace('-', '', 1).replace('+', '', 1).replace('e', '', 1).replace('E', '', 1).isdigit() if x else False)
))
def test_double_validator_valid_inputs(value):
    """Test that double validator accepts valid numeric inputs."""
    try:
        float_val = float(value)
        if math.isnan(float_val) or math.isinf(float_val):
            assume(False)
    except (ValueError, TypeError, OverflowError):
        assume(False)
    
    result = double(value)
    assert result == value


@given(st.one_of(
    st.text().filter(lambda x: not (x and x.replace('.', '', 1).replace('-', '', 1).replace('+', '', 1).replace('e', '', 1).replace('E', '', 1).isdigit())),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_double_validator_invalid_inputs(value):
    """Test that double validator raises ValueError for invalid inputs."""
    try:
        double(value)
        assert False, f"Expected ValueError for {value!r}"
    except ValueError:
        pass  # Expected


# Test 3: Round-trip property for AWS objects
@given(
    name=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50),
    description=st.text(max_size=100),
    max_cpus=st.floats(min_value=1, max_value=10000, allow_nan=False, allow_infinity=False),
    max_runs=st.floats(min_value=1, max_value=1000, allow_nan=False, allow_infinity=False)
)
def test_rungroup_to_dict_from_dict_roundtrip(name, description, max_cpus, max_runs):
    """Test that RunGroup can round-trip through to_dict and _from_dict."""
    # Create a RunGroup with properties
    original = omics.RunGroup("TestRunGroup")
    original.Name = name
    original.MaxCpus = max_cpus
    original.MaxRuns = max_runs
    if description:
        original.Description = description
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Extract properties for reconstruction
    properties = dict_repr.get("Properties", {})
    
    # Create new object from dict
    reconstructed = omics.RunGroup._from_dict("TestRunGroup", **properties)
    
    # Compare the dict representations
    reconstructed_dict = reconstructed.to_dict()
    
    # The dicts should be equal
    assert dict_repr == reconstructed_dict


# Test 4: Invalid property names raise AttributeError
@given(
    invalid_prop_name=st.text(min_size=1, max_size=50).filter(
        lambda x: x not in ["Name", "Description", "MaxCpus", "MaxDuration", "MaxGpus", "MaxRuns", "Tags"]
    )
)
def test_invalid_property_raises_error(invalid_prop_name):
    """Test that setting invalid properties raises AttributeError."""
    rg = omics.RunGroup("TestRunGroup")
    
    try:
        setattr(rg, invalid_prop_name, "test_value")
        # If we get here without exception, check if it's actually set
        # (CustomResource allows arbitrary properties)
        if invalid_prop_name not in rg.properties:
            assert False, f"Expected AttributeError for property {invalid_prop_name!r}"
    except AttributeError:
        pass  # Expected


# Test 5: Required properties validation
@given(
    store_format=st.text(min_size=1, max_size=50),
    invalid_name=st.one_of(st.none(), st.just(""))
)
def test_required_properties_validation(store_format, invalid_name):
    """Test that required properties are validated."""
    # AnnotationStore requires Name and StoreFormat
    store = omics.AnnotationStore("TestStore")
    store.StoreFormat = store_format
    
    # Try to set invalid Name (empty or None)
    if invalid_name is None:
        # Setting None should work but validation might fail
        store.Name = invalid_name
        try:
            dict_repr = store.to_dict()
            # Check if Name is properly set
            props = dict_repr.get("Properties", {})
            # None values might be filtered out
            assert "Name" not in props or props["Name"] is None
        except Exception:
            pass  # Some validation error is acceptable
    else:
        # Empty string
        store.Name = invalid_name
        dict_repr = store.to_dict()
        props = dict_repr.get("Properties", {})
        assert props.get("Name") == invalid_name


# Test 6: Properties with nested objects
@given(
    key_arn=st.text(min_size=1, max_size=100),
    sse_type=st.text(min_size=1, max_size=50)
)
def test_nested_property_objects(key_arn, sse_type):
    """Test that nested property objects work correctly."""
    # Create SSEConfig
    sse_config = omics.SseConfig()
    sse_config.Type = sse_type
    sse_config.KeyArn = key_arn
    
    # Use it in a parent object
    ref_store = omics.ReferenceStore("TestRefStore")
    ref_store.Name = "TestStore"
    ref_store.SseConfig = sse_config
    
    # Convert to dict
    dict_repr = ref_store.to_dict()
    
    # Check nested structure
    props = dict_repr.get("Properties", {})
    assert "SseConfig" in props
    assert props["SseConfig"]["Type"] == sse_type
    assert props["SseConfig"]["KeyArn"] == key_arn


# Test 7: WorkflowParameter Optional field boolean conversion
@given(
    optional_value=st.one_of(
        st.sampled_from([True, False, 1, 0, "true", "false", "True", "False"]),
        st.none()
    )
)
def test_workflow_parameter_optional_boolean(optional_value):
    """Test that WorkflowParameter.Optional field properly uses boolean validator."""
    param = omics.WorkflowParameter()
    
    if optional_value is None:
        # None might be allowed for optional fields
        param.Optional = optional_value
        dict_repr = param.to_dict()
        # Check if None is filtered out or preserved
        assert "Optional" not in dict_repr or dict_repr["Optional"] is None
    elif optional_value in [True, False, 1, 0, "true", "false", "True", "False"]:
        param.Optional = optional_value
        dict_repr = param.to_dict()
        # Should be converted to boolean
        if "Optional" in dict_repr:
            assert isinstance(dict_repr["Optional"], bool)
    else:
        # Invalid values should raise error
        try:
            param.Optional = optional_value
            dict_repr = param.to_dict()
        except (ValueError, TypeError):
            pass  # Expected


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])