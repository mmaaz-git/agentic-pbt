#!/usr/bin/env python3
"""Minimal reproduction of the title validation bug in troposphere.backupgateway"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import backupgateway

# Character 'µ' (micro sign) is considered alphanumeric by Python
# but rejected by troposphere's validation
test_char = 'µ'
print(f"Testing character: '{test_char}'")
print(f"Python considers it alphanumeric: {test_char.isalnum()}")

try:
    h = backupgateway.Hypervisor(test_char)
    print("SUCCESS: Hypervisor created with title 'µ'")
except ValueError as e:
    print(f"FAILED: {e}")
    print("\nThis is a bug because:")
    print("1. Python's isalnum() returns True for 'µ'")
    print("2. The character is a valid Unicode letter (category Ll)")
    print("3. CloudFormation resource names should accept Unicode letters")
    print("4. The regex [a-zA-Z0-9]+ is too restrictive for international users")