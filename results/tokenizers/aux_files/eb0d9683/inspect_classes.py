#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import inspect
from tokenizers import tokenizers

# Inspect Tokenizer class
print("=== Tokenizer class ===")
Tokenizer = tokenizers.Tokenizer
print(f"Signature: {inspect.signature(Tokenizer) if hasattr(Tokenizer, '__init__') else 'No signature'}")
print(f"Docstring: {Tokenizer.__doc__}")
print("\nPublic methods:")
for name in dir(Tokenizer):
    if not name.startswith('_') and callable(getattr(Tokenizer, name, None)):
        method = getattr(Tokenizer, name)
        print(f"  {name}")

print("\n=== Encoding class ===")
Encoding = tokenizers.Encoding
print(f"Docstring: {Encoding.__doc__}")
print("\nPublic methods and properties:")
for name in dir(Encoding):
    if not name.startswith('_'):
        print(f"  {name}")

print("\n=== AddedToken class ===")
AddedToken = tokenizers.AddedToken
print(f"Signature: {inspect.signature(AddedToken) if hasattr(AddedToken, '__init__') else 'No signature'}")
print(f"Docstring: {AddedToken.__doc__}")

print("\n=== NormalizedString class ===")
NormalizedString = tokenizers.NormalizedString
print(f"Docstring: {NormalizedString.__doc__}")
print("\nPublic methods:")
for name in dir(NormalizedString):
    if not name.startswith('_') and callable(getattr(NormalizedString, name, None)):
        print(f"  {name}")