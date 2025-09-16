"""Deep investigation of the validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.iotthingsgraph import DefinitionDocument, FlowTemplate
from troposphere import BaseAWSObject
import re

print("Deep investigation of title validation bug...")
print("=" * 60)

# Let's trace the validation flow
print("\n1. Checking BaseAWSObject.__init__ validation flow:")

# Look at line 183-184 from __init__.py:
# if self.title:
#     self.validate_title()

print("   Code from __init__.py lines 183-184:")
print("   if self.title:")
print("       self.validate_title()")
print("\n   This means validation only happens if title is truthy!")

# Test this
definition = DefinitionDocument(Language="GRAPHQL", Text="{}")

test_titles = ["", None, 0, False, "Valid"]
for title in test_titles:
    print(f"\n   Testing title={title!r}:")
    print(f"     bool(title) = {bool(title)}")
    
    try:
        template = FlowTemplate(title, Definition=definition)
        print(f"     ✓ Object created successfully")
        
        # Check if validate_title would fail
        try:
            template.validate_title()
            print(f"     validate_title() passed")
        except ValueError as e:
            print(f"     validate_title() would raise: {e}")
            
    except ValueError as e:
        print(f"     ✗ Object creation failed: {e}")

print("\n2. Checking to_dict() validation flow:")

# Create object with empty title
template = FlowTemplate("", Definition=definition)

print("   Looking at to_dict(validation=True) flow:")
print("   - Calls self._validate_props() to check required properties")
print("   - Calls self.validate() which is empty by default")  
print("   - But does NOT call self.validate_title()!")

# Verify this
result = template.to_dict(validation=True)
print(f"\n   Result: to_dict() succeeded even with empty title")
print(f"   Type in result: {result.get('Type')}")

print("\n3. Testing with None title:")
template_none = FlowTemplate(None, Definition=definition)
result_none = template_none.to_dict(validation=True)
print(f"   FlowTemplate with None title: to_dict() succeeded")

print("\n4. Testing title validation in real AWS CloudFormation:")
print("   In real CloudFormation, resource logical IDs (titles) must:")
print("   - Be alphanumeric (A-Za-z0-9)")
print("   - Be unique within the template")
print("   - NOT be empty")
print("\n   But troposphere allows empty/None titles!")

print("\n5. Creating minimal reproduction:")
print("\nMinimal failing case:")
print("```python")
print("from troposphere.iotthingsgraph import DefinitionDocument, FlowTemplate")
print("")
print("definition = DefinitionDocument(Language='GRAPHQL', Text='{}')")
print("template = FlowTemplate('', Definition=definition)  # Empty title accepted!")
print("print(template.to_dict())  # Succeeds but shouldn't")
print("```")

print("\n6. Impact analysis:")
print("   - Empty/None titles are accepted during object creation")
print("   - validate_title() is only called if title is truthy")  
print("   - to_dict() doesn't re-validate the title")
print("   - This would create invalid CloudFormation templates")
print("   - AWS would reject these templates, but troposphere doesn't catch it")

print("\n" + "=" * 60)
print("BUG CONFIRMED: Title validation is bypassed for falsy values!")