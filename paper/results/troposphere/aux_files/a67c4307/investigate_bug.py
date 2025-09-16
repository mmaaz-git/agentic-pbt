import troposphere
from troposphere import BaseAWSObject
import re

# Recreate the validation logic
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

def validate_title_logic(title):
    """Mimics the validate_title method"""
    if not title or not valid_names.match(title):
        raise ValueError('Name "%s" not alphanumeric' % title)

# Test the logic
print("Testing validation logic with empty string:")
try:
    validate_title_logic("")
    print("ERROR: Empty string was accepted!")
except ValueError as e:
    print(f"Empty string rejected with: {e}")

print("\n" + "="*50 + "\n")

# Now let's look at what's happening in the actual code
print("Testing actual BaseAWSObject behavior:")

# Looking at the __init__ method, line 183-184:
# if self.title:
#     self.validate_title()

# This means validation only happens if self.title is truthy!
# Empty string is falsy, so validation is skipped!

print("The bug is in __init__ line 183-184:")
print("    if self.title:")
print("        self.validate_title()")
print("")
print("Empty string is falsy, so validate_title() is never called!")
print("")

# Let's confirm this
import troposphere.route53recoverycontrol as r53rc

print("Creating cluster with empty title:")
cluster = r53rc.Cluster(title="", Name="TestName")
print(f"  title = '{cluster.title}'")
print(f"  Validation was skipped!")

print("\nCalling validate_title() directly on empty title:")
try:
    cluster.validate_title()
    print("  ERROR: validate_title() accepted empty string!")
except ValueError as e:
    print(f"  validate_title() correctly rejected: {e}")

print("\n" + "="*50 + "\n")
print("BUG CONFIRMED:")
print("1. Empty string titles bypass validation in __init__")
print("2. The check 'if self.title:' treats empty string as falsy")
print("3. This allows invalid empty titles to be created")
print("4. The validation function itself would reject empty strings")