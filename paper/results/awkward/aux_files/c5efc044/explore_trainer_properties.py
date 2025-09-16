#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.trainers as trainers

print("=== Testing Trainer Properties ===\n")

# Test 1: BpeTrainer parameter validation
print("1. BpeTrainer parameter constraints:")
try:
    # Test negative vocab_size
    t = trainers.BpeTrainer(vocab_size=-1)
    print(f"  - Negative vocab_size accepted: {t.vocab_size}")
except Exception as e:
    print(f"  - Negative vocab_size rejected: {e}")

try:
    # Test negative min_frequency
    t = trainers.BpeTrainer(min_frequency=-5)
    print(f"  - Negative min_frequency accepted: {t.min_frequency}")
except Exception as e:
    print(f"  - Negative min_frequency rejected: {e}")

try:
    # Test initial_alphabet with multi-char strings
    t = trainers.BpeTrainer(initial_alphabet=["abc", "def", "x"])
    print(f"  - Multi-char initial_alphabet: {t.initial_alphabet}")
except Exception as e:
    print(f"  - Multi-char initial_alphabet rejected: {e}")

print("\n2. UnigramTrainer parameter constraints:")
try:
    # Test shrinking_factor out of range
    t = trainers.UnigramTrainer(shrinking_factor=1.5)
    print(f"  - shrinking_factor > 1 accepted: {t}")
except Exception as e:
    print(f"  - shrinking_factor > 1 rejected: {e}")

try:
    t = trainers.UnigramTrainer(shrinking_factor=-0.5)
    print(f"  - shrinking_factor < 0 accepted: {t}")
except Exception as e:
    print(f"  - shrinking_factor < 0 rejected: {e}")

print("\n3. Attribute persistence:")
# Test that set parameters are retrievable
bpe = trainers.BpeTrainer(vocab_size=5000, min_frequency=10, 
                          special_tokens=["<pad>", "<unk>"],
                          initial_alphabet=["a", "b"])
print(f"  BpeTrainer.vocab_size: {bpe.vocab_size} (expected 5000)")
print(f"  BpeTrainer.min_frequency: {bpe.min_frequency} (expected 10)")
print(f"  BpeTrainer.special_tokens: {bpe.special_tokens}")
print(f"  BpeTrainer.initial_alphabet: {bpe.initial_alphabet}")

unigram = trainers.UnigramTrainer(vocab_size=3000, shrinking_factor=0.5)
print(f"  UnigramTrainer.vocab_size: {unigram.vocab_size} (expected 3000)")

print("\n4. Extreme values:")
try:
    t = trainers.BpeTrainer(vocab_size=0)
    print(f"  - vocab_size=0 accepted: {t.vocab_size}")
except Exception as e:
    print(f"  - vocab_size=0 rejected: {e}")

try:
    t = trainers.BpeTrainer(vocab_size=2**31 - 1)  # Max 32-bit int
    print(f"  - vocab_size=2^31-1 accepted: {t.vocab_size}")
except Exception as e:
    print(f"  - vocab_size=2^31-1 rejected: {e}")

try:
    t = trainers.BpeTrainer(vocab_size=2**63)  # Beyond 64-bit int
    print(f"  - vocab_size=2^63 accepted: {t.vocab_size}")
except Exception as e:
    print(f"  - vocab_size=2^63 rejected: {e}")

print("\n5. Type coercion:")
try:
    t = trainers.BpeTrainer(vocab_size=5000.7)  # Float instead of int
    print(f"  - Float vocab_size={t.vocab_size} (type: {type(t.vocab_size)})")
except Exception as e:
    print(f"  - Float vocab_size rejected: {e}")

try:
    t = trainers.BpeTrainer(vocab_size="5000")  # String instead of int
    print(f"  - String vocab_size={t.vocab_size} (type: {type(t.vocab_size)})")
except Exception as e:
    print(f"  - String vocab_size rejected: {e}")