import sys
from datetime import datetime
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.helpers import qb_date_format, qb_datetime_format

dt_999 = datetime(999, 1, 1)
result_date = qb_date_format(dt_999)
print(f"qb_date_format(datetime(999, 1, 1)) = '{result_date}'")
print(f"Expected: '0999-01-01'")
print(f"Bug: Year is not zero-padded to 4 digits")
print()

dt_9 = datetime(9, 12, 31)
result_date2 = qb_date_format(dt_9)
print(f"qb_date_format(datetime(9, 12, 31)) = '{result_date2}'")
print(f"Expected: '0009-12-31'")
print()

result_datetime = qb_datetime_format(dt_999)
print(f"qb_datetime_format(datetime(999, 1, 1)) = '{result_datetime}'")
print(f"Expected: '0999-01-01T00:00:00'")
print(f"Bug: Same issue with datetime formatting")