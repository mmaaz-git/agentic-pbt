#!/usr/bin/env /root/hypothesis-llm/envs/troposphere_env/bin/python3
"""
Bug 2: Tags concatenation doesn't handle duplicate keys properly
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import Tags

print("Testing Tags concatenation with duplicate keys...")

# Create two Tags objects with the same key
tags1 = Tags(Environment="Production")
tags2 = Tags(Environment="Development")

print(f"Tags1: {tags1.to_dict()}")
print(f"Tags2: {tags2.to_dict()}")

# Concatenate them
combined = tags1 + tags2
combined_dict = combined.to_dict()

print(f"Combined: {combined_dict}")
print(f"Combined length: {len(combined_dict)}")

# What we expect: Either merge (keep one) or error
# What happens: Both tags are kept, creating duplicate keys

if len(combined_dict) == 2:
    print("\nBUG CONFIRMED: Tags with duplicate keys are both kept")
    print("This creates invalid CloudFormation: duplicate 'Environment' keys")
    
    # Check if both values are present
    env_values = [tag['Value'] for tag in combined_dict if tag['Key'] == 'Environment']
    print(f"Environment values in combined: {env_values}")
    
    if len(env_values) == 2:
        print("Both 'Production' and 'Development' are present for the same key!")

# Test with more tags
print("\n--- Testing with multiple duplicate keys ---")
tags3 = Tags(A="1", B="2", C="3")
tags4 = Tags(A="4", B="5", D="6")  # A and B are duplicates

combined2 = tags3 + tags4
print(f"Tags3: {tags3.to_dict()}")
print(f"Tags4: {tags4.to_dict()}")
print(f"Combined: {combined2.to_dict()}")
print(f"Expected length: 4 unique keys (A, B, C, D)")
print(f"Actual length: {len(combined2.to_dict())}")