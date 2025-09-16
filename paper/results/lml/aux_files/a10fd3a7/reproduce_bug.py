import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

from lml.utils import PythonObjectEncoder

encoder = PythonObjectEncoder()

# Test basic types that should pass through
test_values = [
    None,
    True,
    False,
    42,
    3.14,
    "hello",
    [1, 2, 3],
    {"key": "value"}
]

print("Testing PythonObjectEncoder.default() with basic types:")
for value in test_values:
    try:
        result = encoder.default(value)
        print(f"✓ {value!r} -> {result}")
    except TypeError as e:
        print(f"✗ {value!r} -> TypeError: {e}")