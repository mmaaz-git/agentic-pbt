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
text = "?!"
print(f"Original text: '{text}'")
print(f"Text characters: {[c for c in text]}")

encoding = tokenizer.encode(text)
print(f"\nTokens: {encoding.tokens}")
print(f"IDs: {encoding.ids}")
print(f"Offsets: {encoding.offsets}")

# Check each token and its offset
print("\n=== Checking offsets ===")
for i, (token, (start, end)) in enumerate(zip(encoding.tokens, encoding.offsets)):
    substring = text[start:end]
    print(f"Token {i}: '{token}'")
    print(f"  Offset: ({start}, {end})")
    print(f"  Substring from text: '{substring}'")
    print(f"  Match: {substring == token}")

# Try other combinations
print("\n=== Testing other combinations ===")
test_cases = ["!?", "??", "!!", "! ?", "? !", "a?", "?a", "a!", "!a"]
for test_text in test_cases:
    enc = tokenizer.encode(test_text)
    if enc.tokens:
        print(f"\nText: '{test_text}'")
        print(f"  Tokens: {enc.tokens}")
        print(f"  Offsets: {enc.offsets}")
        for i, (tok, (s, e)) in enumerate(zip(enc.tokens, enc.offsets)):
            substr = test_text[s:e]
            match = substr == tok
            if not match:
                print(f"  MISMATCH: Token '{tok}' != Substring '{substr}' at offset ({s},{e})")