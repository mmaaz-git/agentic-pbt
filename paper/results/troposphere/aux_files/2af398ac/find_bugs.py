#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean, integer, double
import troposphere.budgets as budgets

print("=== Looking for bugs in troposphere.budgets ===\n")

# Bug Hunt 1: Boolean validator edge cases
print("Test 1: Boolean validator with string '1'")
# According to the code, it checks if x in [True, 1, "1", "true", "True"]
# But there's a potential issue here - let me test it
try:
    # This should work according to the code
    result = boolean("1")
    print(f"  boolean('1') = {result} (type: {type(result)})")
    assert result is True
    print("  ✓ Passed")
except Exception as e:
    print(f"  ✗ FAILED: {e}")

# Bug Hunt 2: Integer validator preserves input type
print("\nTest 2: Integer validator preserves the original input")
# The integer function returns x directly without converting to int
test_val = "42"
result = integer(test_val)
print(f"  integer('42') returns: {result!r} (type: {type(result)})")
print(f"  Original value: {test_val!r} (type: {type(test_val)})")
print(f"  Are they the same object? {result is test_val}")
# This could be a problem if code expects actual integers but gets strings

# Bug Hunt 3: Double validator also preserves input type
print("\nTest 3: Double validator preserves the original input")
test_val = "3.14"
result = double(test_val)
print(f"  double('3.14') returns: {result!r} (type: {type(result)})")
# This means if you pass a string, you get a string back, not a float!

# Bug Hunt 4: Testing Spend object with string numbers
print("\nTest 4: Creating Spend with string number")
try:
    # Since double() accepts strings and returns them as-is,
    # this should work but the Amount will be a string
    spend = budgets.Spend(Amount="100.50", Unit="USD")
    print(f"  Created Spend with Amount='100.50'")
    print(f"  spend.properties['Amount'] = {spend.properties['Amount']!r} (type: {type(spend.properties['Amount'])})")
    
    # Convert to dict
    spend_dict = spend.to_dict()
    print(f"  spend.to_dict()['Amount'] = {spend_dict['Amount']!r} (type: {type(spend_dict['Amount'])})")
except Exception as e:
    print(f"  ✗ FAILED: {e}")

# Bug Hunt 5: Testing with invalid but parseable values
print("\nTest 5: Testing integer validator with float that has no decimal part")
try:
    result = integer(10.0)
    print(f"  integer(10.0) = {result} (should work since int(10.0) succeeds)")
except ValueError as e:
    print(f"  integer(10.0) raised ValueError: {e}")

print("\nTest 6: Testing integer validator with float that has decimal part")
try:
    result = integer(10.5)
    print(f"  ✗ BUG: integer(10.5) = {result} (should fail but doesn't!)")
except ValueError as e:
    print(f"  ✓ integer(10.5) correctly raised ValueError: {e}")

# Bug Hunt 6: Testing CostTypes with string booleans
print("\nTest 7: CostTypes with mixed boolean types")
ct = budgets.CostTypes(
    IncludeCredit="true",  # string
    IncludeDiscount=1,      # integer
    IncludeTax=True,        # actual boolean
    IncludeRefund="false"   # string
)
print(f"  Created CostTypes with mixed boolean inputs")
for key in ["IncludeCredit", "IncludeDiscount", "IncludeTax", "IncludeRefund"]:
    val = ct.properties.get(key)
    print(f"    {key}: {val!r} (type: {type(val)}, is True: {val is True}, is False: {val is False})")

# Bug Hunt 7: Historical options with string integer
print("\nTest 8: HistoricalOptions with string integer")
try:
    ho = budgets.HistoricalOptions(BudgetAdjustmentPeriod="30")
    print(f"  Created HistoricalOptions with BudgetAdjustmentPeriod='30'")
    print(f"  Value stored: {ho.properties['BudgetAdjustmentPeriod']!r} (type: {type(ho.properties['BudgetAdjustmentPeriod'])})")
except Exception as e:
    print(f"  ✗ Failed to create: {e}")

print("\n=== Summary ===")
print("Potential issues found:")
print("1. integer() and double() validators don't convert - they return the input as-is")
print("2. This means string numbers are stored as strings in AWS objects")
print("3. integer() accepts floats like 10.5 without error (int(10.5) = 10)")
print("4. Type inconsistency: properties can have mixed types for the same logical type")