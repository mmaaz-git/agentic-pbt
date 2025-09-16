#!/usr/bin/env python3
"""Focused test to find actual bugs in troposphere.omics."""

import sys
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.omics as omics
from troposphere.validators import boolean, double

print("Searching for bugs in troposphere.omics...")
print("="*50)

# BUG HYPOTHESIS 1: Boolean validator might not handle all edge cases correctly
print("\n1. Testing boolean validator edge cases:")

# According to the code, it should handle these values
truthy_values = [True, 1, "1", "true", "True"]
falsy_values = [False, 0, "0", "false", "False"]

# But what about these edge cases?
edge_cases = [
    # Value, Expected behavior
    ("TRUE", "Should raise ValueError"),
    ("FALSE", "Should raise ValueError"),
    ("yes", "Should raise ValueError"),
    ("no", "Should raise ValueError"),
    ("on", "Should raise ValueError"),
    ("off", "Should raise ValueError"),
    (1.0, "Should return True (1.0 == 1)"),
    (0.0, "Should return False (0.0 == 0)"),
    ("1.0", "Should raise ValueError"),
    ("0.0", "Should raise ValueError"),
    (" true", "Should raise ValueError (leading space)"),
    ("true ", "Should raise ValueError (trailing space)"),
    (" 1", "Should raise ValueError (leading space)"),
    ("1 ", "Should raise ValueError (trailing space)"),
]

bugs_found = []

for value, expected in edge_cases:
    try:
        result = boolean(value)
        actual = f"Returns {result}"
        if "raise" in expected.lower():
            bugs_found.append(f"boolean({value!r}) should raise ValueError but returns {result}")
            print(f"✗ BUG: boolean({value!r}) = {result} ({expected})")
        else:
            print(f"✓ boolean({value!r}) = {result}")
    except ValueError:
        actual = "Raises ValueError"
        if "raise" not in expected.lower():
            bugs_found.append(f"boolean({value!r}) raises ValueError but {expected}")
            print(f"✗ BUG: boolean({value!r}) raises ValueError ({expected})")
        else:
            print(f"✓ boolean({value!r}) raises ValueError (expected)")
    except Exception as e:
        print(f"? boolean({value!r}) raises {type(e).__name__}: {e}")

# BUG HYPOTHESIS 2: _from_dict might not handle nested objects correctly
print("\n2. Testing _from_dict with nested objects:")

# Create a complex nested structure
store = omics.AnnotationStore("TestStore")
store.Name = "MyStore"
store.StoreFormat = "TSV"

# Add nested SSEConfig
sse = omics.SseConfig()
sse.Type = "KMS"
sse.KeyArn = "arn:test"
store.SseConfig = sse

# Add nested StoreOptions with TsvStoreOptions
tsv_opts = omics.TsvStoreOptions()
tsv_opts.AnnotationType = "GENERIC"
tsv_opts.Schema = {"test": "schema"}
store_opts = omics.StoreOptions()
store_opts.TsvStoreOptions = tsv_opts
store.StoreOptions = store_opts

# Convert to dict
original_dict = store.to_dict()
print(f"Original structure: {json.dumps(original_dict, indent=2)}")

# Try to reconstruct
props = original_dict.get("Properties", {})
try:
    reconstructed = omics.AnnotationStore._from_dict("TestStore", **props)
    reconstructed_dict = reconstructed.to_dict()
    
    # Deep comparison
    def deep_compare(d1, d2, path=""):
        diffs = []
        for key in set(list(d1.keys()) + list(d2.keys())):
            current_path = f"{path}.{key}" if path else key
            if key not in d1:
                diffs.append(f"Missing in original: {current_path}")
            elif key not in d2:
                diffs.append(f"Missing in reconstructed: {current_path}")
            elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
                diffs.extend(deep_compare(d1[key], d2[key], current_path))
            elif d1[key] != d2[key]:
                diffs.append(f"Mismatch at {current_path}: {d1[key]!r} != {d2[key]!r}")
        return diffs
    
    diffs = deep_compare(original_dict, reconstructed_dict)
    if diffs:
        print("✗ BUG: Round-trip failed!")
        for diff in diffs:
            print(f"  {diff}")
            bugs_found.append(f"Round-trip: {diff}")
    else:
        print("✓ Round-trip successful")
except Exception as e:
    print(f"✗ BUG: Reconstruction failed: {e}")
    bugs_found.append(f"_from_dict failed: {e}")

# BUG HYPOTHESIS 3: Title validation might be too strict or have edge cases
print("\n3. Testing title validation:")

test_titles = [
    ("ValidTitle123", True),
    ("", False),  # Empty
    ("Title-With-Dashes", False),  # Contains dashes
    ("Title_With_Underscores", False),  # Contains underscores
    ("Title.With.Dots", False),  # Contains dots
    ("Title With Spaces", False),  # Contains spaces
    ("123StartingWithNumber", True),  # Starts with number - should this be valid?
    ("ALLCAPS", True),
    ("alllowercase", True),
    ("CamelCase", True),
    ("ñ", False),  # Non-ASCII
    ("Title!", False),  # Special char
    ("A", True),  # Single char
    ("1", True),  # Single digit
    ("_", False),  # Just underscore
    ("-", False),  # Just dash
]

