#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

# Try to import and inspect what we can about MorphemeList without creating instances
import sudachipy
from sudachipy import MorphemeList

print("MorphemeList class:", MorphemeList)
print("MorphemeList type:", type(MorphemeList))

# Check if we can see anything about the class
print("\nMorphemeList docstring:")
print(MorphemeList.__doc__)

# Check methods
print("\nPublic methods:")
for attr in dir(MorphemeList):
    if not attr.startswith('_'):
        obj = getattr(MorphemeList, attr)
        print(f"  {attr}: {getattr(obj, '__doc__', 'No docstring')[:50] if hasattr(obj, '__doc__') else 'No docstring'}")

# Check if we can directly instantiate (should fail according to docs)
print("\nTrying to instantiate MorphemeList directly...")
try:
    ml = MorphemeList()
    print("Unexpectedly succeeded!")
except Exception as e:
    print(f"Failed as expected: {e}")