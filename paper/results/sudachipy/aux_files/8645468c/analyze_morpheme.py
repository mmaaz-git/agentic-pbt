#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

import inspect
import sudachipy
from sudachipy import Morpheme, MorphemeList, Dictionary, Tokenizer

print("=== Module Structure ===")
print(f"Module file: {sudachipy.__file__}")
print(f"Version: {sudachipy.__version__}")

print("\n=== Morpheme Class ===")
print(f"Type: {type(Morpheme)}")
print("\nPublic methods of Morpheme:")
for name, method in inspect.getmembers(Morpheme):
    if not name.startswith('_') and callable(method):
        sig = None
        doc = None
        try:
            sig = inspect.signature(method)
            doc = method.__doc__
        except:
            pass
        print(f"  - {name}{sig if sig else '()'}")
        if doc:
            first_line = doc.strip().split('\n')[0] if doc else ''
            if first_line:
                print(f"    Doc: {first_line}")

print("\n=== MorphemeList Class ===")
print("\nPublic methods of MorphemeList:")
for name, method in inspect.getmembers(MorphemeList):
    if not name.startswith('_') and callable(method):
        sig = None
        doc = None
        try:
            sig = inspect.signature(method)
            doc = method.__doc__
        except:
            pass
        print(f"  - {name}{sig if sig else '()'}")
        if doc:
            first_line = doc.strip().split('\n')[0] if doc else ''
            if first_line:
                print(f"    Doc: {first_line}")

print("\n=== Testing Basic Functionality ===")
try:
    # Try to create a dictionary and tokenizer
    from sudachipy import Dictionary
    dict_obj = Dictionary()
    tokenizer = dict_obj.create()
    
    # Test tokenizing some text
    text = "東京へ行く"
    morphemes = tokenizer.tokenize(text)
    
    print(f"Tokenized '{text}' into {len(morphemes)} morphemes")
    for i, m in enumerate(morphemes):
        print(f"  Morpheme {i}: surface='{m.surface()}', begin={m.begin()}, end={m.end()}")
    
    # Test morpheme properties
    if len(morphemes) > 0:
        m = morphemes[0]
        print(f"\nFirst morpheme properties:")
        print(f"  - surface(): {m.surface()}")
        print(f"  - begin(): {m.begin()}")
        print(f"  - end(): {m.end()}")
        print(f"  - len(): {len(m)}")
        print(f"  - is_oov(): {m.is_oov()}")
        print(f"  - part_of_speech(): {m.part_of_speech()}")
        print(f"  - dictionary_form(): {m.dictionary_form()}")
        print(f"  - normalized_form(): {m.normalized_form()}")
        print(f"  - reading_form(): {m.reading_form()}")
        
except ImportError as e:
    print(f"Error: Could not import dictionary - {e}")
    print("May need to install sudachidict_core or similar")
except Exception as e:
    print(f"Error during testing: {e}")
    import traceback
    traceback.print_exc()