#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

from tokenizers import tokenizers, Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

# Create and train a simple tokenizer
tokenizer = Tokenizer(BPE())
tokenizer.pre_tokenizer = Whitespace()
trainer = BpeTrainer(special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"])
corpus = ["The quick brown fox jumps over the lazy dog"] * 10
tokenizer.train_from_iterator(corpus, trainer)

# Test various properties
print("=== Testing Encoding properties ===")
text = "The quick brown fox"
encoding = tokenizer.encode(text)

print(f"Original text: '{text}'")
print(f"Tokens: {encoding.tokens}")
print(f"IDs: {encoding.ids}")
print(f"Offsets: {encoding.offsets}")
print(f"Word IDs: {encoding.word_ids}")

# Test char_to_token mapping
print("\n=== Testing char_to_token ===")
for i in range(len(text)):
    token_idx = encoding.char_to_token(i)
    print(f"Char {i} ('{text[i]}'): token {token_idx}")

# Test token_to_chars mapping
print("\n=== Testing token_to_chars ===")
for i in range(len(encoding.tokens)):
    char_span = encoding.token_to_chars(i)
    if char_span:
        print(f"Token {i} ('{encoding.tokens[i]}'): chars {char_span} -> '{text[char_span[0]:char_span[1]]}'")

# Test round-trip
print("\n=== Testing round-trip ===")
decoded = tokenizer.decode(encoding.ids)
print(f"Decoded: '{decoded}'")
print(f"Matches original: {decoded == text}")

# Test batch operations
print("\n=== Testing batch operations ===")
texts = ["Hello", "World", "Test"]
encodings = tokenizer.encode_batch(texts)
print(f"Batch encoded {len(encodings)} texts")
decoded_batch = tokenizer.decode_batch([e.ids for e in encodings])
print(f"Batch decoded: {decoded_batch}")
print(f"Matches originals: {decoded_batch == texts}")

# Test NormalizedString
print("\n=== Testing NormalizedString ===")
norm = tokenizers.NormalizedString("Hello WORLD!")
original = str(norm)
print(f"Original: '{original}'")

norm.lowercase()
after_lower = str(norm)
print(f"After lowercase: '{after_lower}'")

# Test that alignment is maintained
norm2 = tokenizers.NormalizedString("  Hello  ")
print(f"\nBefore strip: '{norm2}' (len={len(str(norm2))})")
norm2.strip()
print(f"After strip: '{norm2}' (len={len(str(norm2))})")