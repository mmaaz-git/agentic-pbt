import sys
from datetime import datetime

# Add the venv site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/dagster-pandas_env/lib/python3.13/site-packages')

from dagster_pandas.constraints import column_range_validation_factory

# Test with integers - this should work
validator = column_range_validation_factory(minim=None, maxim=None)

test_int = 42
result_int, _ = validator(test_int)
print(f"Testing integer 42 with no bounds: {result_int} (Expected: True)")

test_float = 3.14
result_float, _ = validator(test_float)
print(f"Testing float 3.14 with no bounds: {result_float} (Expected: True)")

test_datetime = datetime(2023, 1, 1)
result_datetime, _ = validator(test_datetime)
print(f"Testing datetime with no bounds: {result_datetime} (Expected: True)")

# The bug: when both bounds are None, the validator defaults to integer type checking
# This breaks for non-integer types like datetime