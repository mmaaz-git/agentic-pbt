#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.models

print("=== Testing exact failing case from Hypothesis ===")
# Exact failing example from test
vocab = {'0': 0, '1': 0, '[UNK]': 2}
model = tokenizers.models.WordLevel(vocab, unk_token="[UNK]")

print(f"vocab: {vocab}")
print(f"Note: Both '0' and '1' map to ID 0")
print()

# Test round-trip for '0'
token = '0'
token_id = model.token_to_id(token)
recovered = model.id_to_token(token_id)
print(f"Round-trip for '0': '{token}' -> {token_id} -> '{recovered}'")
print(f"Expected: '0', Got: '{recovered}'")
print(f"Round-trip {'PASSED' if recovered == token else 'FAILED'}")
print()

# Test round-trip for '1'
token = '1'
token_id = model.token_to_id(token)
recovered = model.id_to_token(token_id)
print(f"Round-trip for '1': '{token}' -> {token_id} -> '{recovered}'")
print(f"Expected: '1', Got: '{recovered}'")
print(f"Round-trip {'PASSED' if recovered == token else 'FAILED'}")
print()

print("=== The Core Issue ===")
print("The WordLevel model accepts vocabularies where multiple tokens")
print("map to the same ID. When this happens, id_to_token() can only")
print("return one of them, breaking the round-trip property for the others.")
print()
print("This violates a fundamental property of tokenization: the bijection")
print("between tokens in the vocabulary and their IDs.")