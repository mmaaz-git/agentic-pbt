# Bug Report: coremltools.models.utils.rename_feature Fails to Rename Neural Network Layer Outputs

**Target**: `coremltools.models.utils.rename_feature`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `rename_feature` function fails to rename neural network layer outputs when `rename_inputs=False` and `rename_outputs=True` due to incorrect indentation in the implementation.

## Property-Based Test

```python
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
    assert spec.neuralNetwork.layers[0].output[0] == new_output_name  # This assertion fails!
    
    # Check input was NOT renamed
    assert spec.description.input[0].name == input_name
```

**Failing input**: `input_name='A', output_name='B', new_output_name='A'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

import coremltools.models.utils as utils
from coremltools import proto

def create_simple_spec(input_name="input", output_name="output"):
    spec = proto.Model_pb2.Model()
    spec.specificationVersion = 1
    
    input_desc = spec.description.input.add()
    input_desc.name = input_name
    input_desc.type.multiArrayType.shape.append(1)
    input_desc.type.multiArrayType.dataType = proto.FeatureTypes_pb2.ArrayFeatureType.FLOAT32
    
    output_desc = spec.description.output.add()
    output_desc.name = output_name
    output_desc.type.multiArrayType.shape.append(1)
    output_desc.type.multiArrayType.dataType = proto.FeatureTypes_pb2.ArrayFeatureType.FLOAT32
    
    nn = spec.neuralNetwork
    layer = nn.layers.add()
    layer.name = "identity"
    layer.input.append(input_name)
    layer.output.append(output_name)
    layer.activation.linear.alpha = 1.0
    layer.activation.linear.beta = 0.0
    
    return spec

spec = create_simple_spec(input_name='A', output_name='B')
print(f"Before: layer output = {spec.neuralNetwork.layers[0].output[0]}")

utils.rename_feature(spec, 'B', 'A', rename_inputs=False, rename_outputs=True)

print(f"After: layer output = {spec.neuralNetwork.layers[0].output[0]}")
print(f"Expected: 'A', Actual: '{spec.neuralNetwork.layers[0].output[0]}'")
assert spec.neuralNetwork.layers[0].output[0] == 'A', "Layer output not renamed!"
```

## Why This Is A Bug

The function's docstring states it will rename features in the specification. When `rename_outputs=True`, users expect all occurrences of the output feature to be renamed, including in neural network layer definitions. However, due to incorrect indentation, layer outputs are only renamed when BOTH `rename_inputs=True` AND `rename_outputs=True`, violating the documented API contract.

## Fix

```diff
--- a/coremltools/models/utils.py
+++ b/coremltools/models/utils.py
@@ -674,9 +674,9 @@ def rename_feature(
                 for index, name in enumerate(layer.input):
                     if name == current_name:
                         layer.input[index] = new_name
-                if rename_outputs:
-                    for index, name in enumerate(layer.output):
-                        if name == current_name:
-                            layer.output[index] = new_name
+            if rename_outputs:
+                for index, name in enumerate(layer.output):
+                    if name == current_name:
+                        layer.output[index] = new_name
 
         if rename_inputs:
```