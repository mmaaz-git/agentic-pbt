#!/usr/bin/env python3
"""
Minimal reproduction of no_validation() bug in troposphere.waf
"""

import troposphere.waf as waf

# Demonstrate the bug
print("=== BUG REPRODUCTION ===")
print()
print("The no_validation() method should disable validation, but it doesn't work.")
print()

# Step 1: Create valid Action
action = waf.Action(Type="ALLOW")
print(f"1. Created Action with Type='ALLOW'")

# Step 2: Call no_validation() which should disable validation
action.no_validation()
print(f"2. Called no_validation() - do_validation is now: {action.do_validation}")

# Step 3: Try to set invalid value - this should work with validation disabled
print("3. Attempting to set Type='INVALID' after calling no_validation()...")
try:
    action.Type = "INVALID"
    print("   SUCCESS: Set invalid type (validation was disabled)")
except ValueError as e:
    print(f"   FAILURE: Validation still active despite no_validation(): {e}")

print()
print("=== EXPECTED vs ACTUAL ===")
print("EXPECTED: no_validation() should disable validation, allowing invalid values")
print("ACTUAL: Validation occurs in __setattr__ and ignores do_validation flag")

print()
print("=== IMPACT ===")
print("- The no_validation() method exists but doesn't work as documented")
print("- Users cannot bypass validation even when explicitly requested")
print("- This breaks the ability to work with non-standard or custom WAF actions")