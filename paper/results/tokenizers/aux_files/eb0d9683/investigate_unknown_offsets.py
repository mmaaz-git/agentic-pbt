#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

# Create tokenizer with minimal vocab
tokenizer = Tokenizer(BPE())
tokenizer.pre_tokenizer = Whitespace()
trainer = BpeTrainer(special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"])

# Train only on letters and one punctuation
corpus = ["a b c d e"] * 10
tokenizer.train_from_iterator(corpus, trainer)

print("=== Vocabulary ===")
vocab = tokenizer.get_vocab()
print(f"Vocab size: {len(vocab)}")
print(f"Vocab contains: {sorted(vocab.keys())}")

# Test with unknown characters mixed with known
test_cases = [
    "a?b",     # known, unknown, known
    "?ab",     # unknown, known, known
    "ab?",     # known, known, unknown
    "?a?b?",   # alternating unknown/known
    "???a",    # multiple unknown, then known
    "a???",    # known, then multiple unknown
]

print("\n=== Testing offset behavior with unknown characters ===")
for text in test_cases:
    print(f"\nText: '{text}' (chars: {list(text)})")
    encoding = tokenizer.encode(text)
    print(f"  Tokens: {encoding.tokens}")
    print(f"  Offsets: {encoding.offsets}")
    
    # Check each token offset
    for i, (token, (start, end)) in enumerate(zip(encoding.tokens, encoding.offsets)):
        actual_substring = text[start:end]
        expected_position = text.find(token)
        print(f"    Token '{token}': offset ({start},{end}) -> '{actual_substring}'")
        if actual_substring != token:
            print(f"      ERROR: Offset points to '{actual_substring}' not '{token}'!")
            print(f"      Expected token at position {expected_position}")

# Test if adding unknown token handler helps
print("\n=== Testing with UNK token ===")
# Try to see if we can add '?' as a special token
from tokenizers import AddedToken
unk_token = AddedToken("[UNK]", normalized=False, special=True)
tokenizer.add_special_tokens([unk_token])

test = "?a?"
print(f"\nText: '{test}'")
enc = tokenizer.encode(test)
print(f"Tokens: {enc.tokens}")
print(f"Offsets: {enc.offsets}")