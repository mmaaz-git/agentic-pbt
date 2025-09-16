import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere.validators import boolean

# Test the specific failing case
test_values = [
    0.0,  # The failing case from Hypothesis
    1.0,  # Let's also test 1.0
    0,    # Integer 0 (should return False)
    1,    # Integer 1 (should return True)
    "0",  # String "0" (should return False)
    "1",  # String "1" (should return True)
]

print("Testing boolean validator with various values:")
for value in test_values:
    try:
        result = boolean(value)
        print(f"boolean({value!r}) = {result}")
    except ValueError as e:
        print(f"boolean({value!r}) raised ValueError")

# Let's also check the source more carefully
import inspect
print("\nSource of boolean validator:")
print(inspect.getsource(boolean))