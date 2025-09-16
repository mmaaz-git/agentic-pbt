"""Direct test runner for property-based tests"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.iotthingsgraph import DefinitionDocument, FlowTemplate
from troposphere.validators import double
import json

print("Testing troposphere.iotthingsgraph properties...")
print("=" * 60)

# Test 1: Double validator with valid values
print("\n1. Testing double validator with valid values:")
test_values = [42, 3.14, -1.5, 0, 1e10, "123", "3.14"]
for val in test_values:
    try:
        result = double(val)
        print(f"  ✓ double({val!r}) = {result!r}")
    except Exception as e:
        print(f"  ✗ double({val!r}) raised: {e}")

# Test 2: Double validator with invalid values
print("\n2. Testing double validator with invalid values:")
invalid_values = ["abc", None, [], {}, "not a number"]
for val in invalid_values:
    try:
        result = double(val)
        print(f"  ✗ double({val!r}) should have raised but returned: {result!r}")
    except ValueError as e:
        print(f"  ✓ double({val!r}) correctly raised ValueError")
    except Exception as e:
        print(f"  ? double({val!r}) raised unexpected: {e}")

# Test 3: Title validation
print("\n3. Testing title validation:")
valid_titles = ["ValidTitle123", "Test", "ABC123"]
invalid_titles = ["Invalid-Title", "Title With Spaces", "Title.With.Dots", "", "Title_With_Underscore"]

definition = DefinitionDocument(Language="GRAPHQL", Text="{}")

for title in valid_titles:
    try:
        obj = FlowTemplate(title, Definition=definition)
        print(f"  ✓ Title '{title}' accepted")
    except Exception as e:
        print(f"  ✗ Title '{title}' rejected: {e}")

for title in invalid_titles:
    try:
        obj = FlowTemplate(title, Definition=definition)
        print(f"  ✗ Title '{title}' should have been rejected")
    except ValueError as e:
        print(f"  ✓ Title '{title}' correctly rejected")
    except Exception as e:
        print(f"  ? Title '{title}' raised unexpected: {e}")

# Test 4: Required field validation
print("\n4. Testing required field validation:")

# Test DefinitionDocument
print("  DefinitionDocument:")
try:
    doc = DefinitionDocument(Text="{}")
    doc.to_dict()
    print("    ✗ Missing Language should have raised")
except ValueError as e:
    if "Language" in str(e):
        print("    ✓ Missing Language correctly raised ValueError")
    else:
        print(f"    ? Unexpected error: {e}")

try:
    doc = DefinitionDocument(Language="GRAPHQL")
    doc.to_dict()
    print("    ✗ Missing Text should have raised")
except ValueError as e:
    if "Text" in str(e):
        print("    ✓ Missing Text correctly raised ValueError")
    else:
        print(f"    ? Unexpected error: {e}")

# Test FlowTemplate
print("  FlowTemplate:")
try:
    template = FlowTemplate("Test")
    template.to_dict()
    print("    ✗ Missing Definition should have raised")
except ValueError as e:
    if "Definition" in str(e):
        print("    ✓ Missing Definition correctly raised ValueError")
    else:
        print(f"    ? Unexpected error: {e}")

# Test 5: Type enforcement
print("\n5. Testing type enforcement:")
invalid_definition_values = [123, "string", [], {}]
for val in invalid_definition_values:
    try:
        template = FlowTemplate("Test", Definition=val)
        print(f"  ✗ Definition={val!r} should have raised TypeError")
    except TypeError:
        print(f"  ✓ Definition={val!r} correctly raised TypeError")
    except Exception as e:
        print(f"  ? Definition={val!r} raised unexpected: {e}")

# Test 6: Round-trip conversion
print("\n6. Testing to_dict/from_dict round-trip:")
definition = DefinitionDocument(Language="GRAPHQL", Text='{"test": "data"}')
original_template = FlowTemplate("TestTemplate", Definition=definition, CompatibleNamespaceVersion=1.5)

dict_repr = original_template.to_dict()
print(f"  Original to_dict: {json.dumps(dict_repr, indent=2)}")

# Create new from dict
props = dict_repr.get("Properties", {})
new_template = FlowTemplate.from_dict("TestTemplate", props)
new_dict = new_template.to_dict()

if dict_repr == new_dict:
    print("  ✓ Round-trip preserved data")
else:
    print(f"  ✗ Round-trip failed")
    print(f"  New to_dict: {json.dumps(new_dict, indent=2)}")

# Test 7: Edge cases
print("\n7. Testing edge cases:")

# Empty strings
try:
    doc = DefinitionDocument(Language="", Text="")
    result = doc.to_dict()
    print(f"  ✓ Empty strings accepted: {result}")
except Exception as e:
    print(f"  ✗ Empty strings raised: {e}")

# Very long strings
long_text = "x" * 10000
try:
    doc = DefinitionDocument(Language="GRAPHQL", Text=long_text)
    result = doc.to_dict()
    print(f"  ✓ Long string (10000 chars) accepted")
except Exception as e:
    print(f"  ✗ Long string raised: {e}")

# Special characters in text
special_text = '{"key": "value with 特殊字符 and émojis 🎉"}'
try:
    doc = DefinitionDocument(Language="GRAPHQL", Text=special_text)
    result = doc.to_dict()
    print(f"  ✓ Special characters accepted")
except Exception as e:
    print(f"  ✗ Special characters raised: {e}")

print("\n" + "=" * 60)
print("Testing complete!")