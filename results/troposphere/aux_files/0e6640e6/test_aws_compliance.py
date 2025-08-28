#!/usr/bin/env python3
"""Check what AWS CloudFormation actually accepts for logical IDs."""

# According to AWS CloudFormation documentation:
# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resources-section-structure.html
#
# Logical IDs must be alphanumeric (A-Za-z0-9) and unique within the template.
# 
# So troposphere's validation is actually correct for AWS CloudFormation compliance,
# but the error message is misleading because it says "not alphanumeric" when 
# it should say "not ASCII alphanumeric" or "contains non-ASCII characters".

print("AWS CloudFormation Logical ID Requirements:")
print("=" * 60)
print("According to AWS documentation, logical IDs must be:")
print("- Alphanumeric (A-Za-z0-9)")
print("- Unique within the template")
print()
print("This means AWS only accepts ASCII alphanumeric characters,")
print("not the full Unicode alphanumeric character set.")
print()
print("The Bug:")
print("-" * 60)
print("The error message 'Name \"...\" not alphanumeric' is misleading")
print("because in Python, 'alphanumeric' typically means any Unicode")
print("alphanumeric character (as determined by str.isalnum()).")
print()
print("A more accurate error message would be:")
print("  'Name \"...\" must contain only ASCII alphanumeric characters (A-Za-z0-9)'")
print("or")
print("  'Name \"...\" contains non-ASCII characters'")