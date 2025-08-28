#!/usr/bin/env python3
"""Minimal reproduction of the rename_feature bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import warnings
warnings.filterwarnings('ignore')

import coremltools.models.utils as utils
from coremltools import proto


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


# Reproduce the bug with the exact failing case
print("Creating spec with input='A', output='B'")
spec = create_simple_spec(input_name='A', output_name='B')

print(f"Initial state:")
print(f"  Input name: {spec.description.input[0].name}")
print(f"  Output name: {spec.description.output[0].name}")
print(f"  Layer input: {spec.neuralNetwork.layers[0].input[0]}")
print(f"  Layer output: {spec.neuralNetwork.layers[0].output[0]}")

print("\nRenaming output from 'B' to 'A' (same as input name)...")
utils.rename_feature(spec, 'B', 'A', rename_inputs=False, rename_outputs=True)

print(f"\nAfter rename:")
print(f"  Input name: {spec.description.input[0].name}")
print(f"  Output name: {spec.description.output[0].name}")
print(f"  Layer input: {spec.neuralNetwork.layers[0].input[0]}")
print(f"  Layer output: {spec.neuralNetwork.layers[0].output[0]}")

print("\nBug Analysis:")
print(f"Expected layer output: 'A'")
print(f"Actual layer output: '{spec.neuralNetwork.layers[0].output[0]}'")
print(f"Bug: Layer output was not renamed when rename_outputs=True!")

# Additional test case - does it work if we don't have naming collision?
print("\n\n=== Testing without name collision ===")
spec2 = create_simple_spec(input_name='X', output_name='Y')
print("Initial: input='X', output='Y'")
utils.rename_feature(spec2, 'Y', 'Z', rename_inputs=False, rename_outputs=True)
print(f"After renaming output 'Y' to 'Z':")
print(f"  Layer output: {spec2.neuralNetwork.layers[0].output[0]} (expected: 'Z')")

# Test if the problem is specific to naming collision
print("\n\n=== Detailed analysis of the bug ===")
spec3 = create_simple_spec(input_name='input1', output_name='output1')
print("Case 1: No collision")
utils.rename_feature(spec3, 'output1', 'output2', rename_inputs=False, rename_outputs=True) 
print(f"  Result: layer output = {spec3.neuralNetwork.layers[0].output[0]} (expected: 'output2')")

spec4 = create_simple_spec(input_name='name1', output_name='name2')
print("Case 2: Renaming to existing input name")
utils.rename_feature(spec4, 'name2', 'name1', rename_inputs=False, rename_outputs=True)
print(f"  Result: layer output = {spec4.neuralNetwork.layers[0].output[0]} (expected: 'name1')")