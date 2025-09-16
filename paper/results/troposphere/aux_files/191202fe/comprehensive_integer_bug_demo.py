#!/usr/bin/env python3
"""Comprehensive demonstration of the integer validator bug in troposphere."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import integer
import troposphere.lex as lex

print("=== BUG: troposphere.validators.integer returns original type instead of int ===\n")

# Test 1: Float values
print("1. Float inputs should be converted to int, but aren't:")
float_inputs = [0.0, 1.0, -5.0, 100.0, 3.14]
for val in float_inputs:
    result = integer(val)
    print(f"  integer({val}) = {result} (type: {type(result).__name__})")
    if isinstance(result, float):
        print(f"    ❌ BUG: Returns float instead of int")

print("\n2. This breaks type expectations in AWS CloudFormation resources:")
# Create a CustomVocabularyItem with Weight property (expects integer)
item = lex.CustomVocabularyItem(Phrase="test word")
item.properties['Weight'] = integer(5.0)  

print(f"  CustomVocabularyItem.Weight = {item.properties['Weight']} (type: {type(item.properties['Weight']).__name__})")
print(f"  ❌ Weight property is float, but AWS expects integer type")

print("\n3. JSON serialization will include floats where integers are expected:")
item_dict = item.to_dict()
import json
json_str = json.dumps(item_dict)
print(f"  JSON: {json_str}")
print(f"  ❌ Weight serialized as 5.0 instead of 5")

print("\n4. The bug is in the implementation:")
print("  Current code (line 46-52 of validators/__init__.py):")
print("    def integer(x):")
print("        try:")
print("            int(x)  # Validates conversion")
print("        except (ValueError, TypeError):")
print("            raise ValueError(...)")
print("        else:")
print("            return x  # ❌ BUG: Returns original x instead of int(x)")
print("\n  Should be:")
print("            return int(x)  # ✓ Return the converted integer")

print("\n5. Impact on downstream code:")
print("  - CloudFormation templates may have incorrect types")
print("  - Type checking tools will report wrong types")
print("  - AWS API calls may fail with type validation errors")