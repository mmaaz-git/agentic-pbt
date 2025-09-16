#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

from tokenizers import tokenizers
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

# Test basic Tokenizer creation and usage
print("=== Testing Tokenizer creation ===")
tokenizer = tokenizers.Tokenizer(BPE())
print(f"Created tokenizer: {type(tokenizer)}")

# Test training
print("\n=== Testing training ===")
trainer = BpeTrainer(special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"])
tokenizer.pre_tokenizer = Whitespace()

# Train on a small corpus
corpus = ["Hello world", "This is a test", "Tokenizer testing"]
tokenizer.train_from_iterator(corpus, trainer)
print(f"Vocab size after training: {tokenizer.get_vocab_size()}")

# Test encoding
print("\n=== Testing encoding ===")
encoding = tokenizer.encode("Hello world")
print(f"Encoding type: {type(encoding)}")
print(f"Tokens: {encoding.tokens}")
print(f"IDs: {encoding.ids}")

# Test decoding
print("\n=== Testing decoding ===")
decoded = tokenizer.decode(encoding.ids)
print(f"Decoded: {decoded}")

# Test AddedToken
print("\n=== Testing AddedToken ===")
special_token = tokenizers.AddedToken("[SPECIAL]", single_word=True, special=True)
print(f"Created AddedToken: {special_token}")

# Test NormalizedString
print("\n=== Testing NormalizedString ===")
norm_str = tokenizers.NormalizedString("Hello WORLD!")
print(f"Original: {norm_str}")
norm_str.lowercase()
print(f"After lowercase: {norm_str}")