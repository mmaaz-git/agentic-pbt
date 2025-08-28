#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""Minimal reproduction of CustomActionAttachmentCriteria bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import chatbot

# According to the props definition in chatbot.py line 21-23:
# "Value": (str, False)  # False means optional
# This should mean Value can be omitted or set to None

# Test 1: Try creating without Value field
print("Test 1: Creating CustomActionAttachmentCriteria without Value...")
try:
    criteria1 = chatbot.CustomActionAttachmentCriteria(
        Operator="=",
        VariableName="test_var"
    )
    print("✓ Success - Created without Value field")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 2: Try creating with Value=None explicitly
print("\nTest 2: Creating CustomActionAttachmentCriteria with Value=None...")
try:
    criteria2 = chatbot.CustomActionAttachmentCriteria(
        Operator="=",
        VariableName="test_var",
        Value=None  # Explicitly set to None
    )
    print("✓ Success - Created with Value=None")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 3: Try with empty string
print("\nTest 3: Creating CustomActionAttachmentCriteria with Value=''...")
try:
    criteria3 = chatbot.CustomActionAttachmentCriteria(
        Operator="=",
        VariableName="test_var",
        Value=""  # Empty string
    )
    print("✓ Success - Created with Value=''")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 4: Try with valid string value
print("\nTest 4: Creating CustomActionAttachmentCriteria with Value='test'...")
try:
    criteria4 = chatbot.CustomActionAttachmentCriteria(
        Operator="=",
        VariableName="test_var",
        Value="test"  # Valid string
    )
    print("✓ Success - Created with Value='test'")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n" + "="*60)
print("SUMMARY:")
print("The Value property is marked as optional (False) in props,")
print("but passing None explicitly causes a TypeError.")
print("This is inconsistent behavior - optional properties should")
print("accept None or allow omission.")