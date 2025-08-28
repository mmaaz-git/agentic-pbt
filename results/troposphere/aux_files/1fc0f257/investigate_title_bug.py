"""Investigate the empty title validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.iotthingsgraph import DefinitionDocument, FlowTemplate
import re

print("Investigating empty title validation bug...")
print("=" * 60)

# Look at the validation pattern
print("\n1. Checking the validation regex pattern:")
print("   Pattern from code: ^[a-zA-Z0-9]+$")

valid_names = re.compile(r"^[a-zA-Z0-9]+$")

test_titles = ["", " ", "Valid", "Invalid-", "123", "  "]

for title in test_titles:
    match = valid_names.match(title)
    print(f"   '{title}' matches: {bool(match)}")

print("\n2. Testing FlowTemplate with various empty/whitespace titles:")

definition = DefinitionDocument(Language="GRAPHQL", Text="{}")

test_cases = [
    ("", "empty string"),
    (" ", "single space"),
    ("  ", "multiple spaces"),
    ("\t", "tab"),
    ("\n", "newline"),
    (None, "None")
]

for title, description in test_cases:
    print(f"\n   Testing {description} (title={title!r}):")
    try:
        template = FlowTemplate(title, Definition=definition)
        print(f"     ✗ UNEXPECTED: FlowTemplate created successfully")
        print(f"     Template title: {template.title!r}")
        
        # Try to validate
        try:
            template.validate_title()
            print(f"     ✗ validate_title() passed (should have failed)")
        except ValueError as e:
            print(f"     ✓ validate_title() raised: {e}")
            
        # Try to convert to dict
        try:
            result = template.to_dict()
            print(f"     ? to_dict() succeeded: Type={result.get('Type')}")
        except Exception as e:
            print(f"     ? to_dict() raised: {e}")
            
    except Exception as e:
        print(f"     ✓ FlowTemplate raised: {e}")

print("\n3. Checking validate_title implementation:")

# Let's manually check the validation logic
def manual_validate_title(title):
    if not title or not valid_names.match(title):
        raise ValueError('Name "%s" not alphanumeric' % title)
    return True

test_titles = ["", None, "Valid", "Invalid-"]
for title in test_titles:
    try:
        manual_validate_title(title)
        print(f"   '{title}': Validation passed")
    except ValueError as e:
        print(f"   '{title}': {e}")

print("\n4. Checking if validation is called during __init__:")

# Create a test with empty title and see what happens
try:
    template = FlowTemplate("", Definition=definition)
    print(f"   Empty title object created: title={template.title!r}")
    print(f"   Checking do_validation flag: {template.do_validation}")
    
    # Check if title validation happens in __init__
    print("\n   Looking at object internals:")
    print(f"   - title attribute: {template.title!r}")
    print(f"   - resource_type: {template.resource_type}")
    
    # Force validation
    print("\n   Forcing validation with to_dict():")
    try:
        result = template.to_dict(validation=True)
        print(f"   ✗ to_dict(validation=True) succeeded (should have failed)")
    except ValueError as e:
        print(f"   ✓ to_dict(validation=True) raised: {e}")
        
except Exception as e:
    print(f"   Failed to create object: {e}")

print("\n" + "=" * 60)
print("Investigation complete!")