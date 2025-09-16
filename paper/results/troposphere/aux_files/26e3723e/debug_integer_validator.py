"""Debug integer validator accepting floats."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer

print("Testing integer validator:")

test_values = [
    42,
    "42",
    3.14,
    "3.14",
    3.0,
    "not_a_number"
]

for value in test_values:
    try:
        result = integer(value)
        print(f"integer({value!r}) = {result!r} (type: {type(result).__name__})")
    except ValueError as e:
        print(f"integer({value!r}) raised ValueError: {e}")
    except Exception as e:
        print(f"integer({value!r}) raised {type(e).__name__}: {e}")

print("\nChecking int() behavior:")
for value in [3.14, 3.0, "42"]:
    try:
        result = int(value)
        print(f"int({value!r}) = {result!r}")
    except Exception as e:
        print(f"int({value!r}) raised {type(e).__name__}: {e}")