#!/usr/bin/env python3
import sys
import os
import inspect

# Add the awkward env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak

# Let's explore specific operations that are good candidates for property testing

# 1. Concatenate - should preserve length, elements
print("Exploring concatenate:")
print(ak.concatenate.__doc__[:1000] if ak.concatenate.__doc__ else "No doc")

print("\n\n" + "="*50)
print("Exploring zip/unzip (round-trip candidate):")
print(ak.zip.__doc__[:500] if ak.zip.__doc__ else "No doc")
print("\n")
print(ak.unzip.__doc__[:500] if ak.unzip.__doc__ else "No doc")

print("\n\n" + "="*50)
print("Exploring flatten:")
print(ak.flatten.__doc__[:800] if ak.flatten.__doc__ else "No doc")

print("\n\n" + "="*50)
print("Exploring argsort (should produce valid indices):")
print(ak.argsort.__doc__[:800] if ak.argsort.__doc__ else "No doc")

print("\n\n" + "="*50)
print("Exploring mask/is_none (masking operations):")
print(ak.mask.__doc__[:500] if ak.mask.__doc__ else "No doc")
print("\n")
print(ak.is_none.__doc__[:500] if ak.is_none.__doc__ else "No doc")

# Let's also check if there are conversion functions (to/from other formats)
conversion_funcs = [name for name in dir(ak) if (name.startswith('to_') or name.startswith('from_'))]
print(f"\n\nConversion functions: {conversion_funcs[:10]}")