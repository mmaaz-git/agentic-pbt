"""Minimal reproduction of the rounding bug in money.money"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/py-money_env/lib/python3.13/site-packages')

from money.money import Money
from money.currency import Currency

# Test case found by Hypothesis
m = Money("0.01", Currency.AED)
scalar = 0.5

print("Original amount:", m)
print(f"Multiplying by {scalar}:", m * scalar)

multiplied = m * scalar
divided_back = multiplied / scalar

print(f"Dividing back by {scalar}:", divided_back)
print()
print(f"Expected: {m}")
print(f"Got:      {divided_back}")
print()
print(f"Are they equal? {divided_back == m}")

# Let's trace through what's happening
print("\n--- Detailed trace ---")
print(f"Original amount (decimal): {m.amount}")
print(f"After multiplication: {multiplied.amount}")
print(f"After division: {divided_back.amount}")

# Test with more examples
print("\n--- Testing more cases ---")
test_cases = [
    (Money("0.01", Currency.USD), 0.3),
    (Money("0.01", Currency.USD), 0.7),
    (Money("0.02", Currency.USD), 0.5),
    (Money("1.00", Currency.USD), 3.0),
]

for money, scalar in test_cases:
    result = (money * scalar) / scalar
    if result != money:
        print(f"FAIL: ({money} * {scalar}) / {scalar} = {result} (expected {money})")
    else:
        print(f"OK:   ({money} * {scalar}) / {scalar} = {result}")