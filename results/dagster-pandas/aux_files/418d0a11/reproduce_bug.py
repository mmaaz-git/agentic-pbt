import sys
from datetime import datetime

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages')

from dagster_pandas.constraints import column_range_validation_factory

# Bug: When minim and maxim are both None, the function incorrectly handles datetime values
# It defaults to integer bounds but then fails the type check for datetime values

# Minimal reproduction
validator = column_range_validation_factory(minim=None, maxim=None)
test_datetime = datetime(2023, 1, 1)

result, _ = validator(test_datetime)
print(f"Testing datetime(2023, 1, 1) with no bounds specified: {result}")
print(f"Expected: True (no bounds means accept all values)")
print(f"Actual: {result}")

# This should accept ANY value when no bounds are specified, including datetimes
# But it fails because the function defaults to integer types when both bounds are None