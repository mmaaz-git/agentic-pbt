"""Reproduction script for validate_and_convert bug"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from htmldate.validators import validate_and_convert

# Setup
min_date = datetime(1900, 1, 1)
max_date = datetime(2100, 1, 1)
date_str = "2000-01-01"  # Valid date string

# This should work but crashes with AttributeError
try:
    result = validate_and_convert(date_str, "%Y-%m-%d", min_date, max_date)
    print(f"Result: {result}")
except AttributeError as e:
    print(f"BUG: AttributeError occurred: {e}")
    print("The function tries to call strftime() on a string instead of a datetime object")