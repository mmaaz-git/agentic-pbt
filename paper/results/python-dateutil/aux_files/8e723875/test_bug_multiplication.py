#!/usr/bin/env python3
"""Focused test for multiplication bug in relativedelta."""

from dateutil.relativedelta import relativedelta

# Bug: Multiplication triggers _fix() which normalizes months incorrectly
rd = relativedelta(months=4)
result = rd * 3.0

print(f"relativedelta(months=4) * 3.0 = {result}")
print(f"Expected: relativedelta(months=+12)")
print(f"Actual:   {result}")

# The bug is that _fix() is called, which converts 12 months to 1 year
# But multiplication should preserve the exact representation
assert result.months == 12, f"Expected months=12, got months={result.months}"
assert result.years == 0, f"Expected years=0, got years={result.years}"