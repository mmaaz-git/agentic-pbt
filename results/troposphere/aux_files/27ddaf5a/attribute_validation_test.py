#!/usr/bin/env python3
"""Test attribute validation for potential bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.omics as omics

print("Testing attribute validation...")
print("="*50)

# Test 1: Setting invalid attributes
print("\n1. Testing invalid attribute names:")
rg = omics.RunGroup("TestRunGroup")

invalid_attrs = [
    "InvalidProperty",
    "notAProp",
    "_private",
    "123numeric",
    "with-dash",
    "with.dot",
    "with space",
    "",  # Empty string
    "Constructor",  # Reserved name
    "get",  # Common method name
]

for attr_name in invalid_attrs:
    try:
        setattr(rg, attr_name, "test_value")
        # Check if it was actually set
        try:
            value = getattr(rg, attr_name)
            print(f"✗ {attr_name:20} - Set and retrieved: {value}")
        except AttributeError:
            # It was set but can't be retrieved - inconsistent behavior
            if attr_name in rg.properties:
                print(f"✗ {attr_name:20} - In properties but can't get")
            else:
                print(f"? {attr_name:20} - Set succeeded but not in properties and can't get")
    except AttributeError as e:
        print(f"✓ {attr_name:20} - Rejected with AttributeError")
    except Exception as e:
        print(f"? {attr_name:20} - Unexpected error: {type(e).__name__}")

# Test 2: Type validation
print("\n2. Testing type validation for MaxCpus (expects double):")
rg2 = omics.RunGroup("TestRunGroup2")

test_values = [
    (100, "Integer"),
    (100.5, "Float"),
    ("100", "String number"),
    ("100.5", "String float"),
    ("not_a_number", "Invalid string"),
    (None, "None"),
    ([100], "List"),
    ({"value": 100}, "Dict"),
    (True, "Boolean True"),
    (False, "Boolean False"),
]

for value, description in test_values:
    try:
        rg2.MaxCpus = value
        # Try to convert to dict to trigger validation
        result = rg2.to_dict()
        props = result.get("Properties", {})
        if "MaxCpus" in props:
            print(f"✓ {description:20} - Accepted: {props['MaxCpus']!r}")
        else:
            print(f"? {description:20} - Set but not in dict")
    except (TypeError, ValueError) as e:
        print(f"✗ {description:20} - Rejected: {type(e).__name__}")
    except Exception as e:
        print(f"? {description:20} - Unexpected: {type(e).__name__}: {e}")

# Test 3: Required properties
print("\n3. Testing required properties:")

# VariantStore requires Name and Reference
vs = omics.VariantStore("TestVariantStore")

# Try without setting required properties
try:
    dict1 = vs.to_dict()
    print(f"✗ Created dict without required properties: {dict1}")
except Exception as e:
    print(f"✓ Validation failed without required properties: {e}")

# Set only Name
vs.Name = "MyVariantStore"
try:
    dict2 = vs.to_dict()
    print(f"✗ Created dict with only Name: {dict2}")
except Exception as e:
    print(f"✓ Validation failed without Reference: {e}")

# Set Reference
ref = omics.ReferenceItem()
ref.ReferenceArn = "arn:aws:omics:us-east-1:123456789012:referenceStore/ref123/reference/ref456"
vs.Reference = ref

try:
    dict3 = vs.to_dict()
    print(f"✓ Created dict with all required properties")
except Exception as e:
    print(f"✗ Validation failed even with all required: {e}")

# Test 4: Property name collision with methods
print("\n4. Testing property name collision with methods:")

# These are actual properties that might collide with methods
property_method_collisions = [
    ("Name", "string"),  # Common property
    ("Type", "string"),  # Used in SseConfig
    ("Tags", "dict"),    # Common property
]

for prop_name, prop_type in property_method_collisions:
    # Test on different classes
    if prop_name == "Type":
        obj = omics.SseConfig()
    else:
        obj = omics.RunGroup("TestCollision")
    
    try:
        if prop_type == "string":
            setattr(obj, prop_name, "test_value")
        elif prop_type == "dict":
            setattr(obj, prop_name, {"key": "value"})
        
        value = getattr(obj, prop_name)
        print(f"✓ {prop_name:10} - Set and retrieved: {value!r}")
    except Exception as e:
        print(f"✗ {prop_name:10} - Error: {type(e).__name__}: {e}")

# Test 5: Case sensitivity
print("\n5. Testing case sensitivity of property names:")
rg3 = omics.RunGroup("TestRunGroup3")

case_tests = [
    ("Name", "name", "NAME"),
    ("MaxCpus", "maxcpus", "MAXCPUS", "maxCPUs"),
]

for variants in case_tests:
    original = variants[0]
    print(f"\nTesting variants of '{original}':")
    for variant in variants:
        try:
            setattr(rg3, variant, "test_value")
            value = getattr(rg3, variant)
            print(f"  {variant:10} - Set and retrieved: {value!r}")
        except AttributeError:
            print(f"  {variant:10} - AttributeError (expected for non-exact match)")
        except Exception as e:
            print(f"  {variant:10} - Unexpected: {type(e).__name__}")

# Test 6: Unicode property values
print("\n6. Testing Unicode in property values:")
rg4 = omics.RunGroup("TestRunGroup4")

unicode_tests = [
    "Hello 世界",  # Chinese
    "مرحبا",  # Arabic
    "🚀🔬🧬",  # Emojis
    "Ω≈ç√∫",  # Math symbols
    "\n\t\r",  # Control characters
    "A\x00B",  # Null character
    "\"'<>&",  # Special HTML/XML chars
]

for test_str in unicode_tests:
    try:
        rg4.Name = test_str
        result = rg4.to_dict()
        props = result.get("Properties", {})
        if "Name" in props and props["Name"] == test_str:
            print(f"✓ Preserved: {test_str!r}")
        else:
            print(f"✗ Not preserved: {test_str!r} -> {props.get('Name')!r}")
    except Exception as e:
        print(f"✗ Error with {test_str!r}: {type(e).__name__}")