#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer

# Create tokenizer WITHOUT pre-tokenizer
print("=== Testing WITHOUT Whitespace pre-tokenizer ===")
tokenizer1 = Tokenizer(BPE())
trainer1 = BpeTrainer(special_tokens=["[UNK]"])

# Train with minimal corpus including !
corpus = ["a", "b", "c", "!", "!!", "a!", "!a"] * 10
tokenizer1.train_from_iterator(corpus, trainer1)

text = "?!"
print(f"\nText: '{text}'")
enc1 = tokenizer1.encode(text)
print(f"Tokens: {enc1.tokens}")
print(f"Offsets: {enc1.offsets}")
for i, (token, (start, end)) in enumerate(zip(enc1.tokens, enc1.offsets)):
    substring = text[start:end]
    print(f"  Token '{token}' at offset ({start},{end}) -> substring '{substring}' | Match: {substring == token}")

# Now WITH Whitespace pre-tokenizer
print("\n=== Testing WITH Whitespace pre-tokenizer ===")
from tokenizers.pre_tokenizers import Whitespace

tokenizer2 = Tokenizer(BPE())
tokenizer2.pre_tokenizer = Whitespace()
trainer2 = BpeTrainer(special_tokens=["[UNK]"])
tokenizer2.train_from_iterator(corpus, trainer2)

enc2 = tokenizer2.encode(text)
print(f"Tokens: {enc2.tokens}")
print(f"Offsets: {enc2.offsets}")
for i, (token, (start, end)) in enumerate(zip(enc2.tokens, enc2.offsets)):
    substring = text[start:end]
    print(f"  Token '{token}' at offset ({start},{end}) -> substring '{substring}' | Match: {substring == token}")

# Test with ByteLevel pre-tokenizer
print("\n=== Testing with ByteLevel pre-tokenizer ===")
from tokenizers.pre_tokenizers import ByteLevel

tokenizer3 = Tokenizer(BPE())
tokenizer3.pre_tokenizer = ByteLevel()
trainer3 = BpeTrainer(special_tokens=["[UNK]"])
tokenizer3.train_from_iterator(corpus, trainer3)

enc3 = tokenizer3.encode(text)
print(f"Tokens: {enc3.tokens}")
print(f"Offsets: {enc3.offsets}")
for i, (token, (start, end)) in enumerate(zip(enc3.tokens, enc3.offsets)):
    substring = text[start:end]
    print(f"  Token '{token}' at offset ({start},{end}) -> substring '{substring}' | Match: {substring == token}")