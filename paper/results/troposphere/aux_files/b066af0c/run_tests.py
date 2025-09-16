#!/usr/bin/env python3
"""Runner script for property-based tests"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import string
from hypothesis import assume, given, strategies as st, settings, example
import troposphere.iot as iot
from troposphere import Ref, GetAtt, Tags


# Test 1: Title validation
print("Testing title validation property...")
try:
    # Valid title should work
    cert = iot.Certificate(title="ValidTitle123", Status="ACTIVE")
    print("✓ Valid alphanumeric title accepted")
except Exception as e:
    print(f"✗ Valid title rejected: {e}")

try:
    # Invalid title with spaces should fail
    cert = iot.Certificate(title="Invalid Title", Status="ACTIVE")
    print("✗ Invalid title with spaces was accepted (BUG!)")
except ValueError as e:
    print("✓ Invalid title with spaces rejected")

try:
    # Empty title should fail
    cert = iot.Certificate(title="", Status="ACTIVE")
    print("✗ Empty title was accepted (BUG!)")
except ValueError as e:
    print("✓ Empty title rejected")

# Test 2: Required properties
print("\nTesting required property enforcement...")
try:
    cert = iot.Certificate(title="TestCert")
    cert.to_dict()
    print("✗ Certificate without Status did not raise (BUG!)")
except ValueError as e:
    if "Status required" in str(e):
        print("✓ Missing required Status property caught")
    else:
        print(f"✗ Unexpected error: {e}")

# Test 3: Type validation
print("\nTesting type validation...")
try:
    config = iot.AuditCheckConfiguration()
    config.Enabled = True
    print("✓ Boolean property accepts bool")
except Exception as e:
    print(f"✗ Boolean property rejected bool: {e}")

try:
    config = iot.AuditCheckConfiguration()
    config.Enabled = "not a bool"
    print("✗ Boolean property accepted string (BUG!)")
except TypeError:
    print("✓ Boolean property rejected string")

# Test 4: Round-trip serialization  
print("\nTesting round-trip serialization...")
try:
    thing1 = iot.Thing(title="Thing1", ThingName="TestThing")
    dict1 = thing1.to_dict()
    thing2 = iot.Thing.from_dict(title="Thing1", d=dict1["Properties"])
    dict2 = thing2.to_dict()
    
    if dict1 == dict2:
        print("✓ Round-trip serialization preserved data")
    else:
        print("✗ Round-trip serialization changed data (BUG!)")
        print(f"  Original: {dict1}")
        print(f"  After:    {dict2}")
except Exception as e:
    print(f"✗ Round-trip test failed: {e}")

# Test 5: Empty string edge case
print("\nTesting edge cases...")
try:
    thing = iot.Thing(title="TestThing", ThingName="")
    if thing.ThingName == "":
        print("✓ Empty string accepted for string property")
    else:
        print("✗ Empty string was modified")
except Exception as e:
    print(f"✗ Empty string test failed: {e}")

# Test 6: Special test for potential title validation bug
print("\nSpecial test for title validation edge cases...")

# Testing what characters are actually allowed
test_titles = [
    ("ABC123", True),  # Should pass
    ("Test_Name", False),  # Should fail (underscore)
    ("Test-Name", False),  # Should fail (hyphen)  
    ("Test Name", False),  # Should fail (space)
    ("TestName!", False),  # Should fail (exclamation)
    ("", False),  # Should fail (empty)
    ("123", True),  # Should pass (numbers only)
    ("test", True),  # Should pass (letters only)
]

for title, should_pass in test_titles:
    try:
        cert = iot.Certificate(title=title, Status="ACTIVE")
        if should_pass:
            print(f"✓ Title '{title}' accepted as expected")
        else:
            print(f"✗ Title '{title}' accepted but should have failed (BUG!)")
    except ValueError:
        if not should_pass:
            print(f"✓ Title '{title}' rejected as expected")
        else:
            print(f"✗ Title '{title}' rejected but should have passed (BUG!)")

print("\n" + "="*50)
print("Testing complete!")