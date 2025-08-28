#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.trainers as trainers

# Bug: WordPieceTrainer also has ordering issues with initial_alphabet
print("Bug: WordPieceTrainer initial_alphabet ordering issues")
print("-" * 50)

# Minimal failing case from Hypothesis
trainer = trainers.WordPieceTrainer(initial_alphabet=['10', '0'])
print(f"Input: ['10', '0']")
print(f"Output: {trainer.initial_alphabet}")
print(f"Expected: ['1', '0'] (first char of each, preserving order)")
print(f"Actual: {trainer.initial_alphabet}")
print()

# More examples
trainer = trainers.WordPieceTrainer(initial_alphabet=['0', '1'])
print(f"Input: ['0', '1']")
print(f"Output: {trainer.initial_alphabet}")
print()

trainer = trainers.WordPieceTrainer(initial_alphabet=['a', 'b', 'c'])
print(f"Input: ['a', 'b', 'c']")
print(f"Output: {trainer.initial_alphabet}")
print()

trainer = trainers.WordPieceTrainer(initial_alphabet=['abc', 'def', 'xyz'])
print(f"Input: ['abc', 'def', 'xyz']")
print(f"Output: {trainer.initial_alphabet}")
print(f"Expected: ['a', 'd', 'x'] (first char of each, preserving order)")
print(f"Actual: {trainer.initial_alphabet}")