"""Minimal reproduction of the bug found in test_exclude_unset_behavior"""

from pydantic import BaseModel
from typing import Optional

# Create model with default values
class UnsetModel(BaseModel):
    required: str = "required"
    optional: Optional[str] = None

# Create instance without providing any values
model = UnsetModel()

print("Model created without arguments:")
print(f"  model.required = {model.required}")
print(f"  model.optional = {model.optional}")

# Dump with exclude_unset=True
dumped = model.model_dump(exclude_unset=True)
print("\nmodel.model_dump(exclude_unset=True):")
print(f"  Result: {dumped}")

# The issue: when exclude_unset=True, even fields with default values
# are excluded if they weren't explicitly set during instantiation
print("\nExpected 'required' field to be in the output since it has a value")
print(f"Is 'required' in dumped? {'required' in dumped}")

# Let's also test what happens when we explicitly set the value
model2 = UnsetModel(required="required")
dumped2 = model2.model_dump(exclude_unset=True)
print("\nWhen explicitly setting required='required':")
print(f"  model_dump(exclude_unset=True): {dumped2}")

# And with a different value
model3 = UnsetModel(required="custom")
dumped3 = model3.model_dump(exclude_unset=True)
print("\nWhen setting required='custom':")
print(f"  model_dump(exclude_unset=True): {dumped3}")