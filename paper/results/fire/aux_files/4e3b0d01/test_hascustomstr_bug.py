"""Minimal reproduction of HasCustomStr bug."""

import fire.value_types as vt

# According to the docstring: "This means that the __str__ methods of 
# primitives like ints and floats are considered custom."

# Test various primitives
test_cases = [
    (42, "int"),
    (3.14, "float"),
    (True, "bool"),
    (1+2j, "complex"),
]

print("HasCustomStr results for primitives:")
print("=" * 50)

for value, type_name in test_cases:
    result = vt.HasCustomStr(value)
    print(f"{type_name:10} value={value:10} HasCustomStr={result}")

print("\n" + "=" * 50)
print("BUG: The docstring claims primitives like ints and floats")
print("should have custom __str__, but they return False.")

# Demonstrate the underlying issue
import fire.inspectutils as inspectutils

print("\nUnderlying cause:")
class_attrs = inspectutils.GetClassAttrsDict(int)
str_attr = class_attrs.get('__str__')
print(f"int.__str__ is defined by: {str_attr.defining_class}")
print(f"Is that 'object'? {str_attr.defining_class is object}")
print("Since it's defined by 'object', HasCustomStr returns False")
print("This contradicts the function's documented behavior.")