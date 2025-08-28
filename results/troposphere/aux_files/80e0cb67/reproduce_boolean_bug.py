import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
from troposphere.validators import boolean

# The boolean validator should only accept specific values as documented:
# True values: True, 1, "1", "true", "True"  
# False values: False, 0, "0", "false", "False"
# All other values should raise ValueError

# BUG: Float values are incorrectly accepted
print("Testing float 0.0 (should raise ValueError but returns False):")
result = boolean(0.0)
print(f"boolean(0.0) = {result}")

print("\nTesting float 1.0 (should raise ValueError but returns True):")
result = boolean(1.0)
print(f"boolean(1.0) = {result}")

print("\nTesting float 0.5 (correctly raises ValueError):")
try:
    result = boolean(0.5)
    print(f"boolean(0.5) = {result}")
except ValueError:
    print("boolean(0.5) raised ValueError as expected")

# The issue is that Python's 'in' operator considers 0.0 == 0 and 1.0 == 1
print("\nDemonstrating the root cause:")
print(f"0.0 in [0, False] = {0.0 in [0, False]}")
print(f"1.0 in [1, True] = {1.0 in [1, True]}")