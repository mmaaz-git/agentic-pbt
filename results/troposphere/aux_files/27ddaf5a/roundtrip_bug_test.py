#!/usr/bin/env python3
"""Test round-trip properties for potential bugs."""

import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.omics as omics

print("Testing round-trip properties...")
print("="*50)

def test_roundtrip(obj_class, title, properties):
    """Test if an object can round-trip through to_dict and _from_dict."""
    print(f"\nTesting {obj_class.__name__} round-trip:")
    
    # Create original object
    original = obj_class(title)
    for key, value in properties.items():
        setattr(original, key, value)
    
    # Convert to dict
    dict1 = original.to_dict()
    print(f"Original dict: {json.dumps(dict1, indent=2)}")
    
    # Extract properties for reconstruction
    props = dict1.get("Properties", {})
    
    # Create new object from dict
    try:
        reconstructed = obj_class._from_dict(title, **props)
        dict2 = reconstructed.to_dict()
        print(f"Reconstructed dict: {json.dumps(dict2, indent=2)}")
        
        # Compare
        if dict1 == dict2:
            print("✓ Round-trip successful")
            return True
        else:
            print("✗ Round-trip failed - dicts don't match")
            print(f"Difference: {set(str(dict1).split()) - set(str(dict2).split())}")
            return False
    except Exception as e:
        print(f"✗ Round-trip failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Test 1: RunGroup with all properties
print("\n1. RunGroup with all properties:")
test_roundtrip(
    omics.RunGroup,
    "TestRunGroup",
    {
        "Name": "MyRunGroup",
        "MaxCpus": 100.5,
        "MaxDuration": 3600.0,
        "MaxGpus": 8.0,
        "MaxRuns": 50.0,
        "Tags": {"Environment": "Test", "Project": "Demo"}
    }
)

# Test 2: AnnotationStore with nested objects
print("\n2. AnnotationStore with nested objects:")

# First create the nested objects
ref_item = omics.ReferenceItem()
ref_item.ReferenceArn = "arn:aws:omics:us-east-1:123456789012:referenceStore/ref123/reference/ref456"

sse_config = omics.SseConfig()
sse_config.Type = "KMS"
sse_config.KeyArn = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"

tsv_options = omics.TsvStoreOptions()
tsv_options.AnnotationType = "GENERIC"
tsv_options.FormatToHeader = {"CHR": "chromosome", "POS": "position"}
tsv_options.Schema = {"fields": [{"name": "chromosome", "type": "string"}]}

store_options = omics.StoreOptions()
store_options.TsvStoreOptions = tsv_options

# Create the AnnotationStore
store = omics.AnnotationStore("TestAnnotationStore")
store.Name = "MyAnnotationStore"
store.StoreFormat = "TSV"
store.Reference = ref_item
store.SseConfig = sse_config
store.StoreOptions = store_options
store.Description = "Test annotation store"
store.Tags = {"Type": "Test"}

# Test round-trip
dict1 = store.to_dict()
print(f"AnnotationStore dict: {json.dumps(dict1, indent=2)}")

props = dict1.get("Properties", {})
try:
    reconstructed = omics.AnnotationStore._from_dict("TestAnnotationStore", **props)
    dict2 = reconstructed.to_dict()
    
    if dict1 == dict2:
        print("✓ AnnotationStore round-trip successful")
    else:
        print("✗ AnnotationStore round-trip failed")
        print("Checking differences...")
        
        # Deep comparison
        def compare_dicts(d1, d2, path=""):
            for key in set(list(d1.keys()) + list(d2.keys())):
                current_path = f"{path}.{key}" if path else key
                if key not in d1:
                    print(f"  Missing in original: {current_path}")
                elif key not in d2:
                    print(f"  Missing in reconstructed: {current_path}")
                elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
                    compare_dicts(d1[key], d2[key], current_path)
                elif d1[key] != d2[key]:
                    print(f"  Difference at {current_path}: {d1[key]!r} != {d2[key]!r}")
        
        compare_dicts(dict1, dict2)
except Exception as e:
    print(f"✗ AnnotationStore reconstruction failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Edge case with None values
print("\n3. Testing None values in properties:")
rg = omics.RunGroup("TestRunGroup")
rg.Name = None  # Set a property to None
rg.MaxCpus = 100.0

dict1 = rg.to_dict()
print(f"Dict with None: {dict1}")

# Test 4: Empty string values
print("\n4. Testing empty string values:")
rg2 = omics.RunGroup("TestRunGroup2")
rg2.Name = ""  # Empty string
rg2.MaxCpus = 50.0

dict2 = rg2.to_dict()
print(f"Dict with empty string: {dict2}")

# Test 5: Properties with special characters
print("\n5. Testing special characters in properties:")
rg3 = omics.RunGroup("TestRunGroup3")
rg3.Name = "Test-Run_Group.v2"
rg3.Tags = {
    "Key with spaces": "Value with spaces",
    "Key/with/slashes": "Value/with/slashes",
    "Key:with:colons": "Value:with:colons",
    "Unicode✓": "Emoji😀"
}

dict3 = rg3.to_dict()
print(f"Dict with special chars: {json.dumps(dict3, indent=2, ensure_ascii=False)}")

# Test 6: Very large numbers
print("\n6. Testing very large numbers:")
rg4 = omics.RunGroup("TestRunGroup4")
rg4.MaxCpus = 1e308  # Near max float
rg4.MaxRuns = 1e-308  # Near min positive float

dict4 = rg4.to_dict()
print(f"Dict with extreme numbers: {dict4}")

# Test 7: Boolean fields in WorkflowParameter
print("\n7. Testing WorkflowParameter with boolean field:")
param = omics.WorkflowParameter()
param.Description = "Test parameter"
param.Optional = True

param_dict = param.to_dict()
print(f"WorkflowParameter dict: {param_dict}")

# Try with string boolean
param2 = omics.WorkflowParameter()
param2.Optional = "true"  # String instead of boolean
try:
    param2_dict = param2.to_dict()
    print(f"WorkflowParameter with string 'true': {param2_dict}")
except Exception as e:
    print(f"Error with string 'true': {e}")