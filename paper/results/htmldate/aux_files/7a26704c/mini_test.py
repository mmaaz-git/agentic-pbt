import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from htmldate import validators

# Quick bug hunt
print("Checking for potential bugs...")

# Bug check 1: Does convert_date handle edge cases?
try:
    # Test with same format - should return unchanged per line 173-174
    result = validators.convert_date("2024-01-15", "%Y-%m-%d", "%Y-%m-%d")
    assert result == "2024-01-15", f"Bug: Round-trip failed {result}"
    print("✓ convert_date round-trip works")
except Exception as e:
    print(f"✗ BUG FOUND in convert_date: {e}")

# Bug check 2: Does is_valid_format handle edge cases properly?
try:
    # Empty string should be invalid
    result = validators.is_valid_format("")
    assert result == False, "Bug: Empty format accepted"
    
    # String without % should be invalid
    result = validators.is_valid_format("YYYY-MM-DD")
    assert result == False, "Bug: Format without % accepted"
    
    # Just % alone might cause issues
    result = validators.is_valid_format("%")
    # This should fail during strftime
    print(f"✓ is_valid_format edge cases: % alone returns {result}")
except Exception as e:
    print(f"✗ Potential BUG in is_valid_format: {e}")

# Bug check 3: Boundary validation
try:
    # Test year boundary condition on line 52
    test_date = "2020-01-01"
    earliest = datetime(2020, 1, 1)
    latest = datetime(2020, 1, 1)
    result = validators.is_valid_date(test_date, "%Y-%m-%d", earliest, latest)
    assert result == True, f"Bug: Exact boundary date rejected"
    print("✓ is_valid_date boundary works")
except Exception as e:
    print(f"✗ BUG FOUND in is_valid_date: {e}")

# Bug check 4: Timestamp comparison edge case
try:
    # Check if timestamp comparison handles edge cases properly
    test_date = "2020-01-01"
    earliest = datetime(2020, 1, 1, 0, 0, 1)  # 1 second after midnight
    latest = datetime(2020, 12, 31)
    result = validators.is_valid_date(test_date, "%Y-%m-%d", earliest, latest)
    # This should be False since test_date is at midnight, earlier than 00:00:01
    print(f"  Timestamp edge case: date at midnight vs earliest at 00:00:01 = {result}")
    if result == True:
        print("✗ POTENTIAL BUG: Date at midnight accepted when earliest is 00:00:01")
except Exception as e:
    print(f"✗ Error in timestamp test: {e}")

# Bug check 5: None handling
try:
    result = validators.is_valid_date(None, "%Y-%m-%d", datetime(2020, 1, 1), datetime(2021, 1, 1))
    assert result == False, "Bug: None not handled properly"
    print("✓ None handling works")
except Exception as e:
    print(f"✗ BUG FOUND in None handling: {e}")

print("\nTest completed!")