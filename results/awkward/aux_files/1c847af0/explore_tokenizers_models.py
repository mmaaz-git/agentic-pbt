#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import inspect
import tokenizers.models

# Get all public classes/functions
print("=== Available Models ===")
for name, obj in inspect.getmembers(tokenizers.models):
    if not name.startswith('_'):
        print(f"{name}: {type(obj)}")

print("\n=== BPE Model Details ===")
print(f"BPE signature: {inspect.signature(tokenizers.models.BPE.__init__)}")
print(f"BPE docstring: {tokenizers.models.BPE.__doc__}")

print("\n=== WordLevel Model Details ===")
print(f"WordLevel signature: {inspect.signature(tokenizers.models.WordLevel.__init__)}")
print(f"WordLevel docstring: {tokenizers.models.WordLevel.__doc__}")

print("\n=== WordPiece Model Details ===")
print(f"WordPiece signature: {inspect.signature(tokenizers.models.WordPiece.__init__)}")
print(f"WordPiece docstring: {tokenizers.models.WordPiece.__doc__}")

print("\n=== Unigram Model Details ===")
print(f"Unigram signature: {inspect.signature(tokenizers.models.Unigram.__init__)}")
print(f"Unigram docstring: {tokenizers.models.Unigram.__doc__}")

# Test basic functionality
print("\n=== Testing Basic Instantiation ===")
try:
    # Test WordLevel with simple vocab
    vocab = {"hello": 0, "world": 1, "test": 2}
    model = tokenizers.models.WordLevel(vocab, unk_token="[UNK]")
    print("WordLevel instantiated successfully")
    
    # Test basic methods
    print(f"token_to_id('hello'): {model.token_to_id('hello')}")
    print(f"id_to_token(0): {model.id_to_token(0)}")
    
    # Test tokenization
    tokens = model.tokenize("hello world")
    print(f"tokenize('hello world'): {tokens}")
    
except Exception as e:
    print(f"Error: {e}")

print("\n=== Testing BPE Model ===")
try:
    vocab = {"h": 0, "e": 1, "l": 2, "o": 3, "he": 4, "ll": 5, "hello": 6}
    merges = [("h", "e"), ("l", "l"), ("he", "llo")]
    bpe = tokenizers.models.BPE(vocab, merges, unk_token="[UNK]")
    print("BPE instantiated successfully")
    
    print(f"token_to_id('hello'): {bpe.token_to_id('hello')}")
    print(f"id_to_token(6): {bpe.id_to_token(6)}")
    
except Exception as e:
    print(f"Error: {e}")