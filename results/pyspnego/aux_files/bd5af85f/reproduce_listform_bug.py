#!/usr/bin/env python3
"""
Minimal reproduction of the ListForm.length_one_array() bug
"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward.forms as forms

# Create a ListForm with any content
list_form = forms.ListForm('i8', 'i8', forms.NumpyForm('bool'))

# This should create an array with length 1, but it crashes
try:
    arr = list_form.length_one_array()
    print(f"Success: Created array with length {len(arr)}")
except ValueError as e:
    print(f"BUG FOUND: {e}")
    print(f"Form: {list_form}")
    
    # Let's try with different index types to see if the issue is specific
    for idx_type in ["i8", "u8", "i32", "u32", "i64"]:
        test_form = forms.ListForm(idx_type, idx_type, forms.NumpyForm('bool'))
        try:
            test_form.length_one_array()
            print(f"  {idx_type}: SUCCESS")
        except Exception as e:
            print(f"  {idx_type}: FAILS with {type(e).__name__}")
    
    # Let's also test with ListOffsetForm to compare
    print("\nComparing with ListOffsetForm:")
    offset_form = forms.ListOffsetForm('i8', forms.NumpyForm('bool'))
    try:
        arr = offset_form.length_one_array()
        print(f"ListOffsetForm: SUCCESS (length={len(arr)})")
    except Exception as e:
        print(f"ListOffsetForm: FAILS with {e}")