#!/usr/bin/env python3
"""Bug: troposphere.backupgateway accepts empty string as title"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import backupgateway

print("Testing empty string as Hypervisor title...")

try:
    # This should fail but doesn't!
    h = backupgateway.Hypervisor('')
    print(f"BUG FOUND: Empty string accepted as title!")
    print(f"to_dict() output: {h.to_dict()}")
    
    # Try to validate explicitly
    h.validate_title()
    print("validate_title() also passed - this is wrong!")
    
except ValueError as e:
    print(f"Correctly rejected: {e}")

print("\nAnalysis:")
print("The validation code checks: 'if not self.title or not valid_names.match(self.title)'")
print("When title is empty string:")
print("  - 'not self.title' evaluates to True (empty string is falsy)")
print("  - This should trigger the ValueError, but the logic is backwards!")
print("The condition should raise error when title is empty OR doesn't match pattern.")