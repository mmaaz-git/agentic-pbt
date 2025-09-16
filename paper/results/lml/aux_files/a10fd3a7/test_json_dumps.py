import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

from lml.utils import json_dumps

# Test that json_dumps works correctly with basic types
test_data = {
    "none": None,
    "bool_true": True,
    "bool_false": False,
    "int": 42,
    "float": 3.14,
    "string": "hello",
    "list": [1, 2, 3],
    "dict": {"nested": "value"},
    "complex": object()  # This should get wrapped
}

print("Testing json_dumps():")
result = json_dumps(test_data)
print(f"Encoded: {result}")

decoded = json.loads(result)
print(f"\nDecoded: {decoded}")

# Check if basic types are preserved
print("\nChecking basic types preservation:")
assert decoded["none"] is None
assert decoded["bool_true"] is True
assert decoded["bool_false"] is False
assert decoded["int"] == 42
assert decoded["float"] == 3.14
assert decoded["string"] == "hello"
assert decoded["list"] == [1, 2, 3]
assert decoded["dict"] == {"nested": "value"}
assert "_python_object" in decoded["complex"]

print("✓ All basic types preserved correctly!")
print("✓ Complex object wrapped correctly!")