"""Confirm the validation bug with do_validation flag"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.controltower import EnabledBaseline

print("Confirming validation bug:")
print("=" * 50)

print("\n1. Object created with validation=False:")
baseline1 = EnabledBaseline("Test1", validation=False)
print(f"   do_validation = {baseline1.do_validation}")
try:
    result = baseline1.to_dict(validation=True)
    print(f"   ✗ to_dict(validation=True) succeeded: {result}")
    print("   BUG: validation=True parameter is ignored when do_validation=False!")
except ValueError as e:
    print(f"   ✓ Validation failed: {e}")

print("\n2. Object created with validation=True (default):")
baseline2 = EnabledBaseline("Test2")  # validation=True by default
print(f"   do_validation = {baseline2.do_validation}")
try:
    result = baseline2.to_dict(validation=True)
    print(f"   ✗ to_dict succeeded: {result}")
except ValueError as e:
    print(f"   ✓ Validation failed correctly: {e}")

print("\nActual Bug Summary:")
print("=" * 50)
print("The to_dict method checks BOTH validation parameter AND do_validation attribute")
print("Line 338: if validation and self.do_validation:")
print("This means objects created with validation=False can NEVER be validated later!")
print("This is likely a design flaw, not just a bug.")