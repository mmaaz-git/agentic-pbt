#!/usr/bin/env python3
"""Debug why title validation is failing"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.mediaconvert as mc
import troposphere

print("Debugging title validation...")

# Check the validate_title method
print("\n1. Looking at validate_title method:")
print(f"  valid_names pattern: {troposphere.valid_names.pattern}")

# Test the regex directly
print("\n2. Testing regex directly:")
test_cases = ["", None, "Valid123", "test-name"]
for test in test_cases:
    if test is None:
        print(f"  None: Cannot match regex")
    else:
        match = troposphere.valid_names.match(test)
        print(f"  '{test}': match = {bool(match)}")

# Check what happens in __init__
print("\n3. Tracing through __init__:")

class DebugJobTemplate(mc.JobTemplate):
    def validate_title(self):
        print(f"    validate_title called with title={self.title!r}")
        if not self.title:
            print(f"    Empty/None title detected: not self.title = {not self.title}")
        if self.title and not troposphere.valid_names.match(self.title):
            print(f"    Non-alphanumeric title detected")
        super().validate_title()

# Test with empty string
print("  Creating with empty string:")
try:
    jt = DebugJobTemplate("", SettingsJson={})
    print(f"    SUCCESS: Object created with title={jt.title!r}")
except ValueError as e:
    print(f"    FAILED: {e}")

# Test with None
print("\n  Creating with None:")
try:
    jt2 = DebugJobTemplate(None, SettingsJson={})
    print(f"    SUCCESS: Object created with title={jt2.title!r}")
except (ValueError, TypeError) as e:
    print(f"    FAILED: {e}")

# Check the actual validation logic in BaseAWSObject
print("\n4. Checking BaseAWSObject.validate_title logic:")
print("  The condition is: if not self.title or not valid_names.match(self.title)")
print(f"  For empty string: not '' = {not ''} (should trigger error)")
print(f"  For None: not None = {not None} (should trigger error)")

# But the error message says "not alphanumeric", let's see
print("\n5. Testing the actual validation:")
jt_test = mc.JobTemplate("test", SettingsJson={})
jt_test.title = ""
try:
    jt_test.validate_title()
    print("  Empty title validation PASSED (BUG!)")
except ValueError as e:
    print(f"  Empty title validation failed: {e}")

jt_test.title = None
try:
    jt_test.validate_title()
    print("  None title validation PASSED (BUG!)")
except ValueError as e:
    print(f"  None title validation failed: {e}")