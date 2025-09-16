#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.trainers as trainers

# Bug 1: BpeTrainer reverses the order of initial_alphabet
print("Bug 1: BpeTrainer initial_alphabet order reversal")
print("-" * 50)

# Minimal failing case from Hypothesis
trainer = trainers.BpeTrainer(initial_alphabet=['0', '1'])
print(f"Input: ['0', '1']")
print(f"Output: {trainer.initial_alphabet}")
print(f"Expected: ['0', '1'] (preserving order)")
print(f"Actual: {trainer.initial_alphabet} (reversed!)")
print()

# Another example
trainer = trainers.BpeTrainer(initial_alphabet=['a', 'b', 'c'])
print(f"Input: ['a', 'b', 'c']")
print(f"Output: {trainer.initial_alphabet}")
print(f"Expected: ['a', 'b', 'c'] (preserving order)")
print(f"Actual: {trainer.initial_alphabet}")
print()

# With multi-character strings (should take first char)
trainer = trainers.BpeTrainer(initial_alphabet=['abc', 'def', 'xyz'])
print(f"Input: ['abc', 'def', 'xyz']")
print(f"Output: {trainer.initial_alphabet}")
print(f"Expected: ['a', 'd', 'x'] (first char of each, preserving order)")
print(f"Actual: {trainer.initial_alphabet}")