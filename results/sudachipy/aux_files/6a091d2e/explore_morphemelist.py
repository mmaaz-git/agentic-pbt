#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import inspect
import sudachipy
from sudachipy import Dictionary, MorphemeList

# Create dictionary and tokenizer
dictionary = Dictionary()
tokenizer = dictionary.create()

# Check the MorphemeList class
print("MorphemeList attributes and methods:")
for name, obj in inspect.getmembers(MorphemeList):
    if not name.startswith('_'):
        print(f"  {name}: {type(obj).__name__}")

# Test basic functionality
text = "すもももももももものうち"
morphemes = tokenizer.tokenize(text)
print(f"\nTokenized '{text}':")
print(f"Type: {type(morphemes)}")
print(f"Length: {len(morphemes)}")
print(f"Size: {morphemes.size()}")

# Check individual morphemes
for i, morpheme in enumerate(morphemes):
    print(f"  [{i}] {morpheme.surface()} ({morpheme.reading_form()})")
    
# Test empty morpheme list
empty_morphemes = tokenizer.tokenize("")
print(f"\nEmpty tokenization:")
print(f"Length: {len(empty_morphemes)}")
print(f"Size: {empty_morphemes.size()}")

# Test iteration
print("\nIteration test:")
for m in morphemes:
    print(f"  - {m.surface()}")

# Test indexing
print("\nIndexing test:")
if len(morphemes) > 0:
    print(f"First morpheme: {morphemes[0].surface()}")
    print(f"Last morpheme: {morphemes[-1].surface()}")