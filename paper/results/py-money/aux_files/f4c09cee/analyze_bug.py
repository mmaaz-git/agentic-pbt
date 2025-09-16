"""Analyze the rounding bug in money.money"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/py-money_env/lib/python3.13/site-packages')

from decimal import Decimal
from money.money import Money
from money.currency import Currency

# Let's trace through the exact calculations
print("=== Analyzing the bug ===")
print()

m = Money("0.01", Currency.AED)
scalar = 0.5

print(f"Original: {m.amount}")
print(f"Scalar: {scalar}")
print()

# Step 1: Multiplication
print("Step 1: Multiplication")
print(f"  0.01 * 0.5 = {Decimal('0.01') * Decimal('0.5')}")
print(f"  After rounding: {(m * scalar).amount}")
print()

# The multiplication rounds 0.005 to 0.01 (ROUND_HALF_UP)
multiplied = m * scalar

# Step 2: Division
print("Step 2: Division")
print(f"  0.01 / 0.5 = {Decimal('0.01') / Decimal('0.5')}")
print(f"  After rounding: {(multiplied / scalar).amount}")
print()

# The issue is that 0.01 * 0.5 = 0.005, which rounds to 0.01
# Then 0.01 / 0.5 = 0.02

print("=== The problem ===")
print("0.01 * 0.5 = 0.005, which rounds UP to 0.01")
print("0.01 / 0.5 = 0.02")
print()
print("The rounding during multiplication loses precision,")
print("making the inverse operation incorrect.")

# Another failing case
print("\n=== Another example ===")
m2 = Money("0.01", Currency.USD) 
scalar2 = 0.3

print(f"Original: {m2.amount}")
print(f"Scalar: {scalar2}")
print(f"0.01 * 0.3 = {Decimal('0.01') * Decimal('0.3')}")
print(f"After rounding: {(m2 * scalar2).amount}")
print()
# 0.003 rounds to 0.00
multiplied2 = m2 * scalar2
print(f"0.00 / 0.3 = {Decimal('0.00') / Decimal('0.3') if multiplied2.amount != 0 else 'Cannot divide (zero)'}")
print(f"Result: {(multiplied2 / scalar2).amount if multiplied2.amount != 0 else 'N/A'}")