for title, should_be_valid in test_titles:
    try:
        rg = omics.RunGroup(title)
        if not should_be_valid:
            print(f"✗ BUG: Title {title!r} accepted but should be invalid")
            bugs_found.append(f"Title validation: {title!r} wrongly accepted")
        else:
            print(f"✓ Title {title!r} accepted")
    except ValueError as e:
        if should_be_valid:
            print(f"✗ BUG: Title {title!r} rejected but should be valid")
            bugs_found.append(f"Title validation: {title!r} wrongly rejected")
        else:
            print(f"✓ Title {title!r} rejected (expected)")
    except Exception as e:
        print(f"? Title {title!r} caused {type(e).__name__}: {e}")

# BUG HYPOTHESIS 4: Double validator with edge cases
print("\n4. Testing double validator with special values:")

special_doubles = [
    (float('inf'), "Should accept infinity"),
    (float('-inf'), "Should accept negative infinity"),
    (float('nan'), "Should accept NaN"),
    ("infinity", "String 'infinity' - might work?"),
    ("INFINITY", "String 'INFINITY' - might work?"),
    ("-infinity", "String '-infinity' - might work?"),
    ("Infinity", "String 'Infinity' - might work?"),
]

for value, description in special_doubles:
    try:
        result = double(value)
        print(f"✓ double({value!r}) = {result}")
        # Check if the value is preserved
        if str(value) != str(result):
            print(f"  Note: Value changed from {value!r} to {result!r}")
    except ValueError:
        print(f"✗ double({value!r}) raised ValueError")
        if "should accept" in description.lower():
            bugs_found.append(f"double({value!r}) rejected but {description}")
    except Exception as e:
        print(f"? double({value!r}) raised {type(e).__name__}: {e}")

# BUG HYPOTHESIS 5: Property type checking with AWS helper functions
print("\n5. Testing property setting with potential type confusion:")

# MaxCpus expects a double (float)
rg = omics.RunGroup("TestGroup")

# These should work
try:
    rg.MaxCpus = 100
    print(f"✓ MaxCpus = 100 (int) accepted")
except:
    print(f"✗ BUG: MaxCpus = 100 (int) rejected")
    bugs_found.append("MaxCpus rejects valid integer")

try:
    rg.MaxCpus = 100.5
    print(f"✓ MaxCpus = 100.5 (float) accepted")
except:
    print(f"✗ BUG: MaxCpus = 100.5 (float) rejected")
    bugs_found.append("MaxCpus rejects valid float")

try:
    rg.MaxCpus = "100"
    print(f"✓ MaxCpus = '100' (string) accepted")
except:
    print(f"✗ BUG: MaxCpus = '100' (string) rejected")
    bugs_found.append("MaxCpus rejects valid string number")

# This should fail
try:
    rg.MaxCpus = "not_a_number"
    print(f"✗ BUG: MaxCpus = 'not_a_number' accepted")
    bugs_found.append("MaxCpus accepts invalid string")
except:
    print(f"✓ MaxCpus = 'not_a_number' rejected")

# BUG HYPOTHESIS 6: Empty dict/list in properties
print("\n6. Testing empty collections in properties:")

rg2 = omics.RunGroup("TestGroup2")
rg2.Tags = {}  # Empty dict

try:
    dict_result = rg2.to_dict()
    props = dict_result.get("Properties", {})
    if "Tags" in props:
        if props["Tags"] == {}:
            print("✓ Empty Tags dict preserved")
        else:
            print(f"✗ BUG: Empty Tags dict changed to {props['Tags']!r}")
            bugs_found.append(f"Empty dict handling: {} became {props['Tags']!r}")
    else:
        print("? Empty Tags dict removed from properties")
except Exception as e:
    print(f"✗ Error with empty dict: {e}")

# SUMMARY
print("\n" + "="*50)
print("BUG SEARCH SUMMARY:")
if bugs_found:
    print(f"Found {len(bugs_found)} potential bug(s):")
    for i, bug in enumerate(bugs_found, 1):
        print(f"{i}. {bug}")
else:
    print("No bugs found in the tested scenarios.")

# Let's try to create a minimal reproduction for any bugs found
if bugs_found:
    print("\n" + "="*50)
    print("MINIMAL REPRODUCTIONS:")
    
    # Check for boolean validator bugs
    if any("boolean" in bug for bug in bugs_found):
        print("\n# Boolean validator bug:")
        print("from troposphere.validators import boolean")
        print("# These should raise ValueError but don't:")
        for value in [1.0, 0.0]:
            try:
                result = boolean(value)
                print(f"boolean({value!r})  # Returns {result}, should raise ValueError")
            except:
                pass