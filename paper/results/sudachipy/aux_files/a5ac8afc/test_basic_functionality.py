#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import sudachipy
from sudachipy import Dictionary

# Test basic functionality
try:
    # Create a dictionary
    print("Creating dictionary...")
    dict_obj = Dictionary()
    print("Dictionary created successfully")
    
    # Create a tokenizer
    print("Creating tokenizer...")
    tokenizer = dict_obj.create()
    print("Tokenizer created successfully")
    
    # Test tokenization with simple text
    print("Testing tokenization...")
    text = "こんにちは"
    result = tokenizer.tokenize(text)
    print(f"Tokenization result for '{text}': {len(result)} morphemes")
    for morpheme in result:
        print(f"  - {morpheme.surface()} [{morpheme.begin()}:{morpheme.end()}]")
    
    # Test pos_of
    print("\nTesting pos_of...")
    pos_result = dict_obj.pos_of(0)
    print(f"POS for id 0: {pos_result}")
    
    pos_result = dict_obj.pos_of(999999)
    print(f"POS for id 999999: {pos_result}")
    
    # Test lookup
    print("\nTesting lookup...")
    lookup_result = dict_obj.lookup("日本")
    print(f"Lookup for '日本': {len(lookup_result)} results")
    
    # Close dictionary
    dict_obj.close()
    print("\nDictionary closed successfully")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()