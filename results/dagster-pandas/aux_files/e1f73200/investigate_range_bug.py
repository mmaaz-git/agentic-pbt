import sys as sys_module
import sys
from datetime import datetime
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages/')

from dagster_pandas.constraints import column_range_validation_factory

# Investigate the bug with extreme ranges
print("Testing extreme numeric ranges...")
print(f"sys.maxsize = {sys_module.maxsize}")
print(f"-sys.maxsize = {-sys_module.maxsize}")

# Test with no min specified (should use system min according to the code)
validator_no_min = column_range_validation_factory(None, 0)

# Test various negative values
test_values = [
    -sys_module.maxsize,
    -sys_module.maxsize + 1,
    -(sys_module.maxsize - 1),
    -1000,
    -1,
    0,
    1
]

print("\nTesting with validator(None, 0):")
for val in test_values:
    result, metadata = validator_no_min(val)
    print(f"  validator({val}): {result}")

# Let's look at what the actual min value is being set to
print("\nLet's check what happens inside the factory...")

# Recreate the logic from the source
minim = None
maxim = 0

if minim is None:
    if isinstance(maxim, datetime):
        from datetime import datetime
        minim = datetime.min
    else:
        minim = -1 * (sys_module.maxsize - 1)
        
print(f"When minim=None and maxim=0 (int), minim is set to: {minim}")
print(f"This equals: -{sys_module.maxsize - 1} = {-1 * (sys_module.maxsize - 1)}")

# Now test the actual values
print(f"\nIs -sys.maxsize <= {minim}? {-sys_module.maxsize <= minim}")
print(f"Is -(sys.maxsize - 1) <= {minim}? {-(sys_module.maxsize - 1) <= minim}")

# The issue is that -sys.maxsize is LESS than -(sys.maxsize - 1)
print(f"\n-sys.maxsize = {-sys_module.maxsize}")
print(f"-(sys.maxsize - 1) = {-(sys_module.maxsize - 1)}")
print(f"-sys.maxsize < -(sys.maxsize - 1)? {-sys_module.maxsize < -(sys_module.maxsize - 1)}")

print("\nThis is a BUG! The code sets minim = -(sys.maxsize - 1) which is actually")
print("GREATER than -sys.maxsize, so -sys.maxsize fails the range check!")