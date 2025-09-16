#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import inspect
import tokenizers.trainers as trainers

print("=== Module Information ===")
print(f"Module file: {trainers.__file__}")
print(f"Module package: {trainers.__package__}")

print("\n=== Available Classes ===")
members = inspect.getmembers(trainers, inspect.isclass)
for name, cls in members:
    print(f"\n{name}:")
    print(f"  MRO: {[c.__name__ for c in cls.__mro__]}")
    
    try:
        sig = inspect.signature(cls.__init__)
        print(f"  Signature: {sig}")
    except:
        print("  Signature: (Unable to get signature)")
    
    if cls.__doc__:
        print(f"  Docstring preview: {cls.__doc__[:200]}...")

print("\n=== Trying to instantiate trainers ===")

try:
    bpe = trainers.BpeTrainer()
    print(f"BpeTrainer instantiated: {bpe}")
    print(f"  Type: {type(bpe)}")
    print(f"  Attributes: {dir(bpe)}")
except Exception as e:
    print(f"BpeTrainer error: {e}")

try:
    unigram = trainers.UnigramTrainer()
    print(f"\nUnigramTrainer instantiated: {unigram}")
    print(f"  Type: {type(unigram)}")
    print(f"  Attributes: {dir(unigram)}")
except Exception as e:
    print(f"UnigramTrainer error: {e}")

try:
    wordlevel = trainers.WordLevelTrainer()
    print(f"\nWordLevelTrainer instantiated: {wordlevel}")
    print(f"  Type: {type(wordlevel)}")
    print(f"  Attributes: {dir(wordlevel)}")
except Exception as e:
    print(f"WordLevelTrainer error: {e}")

try:
    wordpiece = trainers.WordPieceTrainer()
    print(f"\nWordPieceTrainer instantiated: {wordpiece}")
    print(f"  Type: {type(wordpiece)}")
    print(f"  Attributes: {dir(wordpiece)}")
except Exception as e:
    print(f"WordPieceTrainer error: {e}")