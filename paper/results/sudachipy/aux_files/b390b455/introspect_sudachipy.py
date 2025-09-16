#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import inspect
import sudachipy
from sudachipy import Dictionary, Tokenizer, SplitMode, MorphemeList, Morpheme

# Explore main classes and functions
print("=== Sudachipy Module Overview ===")
print(f"Version: {sudachipy.__version__}")
print(f"Module file: {sudachipy.__file__}")

print("\n=== Public Members ===")
members = inspect.getmembers(sudachipy, lambda m: not m.__name__.startswith('_') if hasattr(m, '__name__') else True)
for name, obj in members:
    if not name.startswith('_'):
        print(f"  {name}: {type(obj)}")

print("\n=== Dictionary Class ===")
print(f"Signature: {inspect.signature(Dictionary.__init__)}")
print(f"Docstring: {Dictionary.__init__.__doc__}")

print("\n=== Tokenizer Creation ===")
try:
    # Create dictionary and tokenizer
    dict = Dictionary()
    print("Dictionary created successfully")
    
    # Try to create tokenizer
    tokenizer = dict.create()
    print(f"Tokenizer type: {type(tokenizer)}")
    
    # Check tokenizer methods
    print("\nTokenizer methods:")
    for name in dir(tokenizer):
        if not name.startswith('_'):
            attr = getattr(tokenizer, name)
            if callable(attr):
                try:
                    sig = inspect.signature(attr)
                    print(f"  {name}{sig}")
                except:
                    print(f"  {name}()")
                    
except Exception as e:
    print(f"Error creating dictionary/tokenizer: {e}")

print("\n=== SplitMode ===")
print(f"SplitMode.A: {SplitMode.A}")
print(f"SplitMode.B: {SplitMode.B}")
print(f"SplitMode.C: {SplitMode.C}")

print("\n=== Morpheme Class Methods ===")
morpheme_methods = [m for m in dir(Morpheme) if not m.startswith('_') and callable(getattr(Morpheme, m))]
for method in morpheme_methods:
    print(f"  {method}")

print("\n=== MorphemeList Class Methods ===")
morpheme_list_methods = [m for m in dir(MorphemeList) if not m.startswith('_') and callable(getattr(MorphemeList, m))]
for method in morpheme_list_methods:
    print(f"  {method}")