#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/mdxpy_env/lib/python3.13/site-packages')

from mdxpy import normalize

# Test idempotence of normalize function
input_str = ']'
normalized_once = normalize(input_str)
normalized_twice = normalize(normalized_once)

print(f"Original: '{input_str}'")
print(f"Normalized once: '{normalized_once}'")
print(f"Normalized twice: '{normalized_twice}'")
print(f"Idempotent? {normalized_once == normalized_twice}")

# The issue: normalize replaces ] with ]], but when applied again,
# it replaces ]] with ]]]], violating idempotence
assert normalized_once == normalized_twice, f"normalize() is not idempotent: '{normalized_once}' != '{normalized_twice}'"