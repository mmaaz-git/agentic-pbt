#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

from sudachipy import Dictionary
from sudachipy.tokenizer import Tokenizer

# Create a tokenizer
try:
    dic = Dictionary()
    tokenizer_a = dic.create(mode="A")
    tokenizer_b = dic.create(mode="B")
    tokenizer_c = dic.create(mode="C")
    
    # Test basic tokenization
    test_text = "東京都へ行く"
    
    print("Testing basic tokenization:")
    print(f"Input text: '{test_text}'")
    print()
    
    # Test different modes
    result_a = tokenizer_a.tokenize(test_text)
    print(f"Mode A: {[m.surface() for m in result_a]}")
    
    result_b = tokenizer_b.tokenize(test_text)
    print(f"Mode B: {[m.surface() for m in result_b]}")
    
    result_c = tokenizer_c.tokenize(test_text)
    print(f"Mode C: {[m.surface() for m in result_c]}")
    
    # Test empty string
    print("\nTesting empty string:")
    empty_result = tokenizer_a.tokenize("")
    print(f"Empty string result: {[m.surface() for m in empty_result]} (len={len(empty_result)})")
    
    # Test with special characters
    print("\nTesting special characters:")
    special_text = "123　あいう　#$%"
    special_result = tokenizer_a.tokenize(special_text)
    print(f"Input: '{special_text}'")
    print(f"Result: {[m.surface() for m in special_result]}")
    
    # Test begin/end indices
    print("\nTesting indices:")
    test_text2 = "私は学生です"
    result = tokenizer_c.tokenize(test_text2)
    for m in result:
        print(f"  '{m.surface()}': begin={m.begin()}, end={m.end()}, text[{m.begin()}:{m.end()}]='{test_text2[m.begin():m.end()]}'")
        
except Exception as e:
    print(f"Error during testing: {e}")
    import traceback
    traceback.print_exc()