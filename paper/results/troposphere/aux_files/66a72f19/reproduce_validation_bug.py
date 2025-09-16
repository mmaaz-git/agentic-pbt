#!/usr/bin/env python3

import troposphere.rolesanywhere as ra

# Create a CRL object without required properties
crl = ra.CRL('TestCRL')

# The validate() method should fail but doesn't
print("Calling crl.validate()...")
crl.validate()
print("✓ validate() passed (BUG: should have failed!)")

# The to_dict() method correctly fails
print("\nCalling crl.to_dict()...")
try:
    crl.to_dict()
    print("✓ to_dict() passed (unexpected)")
except ValueError as e:
    print(f"✗ to_dict() failed with: {e}")

print("\nThis demonstrates the bug: validate() doesn't check required properties")
print("but to_dict() does, leading to inconsistent validation behavior.")