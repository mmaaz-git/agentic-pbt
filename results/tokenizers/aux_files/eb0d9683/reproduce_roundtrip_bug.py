#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

# Create and train tokenizer
tokenizer = Tokenizer(BPE())
tokenizer.pre_tokenizer = Whitespace()
trainer = BpeTrainer(special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"])

corpus = [
    "The quick brown fox jumps over the lazy dog",
    "Hello world this is a test",
    "Testing tokenizer properties with hypothesis",
    "abcdefghijklmnopqrstuvwxyz",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "0123456789",
    "!@#$%^&*()",
] * 5

tokenizer.train_from_iterator(corpus, trainer)

# Test the failing case
text = "?"
print(f"Original text: '{text}'")

encoding = tokenizer.encode(text)
print(f"Tokens: {encoding.tokens}")
print(f"IDs: {encoding.ids}")

decoded = tokenizer.decode(encoding.ids)
print(f"Decoded text: '{decoded}'")
print(f"Length of decoded: {len(decoded)}")

print(f"\nRound-trip successful: {decoded == text}")

# Test with more punctuation
print("\n=== Testing other punctuation ===")
for char in "?!.,;:'\"":
    enc = tokenizer.encode(char)
    dec = tokenizer.decode(enc.ids)
    print(f"'{char}' -> tokens: {enc.tokens}, ids: {enc.ids} -> decoded: '{dec}' | Match: {dec == char}")

# Check vocab
print("\n=== Checking vocabulary ===")
vocab = tokenizer.get_vocab()
print(f"Vocab size: {tokenizer.get_vocab_size()}")
print(f"Is '?' in vocab: {'?' in vocab}")
if '?' in vocab:
    print(f"ID for '?': {vocab['?']}")

# Try with unknown token
print("\n=== Testing unknown handling ===")
print(f"Token to ID for '?': {tokenizer.token_to_id('?')}")
print(f"ID to token for ID used: {tokenizer.id_to_token(encoding.ids[0]) if encoding.ids else 'No IDs'}")