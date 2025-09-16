import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import inspector, Template

# Demonstrate the bug: Empty string title bypasses validation
print("Bug Reproduction: Empty Title Validation Bypass")
print("=" * 50)

# Create resources with empty/None titles (should fail but doesn't)
target_empty = inspector.AssessmentTarget('')
target_none = inspector.AssessmentTarget(None)

print("Created AssessmentTarget with empty string title - Should have failed!")
print(f"  target.title = {repr(target_empty.title)}")

print("\nCreated AssessmentTarget with None title - Should have failed!")
print(f"  target.title = {repr(target_none.title)}")

# Add to template to show it generates invalid CloudFormation
template = Template()
template.add_resource(target_empty)
template.add_resource(target_none)

print("\nGenerated CloudFormation template:")
import json
output = json.loads(template.to_json())
print(json.dumps(output, indent=2))

print("\n" + "=" * 50)
print("ISSUE: AWS CloudFormation requires resource names to be alphanumeric.")
print("Empty or None resource names will cause deployment failures.")
print("The library should validate this at object creation time.")

# Show that calling validate_title directly would catch this
print("\n" + "=" * 50)
print("If validate_title() was actually called, it would catch this:")
try:
    target_empty.validate_title()
except ValueError as e:
    print(f"Empty string: {e}")

try:
    target_none.validate_title()
except ValueError as e:
    print(f"None: {e}")