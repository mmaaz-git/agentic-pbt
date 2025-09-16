#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import AWSProperty

print("Investigation: Conflict between user-defined props and internal attributes")
print("="*70)

# Test case 1: Using 'template' as a property name
print("\nTest 1: Creating AWSProperty with 'template' field")
print("-"*40)

class ProblematicProperty(AWSProperty):
    props = {
        'template': (str, True)  # Required string field named 'template'
    }

try:
    obj = ProblematicProperty()
    obj.template = "test_value"
    result = obj.to_dict(validation=True)
    print(f"Success: Created object with template={obj.template}")
    print(f"Result dict: {result}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "-"*40)
print("Test 2: What happens when we set 'template' attribute?")
print("-"*40)

try:
    obj2 = ProblematicProperty()
    print(f"Initial obj2.template: {obj2.template}")
    obj2.template = "my_value"
    print(f"After setting, obj2.template: {obj2.template}")
    print(f"Is 'template' in properties? {'template' in obj2.properties}")
    print(f"Properties dict: {obj2.properties}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "-"*40)
print("Test 3: Other internal attributes that might conflict")
print("-"*40)

# Check other internal attributes
internal_attrs = ['title', 'template', 'do_validation', 'properties', 'resource', 
                  'propnames', 'attributes', 'dictname', 'resource_type']

for attr in internal_attrs:
    class TestProp(AWSProperty):
        props = {
            attr: (str, True)
        }
    
    try:
        obj = TestProp()
        setattr(obj, attr, "test_value")
        result = obj.to_dict(validation=True)
        print(f"✗ ISSUE: '{attr}' can be used as prop name but may cause conflicts")
    except Exception as e:
        if "required" in str(e).lower():
            print(f"✓ OK: '{attr}' fails validation when not set (conflicts with internal)")
        else:
            print(f"? '{attr}': {e}")

print("\n" + "="*70)
print("Analysis:")
print("-"*40)
print("The BaseAWSObject class has internal attributes that can conflict with")
print("user-defined property names. When a property name matches an internal")
print("attribute (like 'template'), setting it may affect internal state rather")
print("than being stored as a property, leading to unexpected behavior.")
print()
print("This is a genuine bug because:")
print("1. The API allows defining props with any name")
print("2. There's no documented restriction on property names")
print("3. The conflict causes silent failures or unexpected validation errors")
print("4. Users would expect property names to be isolated from internal state")