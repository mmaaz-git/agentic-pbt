import sys
from datetime import datetime, timedelta

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages')

from dagster_pandas.constraints import column_range_validation_factory

# Reproduce the failing case
base_date = datetime(2023, 1, 1)
min_date = None  # use_min=False
max_date = None  # use_max=False
test_date = base_date  # days_offset=0

print(f"Testing with min_date={min_date}, max_date={max_date}, test_date={test_date}")

validator = column_range_validation_factory(minim=min_date, maxim=max_date)
result, metadata = validator(test_date)

print(f"Result: {result}")
print(f"Metadata: {metadata}")

# What should happen:
# According to the code, when minim is None and maxim is None,
# it should check if maxim is a datetime, but maxim is None
# So it falls back to sys.maxsize

# Let's check what the validation function is actually doing
print("\n--- Debugging the validator function ---")
print(f"Validator docstring: {validator.__doc__}")

# Let's manually trace through what should happen in the validator
import sys as sys_module
minim = min_date
maxim = max_date

if minim is None:
    if isinstance(maxim, datetime):
        print(f"maxim is datetime: {isinstance(maxim, datetime)}")
        minim = datetime.min
    else:
        print(f"maxim is NOT datetime, setting minim to -{sys_module.maxsize - 1}")
        minim = -1 * (sys_module.maxsize - 1)
        
if maxim is None:
    if isinstance(minim, datetime):
        print(f"minim is datetime: {isinstance(minim, datetime)}")
        maxim = datetime.max
    else:
        print(f"minim is NOT datetime, setting maxim to {sys_module.maxsize}")
        maxim = sys_module.maxsize

print(f"\nEffective minim: {minim} (type: {type(minim)})")
print(f"Effective maxim: {maxim} (type: {type(maxim)})")
print(f"Test date: {test_date} (type: {type(test_date)})")

# Now the actual check in the validator
x = test_date
check_result = (isinstance(x, (type(minim), type(maxim)))) and (x <= maxim) and (x >= minim)
print(f"\nCheck: isinstance({x}, ({type(minim)}, {type(maxim)})) = {isinstance(x, (type(minim), type(maxim)))}")
print(f"Result of check: {check_result}")