"""Verify the empty title bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.frauddetector as fd
import re

# The regex from troposphere
valid_names = re.compile(r"^[a-zA-Z0-9]+$")

print("Testing empty title bug:")
print("=" * 50)

# Test 1: Empty string as title
print("\n1. Testing empty string as title:")
try:
    entity = fd.EntityType("", Name="test_name")
    print(f"   ✓ Created successfully with empty title!")
    print(f"   entity.title = {repr(entity.title)}")
    result = entity.to_dict()
    print(f"   to_dict() = {result}")
except ValueError as e:
    print(f"   ✗ Failed as expected: {e}")

# Test 2: None as title
print("\n2. Testing None as title:")
try:
    entity = fd.EntityType(None, Name="test_name")
    print(f"   ✓ Created successfully with None title!")
    print(f"   entity.title = {repr(entity.title)}")
    result = entity.to_dict()
    print(f"   to_dict() = {result}")
except (ValueError, TypeError) as e:
    print(f"   ✗ Failed: {e}")

# Test 3: Check what the validation logic should be
print("\n3. Checking validation logic:")
print(f"   Regex matches empty string: {bool(valid_names.match(''))}")
print(f"   Regex matches None: {bool(valid_names.match(None) if None else False)}")

# Test 4: Multiple entities with empty/None titles
print("\n4. Testing multiple entities with empty/None titles:")
try:
    e1 = fd.EntityType("", Name="entity1")
    e2 = fd.EntityType("", Name="entity2")
    e3 = fd.EntityType(None, Name="entity3")
    print(f"   Created 3 entities with empty/None titles")
    print(f"   e1.title={repr(e1.title)}, e2.title={repr(e2.title)}, e3.title={repr(e3.title)}")
except Exception as e:
    print(f"   Failed: {e}")

# Test 5: Check if this affects CloudFormation template generation
print("\n5. Testing CloudFormation template impact:")
from troposphere import Template

template = Template()
try:
    # Add entity with empty title
    entity = fd.EntityType("", Name="TestEntity", Description="Entity with empty title")
    template.add_resource(entity)
    print(f"   Added entity with empty title to template")
    
    # Try to generate JSON
    json_output = template.to_json()
    print(f"   ✓ Template generated successfully!")
    print(f"   Template resources: {list(template.resources.keys())}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 6: What happens with other resources?
print("\n6. Testing other resource types with empty title:")
classes_to_test = [
    (fd.Label, {"Name": "test_label"}),
    (fd.Outcome, {"Name": "test_outcome"}),
    (fd.Variable, {"Name": "test_var", "DataSource": "EVENT", "DataType": "STRING", "DefaultValue": "default"}),
]

for cls, props in classes_to_test:
    try:
        obj = cls("", **props)
        print(f"   ✓ {cls.__name__} created with empty title")
    except Exception as e:
        print(f"   ✗ {cls.__name__} failed: {e}")