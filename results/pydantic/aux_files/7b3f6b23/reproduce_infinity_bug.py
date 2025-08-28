"""Reproduction of infinity JSON serialization bug"""

import math
from pydantic import BaseModel

class FloatModel(BaseModel):
    value: float

# Test with positive infinity
print("Testing positive infinity:")
model_inf = FloatModel(value=float('inf'))
print(f"  Original value: {model_inf.value}")
print(f"  Is infinite? {math.isinf(model_inf.value)}")

# Serialize to JSON
json_str = model_inf.model_dump_json()
print(f"  JSON representation: {json_str}")

# Try to deserialize
try:
    restored = FloatModel.model_validate_json(json_str)
    print(f"  Restored value: {restored.value}")
except Exception as e:
    print(f"  ERROR deserializing: {e}")

print("\nTesting negative infinity:")
model_neginf = FloatModel(value=float('-inf'))
print(f"  Original value: {model_neginf.value}")

json_str = model_neginf.model_dump_json()
print(f"  JSON representation: {json_str}")

try:
    restored = FloatModel.model_validate_json(json_str)
    print(f"  Restored value: {restored.value}")
except Exception as e:
    print(f"  ERROR deserializing: {e}")

print("\nTesting NaN:")
model_nan = FloatModel(value=float('nan'))
print(f"  Original value: {model_nan.value}")
print(f"  Is NaN? {math.isnan(model_nan.value)}")

json_str = model_nan.model_dump_json()
print(f"  JSON representation: {json_str}")

try:
    restored = FloatModel.model_validate_json(json_str)
    print(f"  Restored value: {restored.value}")
    print(f"  Is restored NaN? {math.isnan(restored.value)}")
except Exception as e:
    print(f"  ERROR deserializing: {e}")

# Let's also check what Python's json module does
print("\nComparing with Python's json module:")
import json

data = {"inf": float('inf'), "neginf": float('-inf'), "nan": float('nan')}
print(f"  Original data: {data}")

try:
    json_str = json.dumps(data)
    print(f"  json.dumps result: {json_str}")
except Exception as e:
    print(f"  json.dumps error: {e}")

# Try with allow_nan=True
json_str = json.dumps(data, allow_nan=True)
print(f"  json.dumps with allow_nan=True: {json_str}")

# Can we parse it back?
try:
    parsed = json.loads(json_str)
    print(f"  json.loads result: {parsed}")
except Exception as e:
    print(f"  json.loads error: {e}")