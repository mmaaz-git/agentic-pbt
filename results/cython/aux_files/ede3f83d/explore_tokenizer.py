#!/usr/bin/env python3
import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import sudachipy.tokenizer as tokenizer_module
from sudachipy.tokenizer import Tokenizer

print("Tokenizer class details:")
print("=" * 50)
print("Full docstring:")
print(Tokenizer.__doc__)
print("\n" + "=" * 50)

# Look at methods in detail
print("\nTokenizer methods:")
for attr_name in dir(Tokenizer):
    if not attr_name.startswith('_'):
        attr = getattr(Tokenizer, attr_name)
        if callable(attr) and not inspect.isclass(attr):
            print(f"\n{attr_name}:")
            if hasattr(attr, '__doc__') and attr.__doc__:
                print(f"  Docstring: {attr.__doc__}")
            try:
                sig = inspect.signature(attr)
                print(f"  Signature: {sig}")
            except:
                print("  (Signature not available)")
                
# Check for SplitMode which seems to be an enum or nested class
print("\n" + "=" * 50)
print("\nSplitMode details:")
if hasattr(Tokenizer, 'SplitMode'):
    split_mode = Tokenizer.SplitMode
    print(f"Type: {type(split_mode)}")
    print(f"Members: {[m for m in dir(split_mode) if not m.startswith('_')]}")
    
# Try to see if there's a way to create a Tokenizer instance
print("\n" + "=" * 50)
print("\nChecking for Dictionary class (mentioned in docstring):")
try:
    import sudachipy
    if hasattr(sudachipy, 'Dictionary'):
        print("Dictionary class found!")
        print(f"Dictionary.create signature: {inspect.signature(sudachipy.Dictionary.create) if hasattr(sudachipy.Dictionary, 'create') else 'Not found'}")
except ImportError:
    pass