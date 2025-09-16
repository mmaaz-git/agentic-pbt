#!/usr/bin/env python3
"""Property-based tests for coremltools using Hypothesis."""

import sys
import tempfile
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

# Suppress warnings about missing compiled libraries
import warnings
warnings.filterwarnings('ignore', message='Failed to load')
warnings.filterwarnings('ignore', message='Fail to import')

import coremltools
import coremltools.models.utils as utils
from coremltools import proto
from hypothesis import given, strategies as st, assume, settings
import shutil


def create_simple_spec(input_name="input", output_name="output"):
    """Create a simple valid protobuf spec for testing."""
    spec = proto.Model_pb2.Model()
    spec.specificationVersion = 1
    
    # Add a simple input
    input_desc = spec.description.input.add()
    input_desc.name = input_name
    input_desc.type.multiArrayType.shape.append(1)
    input_desc.type.multiArrayType.dataType = proto.FeatureTypes_pb2.ArrayFeatureType.FLOAT32
    
    # Add a simple output
    output_desc = spec.description.output.add()
    output_desc.name = output_name
    output_desc.type.multiArrayType.shape.append(1)
    output_desc.type.multiArrayType.dataType = proto.FeatureTypes_pb2.ArrayFeatureType.FLOAT32
    
    # Add a simple identity layer (neuralNetwork)
    nn = spec.neuralNetwork
    layer = nn.layers.add()
    layer.name = "identity"
    layer.input.append(input_name)
    layer.output.append(output_name)
    layer.activation.linear.alpha = 1.0
    layer.activation.linear.beta = 0.0
    
    return spec


# Strategy for valid feature names
valid_names = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
    min_size=1,
    max_size=50
).filter(lambda x: x[0].isalpha() or x[0] == '_')  # Must start with letter or underscore


@given(
    original_name=valid_names,
    intermediate_name=valid_names
)
@settings(max_examples=100)
def test_rename_feature_round_trip(original_name, intermediate_name):
    """Test that renaming a feature and then renaming back preserves the spec."""
    assume(original_name != intermediate_name)  # Skip if names are the same
    
    # Create a spec with the original name
    spec = create_simple_spec(input_name=original_name)
    
    # Save original spec state
    original_input_name = spec.description.input[0].name
    original_layer_input = spec.neuralNetwork.layers[0].input[0]
    
    # Rename from original to intermediate
    utils.rename_feature(spec, original_name, intermediate_name, rename_inputs=True, rename_outputs=False)
    
    # Check intermediate state
    assert spec.description.input[0].name == intermediate_name
    assert spec.neuralNetwork.layers[0].input[0] == intermediate_name
    
    # Rename back to original
    utils.rename_feature(spec, intermediate_name, original_name, rename_inputs=True, rename_outputs=False)
    
    # Check we're back to original
    assert spec.description.input[0].name == original_input_name
    assert spec.neuralNetwork.layers[0].input[0] == original_layer_input


@given(
    feature_name=valid_names
)
@settings(max_examples=100)
def test_rename_feature_idempotence(feature_name):
    """Test that renaming a feature to the same name is idempotent."""
    # Create a spec
    spec = create_simple_spec(input_name=feature_name)
    
    # Save original spec as bytes for comparison
    original_bytes = spec.SerializeToString()
    
    # Rename to same name (should be no-op)
    utils.rename_feature(spec, feature_name, feature_name, rename_inputs=True, rename_outputs=True)
    
    # Check spec hasn't changed
    assert spec.SerializeToString() == original_bytes


@given(
    input_name=valid_names,
    output_name=valid_names
)
@settings(max_examples=50)
def test_save_load_spec_round_trip(input_name, output_name):
    """Test that saving and loading a spec preserves it."""
    assume(input_name != output_name)  # Different names for input/output
    
    # Create a spec
    original_spec = create_simple_spec(input_name=input_name, output_name=output_name)
    
    # Save original spec bytes for comparison
    original_bytes = original_spec.SerializeToString()
    
    # Save and load the spec
    with tempfile.NamedTemporaryFile(suffix='.mlmodel', delete=False) as f:
        temp_path = f.name
    
    try:
        # Save spec
        utils.save_spec(original_spec, temp_path)
        
        # Load spec back
        loaded_spec = utils.load_spec(temp_path)
        
        # Compare specs
        assert loaded_spec.SerializeToString() == original_bytes
        
        # Verify key fields are preserved
        assert loaded_spec.description.input[0].name == input_name
        assert loaded_spec.description.output[0].name == output_name
        
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@given(
    old_name=valid_names,
    new_name=valid_names,
    rename_inputs=st.booleans(),
    rename_outputs=st.booleans()
)
@settings(max_examples=100)
def test_rename_nonexistent_feature_is_noop(old_name, new_name, rename_inputs, rename_outputs):
    """Test that renaming a non-existent feature is a no-op."""
    # Create spec with known feature names
    spec = create_simple_spec(input_name="known_input", output_name="known_output")
    assume(old_name != "known_input" and old_name != "known_output")  # Ensure we're testing non-existent
    
    # Save original spec
    original_bytes = spec.SerializeToString()
    
    # Try to rename non-existent feature
    utils.rename_feature(spec, old_name, new_name, rename_inputs=rename_inputs, rename_outputs=rename_outputs)
    
    # Spec should be unchanged (no-op as documented)
    assert spec.SerializeToString() == original_bytes


@given(
    input_name=valid_names,
    output_name=valid_names,
    new_output_name=valid_names
)
@settings(max_examples=100)
def test_rename_output_feature(input_name, output_name, new_output_name):
    """Test renaming output features."""
    assume(output_name != new_output_name)
    assume(input_name != output_name)
    
    # Create spec
    spec = create_simple_spec(input_name=input_name, output_name=output_name)
    
    # Rename output
    utils.rename_feature(spec, output_name, new_output_name, rename_inputs=False, rename_outputs=True)
    
    # Check output was renamed
    assert spec.description.output[0].name == new_output_name
    assert spec.neuralNetwork.layers[0].output[0] == new_output_name
    
    # Check input was NOT renamed
    assert spec.description.input[0].name == input_name


if __name__ == "__main__":
    # Run tests directly with pytest
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])