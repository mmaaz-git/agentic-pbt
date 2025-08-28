#!/usr/bin/env python3
"""Minimal reproduction of global state mutation bug in yq.loader.get_loader"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import yq.loader

# Get loader class with expand_merge_keys=True
loader_class_1 = yq.loader.get_loader(expand_merge_keys=True)

# Get loader class with expand_merge_keys=False  
loader_class_2 = yq.loader.get_loader(expand_merge_keys=False)

# Both return the same class object
assert loader_class_1 is loader_class_2, "Should be same class"

# But the second call modified the class for everyone!
# Check if '<' (merge key) is in resolvers
has_merge = any('<' in str(k) for k in loader_class_1.yaml_implicit_resolvers.keys())

print(f"loader_class_1 is loader_class_2: {loader_class_1 is loader_class_2}")
print(f"Class has merge resolver after second call: {has_merge}")
print("\nBUG: Second call with expand_merge_keys=False removed merge")
print("resolver from the shared class, affecting all users!")