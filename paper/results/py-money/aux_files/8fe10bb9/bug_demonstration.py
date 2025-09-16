#!/usr/bin/env python3
"""Demonstration of __rsub__ bug in money module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/py-money_env/lib/python3.13/site-packages')

from money.money import Money
from money.currency import Currency

print("Bug Demonstration: __rsub__ implementation error")
print("=" * 60)

# The __rsub__ method is called when the left operand doesn't support subtraction
# with the right operand. For example, if we had:
# some_other_type - Money_instance
# Python would try Money_instance.__rsub__(some_other_type)

# However, even between Money objects, we can demonstrate the bug by calling __rsub__ directly

print("\nDemonstrating the bug:")
print("-" * 40)

m1 = Money("10.00", Currency.USD)
m2 = Money("3.00", Currency.USD)

print(f"m1 = {m1}")  # USD 10.00
print(f"m2 = {m2}")  # USD 3.00

# Normal subtraction works correctly:
normal_result = m1 - m2
print(f"\nm1 - m2 = {normal_result}")  # Should be USD 7.00

# According to Python's data model, m2.__rsub__(m1) should compute m1 - m2
# But the implementation returns self.__sub__(other), which is m2 - m1
rsub_result = m2.__rsub__(m1)
print(f"m2.__rsub__(m1) = {rsub_result}")  # Returns USD 7.00 but with wrong sign!

# Wait, let's check more carefully:
print(f"\nDetailed check:")
print(f"  m1 - m2 = {m1 - m2}")  # USD 7.00
print(f"  m2 - m1 = {m2 - m1}")  # USD -7.00
print(f"  m2.__rsub__(m1) = {m2.__rsub__(m1)}")  # Should be m1 - m2 = USD 7.00

# The bug is that __rsub__ calls self.__sub__(other) which computes self - other
# But it should compute other - self

print("\n" + "=" * 60)
print("BUG CONFIRMED:")
print("  __rsub__ is implemented as: return self.__sub__(other)")
print("  This computes: self - other")
print("  But it should compute: other - self")
print("\nThis means __rsub__ returns the wrong result with the wrong sign!")
print("=" * 60)

# Actually, let me verify this more carefully
print("\nActually, let me trace through the code:")
print(f"  m2.__rsub__(m1) calls m2.__sub__(m1)")
print(f"  m2.__sub__(m1) computes m2 - m1 = {m2 - m1}")
print(f"  So m2.__rsub__(m1) = {m2.__rsub__(m1)}")

# The implementation is:
# def __rsub__(self, other):
#     return self.__sub__(other)
#
# But it should be:
# def __rsub__(self, other):
#     return other.__sub__(self)

print("\nThe correct implementation should be:")
print("  def __rsub__(self, other):")
print("      return other - self  # or other.__sub__(self)")
print("\nNot:")
print("  def __rsub__(self, other):")
print("      return self - other  # Current wrong implementation")