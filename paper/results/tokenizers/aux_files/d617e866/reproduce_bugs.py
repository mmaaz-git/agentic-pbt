#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.normalizers as norm

print("=== Bug 1: Prepend fails on empty string ===")
prepend = norm.Prepend("prefix")
result = prepend.normalize_str("")
print(f"prepend.normalize_str('') = '{result}'")
print(f"Expected: 'prefix', Got: '{result}'")
print(f"Bug confirmed: {result != 'prefix'}")

print("\n=== Bug 2: Strip doesn't handle all whitespace ===")
strip = norm.Strip()
text = "\x1f"  # Unit separator character
result = strip.normalize_str(text)
print(f"strip.normalize_str('\\x1f') = '{result}'")
print(f"Python's isspace: {text.isspace()}")
print(f"After strip, result is: '{result}' (length: {len(result)})")
print(f"Bug confirmed: {len(result) > 0 and result.isspace()}")

print("\n=== Bug 3: BertNormalizer not idempotent with Chinese ===")
bert = norm.BertNormalizer()
text = "㐀"  # A Chinese character
once = bert.normalize_str(text)
twice = bert.normalize_str(once)
print(f"Original: '{text}'")
print(f"After 1st normalize: '{once}'")
print(f"After 2nd normalize: '{twice}'")
print(f"Bug confirmed: {once != twice}")

print("\n=== Additional test: Prepend behavior ===")
prepend = norm.Prepend(">>>")
text = "hello"
once = prepend.normalize_str(text)
twice = prepend.normalize_str(once)
print(f"Original: '{text}'")
print(f"After 1st prepend: '{once}'")
print(f"After 2nd prepend: '{twice}'")
print(f"Prepend is correctly not idempotent: {once != twice}")

# Empty string prepend
empty_once = prepend.normalize_str("")
empty_twice = prepend.normalize_str(empty_once)
print(f"Empty string after 1st prepend: '{empty_once}'")
print(f"Empty string after 2nd prepend: '{empty_twice}'")
print(f"Bug: Both return empty string instead of prefix!")