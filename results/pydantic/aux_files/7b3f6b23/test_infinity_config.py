"""Check if there's a configuration option for infinity handling"""

import math
from pydantic import BaseModel, Field

# Test with allow_inf_nan field configuration
class ConfiguredFloatModel(BaseModel):
    value: float = Field(allow_inf_nan=True)

print("Testing with allow_inf_nan=True in Field:")
model = ConfiguredFloatModel(value=float('inf'))
print(f"  Model created with inf: {model.value}")

json_str = model.model_dump_json()
print(f"  JSON representation: {json_str}")

try:
    restored = ConfiguredFloatModel.model_validate_json(json_str)
    print(f"  Restored successfully: {restored.value}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test if model_dump_json has options for this
print("\nChecking model_dump_json parameters:")
import inspect
sig = inspect.signature(BaseModel.model_dump_json)
print(f"  Parameters: {list(sig.parameters.keys())}")

# Check if there's a ser_json_inf_nan option
print("\nTrying different serialization modes:")
model = ConfiguredFloatModel(value=float('inf'))

# Try with different modes
try:
    json_str = model.model_dump_json(mode='json')
    print(f"  mode='json': {json_str}")
except Exception as e:
    print(f"  mode='json' error: {e}")

try:
    json_str = model.model_dump_json(mode='python')
    print(f"  mode='python': {json_str}")
except Exception as e:
    print(f"  mode='python' error: {e}")

# Check model_dump output
print("\nChecking model_dump output:")
dumped = model.model_dump()
print(f"  model_dump() value: {dumped['value']}")
print(f"  Type: {type(dumped['value'])}")
print(f"  Is inf? {math.isinf(dumped['value'])}")

# Can we round-trip through dict?
print("\nTesting dict round-trip:")
restored = ConfiguredFloatModel.model_validate(dumped)
print(f"  Restored from dict: {restored.value}")
print(f"  Is inf? {math.isinf(restored.value)}")

# Try with ser_json_inf_nan if it exists
print("\nLooking for inf_nan serialization options...")
try:
    # Try pydantic_core options
    from pydantic_core import to_json
    data = {"value": float('inf')}
    json_bytes = to_json(data, inf_nan_mode='constants')
    print(f"  pydantic_core.to_json with inf_nan_mode='constants': {json_bytes}")
except Exception as e:
    print(f"  Error: {e}")