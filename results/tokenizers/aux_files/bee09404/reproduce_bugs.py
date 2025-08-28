#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.models

print("=== Bug 1: WordLevel allows duplicate IDs breaking round-trip ===")
# Multiple tokens mapping to same ID breaks round-trip property
vocab = {'token_a': 0, 'token_b': 0, '[UNK]': 1}
model = tokenizers.models.WordLevel(vocab, unk_token="[UNK]")

print(f"vocab: {vocab}")
print(f"token_to_id('token_a'): {model.token_to_id('token_a')}")  # Returns 0
print(f"token_to_id('token_b'): {model.token_to_id('token_b')}")  # Returns 0
print(f"id_to_token(0): {model.id_to_token(0)}")  # Returns 'token_b', not 'token_a'!

# This violates the round-trip property
token = 'token_a'
recovered = model.id_to_token(model.token_to_id(token))
print(f"Round-trip for 'token_a': '{token}' -> {model.token_to_id(token)} -> '{recovered}'")
print(f"Round-trip broken: '{token}' != '{recovered}'")

print("\n=== Bug 2: Unknown tokens return None instead of UNK ID ===")
vocab2 = {'known': 0, '[UNK]': 1}
model2 = tokenizers.models.WordLevel(vocab2, unk_token="[UNK]")

unknown_token = "unknown_token"
result = model2.token_to_id(unknown_token)
print(f"vocab: {vocab2}")
print(f"token_to_id('{unknown_token}'): {result}")
print(f"Expected: 1 (the ID of '[UNK]'), Got: {result}")

print("\n=== Bug 3: WordPiece has the same issue ===")
wp_vocab = {'hello': 0, 'world': 0, '[UNK]': 1}
wp_model = tokenizers.models.WordPiece(wp_vocab, unk_token="[UNK]", max_input_chars_per_word=100)
print(f"WordPiece vocab: {wp_vocab}")
print(f"token_to_id('hello'): {wp_model.token_to_id('hello')}")
print(f"token_to_id('world'): {wp_model.token_to_id('world')}")  
print(f"id_to_token(0): {wp_model.id_to_token(0)}")  # Returns 'world', not 'hello'!