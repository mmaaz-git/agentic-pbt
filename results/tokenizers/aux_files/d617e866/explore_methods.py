#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.normalizers as norm
import inspect

# Create instances and explore their methods
normalizers_to_test = [
    ("Lowercase", norm.Lowercase()),
    ("NFC", norm.NFC()),
    ("NFD", norm.NFD()),
    ("NFKC", norm.NFKC()),
    ("NFKD", norm.NFKD()),
    ("Strip", norm.Strip()),
    ("StripAccents", norm.StripAccents()),
    ("Prepend", norm.Prepend("▁")),
    ("Replace", norm.Replace("a", "b")),
    ("BertNormalizer", norm.BertNormalizer()),
    ("ByteLevel", norm.ByteLevel()),
    ("Nmt", norm.Nmt()),
]

for name, normalizer in normalizers_to_test:
    print(f"\n=== {name} ===")
    print(f"Type: {type(normalizer)}")
    
    # Get all methods
    methods = [m for m in dir(normalizer) if not m.startswith('_')]
    print(f"Methods: {methods}")
    
    # Try to understand normalize_str method
    if hasattr(normalizer, 'normalize_str'):
        print(f"normalize_str doc: {normalizer.normalize_str.__doc__}")
        try:
            # Test with simple string
            result = normalizer.normalize_str("Hello World")
            print(f"normalize_str('Hello World') = '{result}'")
        except Exception as e:
            print(f"Error calling normalize_str: {e}")

# Test Sequence normalizer
print("\n=== Sequence ===")
seq = norm.Sequence([norm.Lowercase(), norm.Strip()])
print(f"Type: {type(seq)}")
methods = [m for m in dir(seq) if not m.startswith('_')]
print(f"Methods: {methods}")
if hasattr(seq, 'normalize_str'):
    result = seq.normalize_str("  HELLO WORLD  ")
    print(f"Sequence.normalize_str('  HELLO WORLD  ') = '{result}'")