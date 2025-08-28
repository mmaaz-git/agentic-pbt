#!/usr/bin/env python3
"""
Analyze properties of awkward._connect.cling module
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
from awkward._connect import cling
import inspect

# Test togenerator function - it converts forms to generators
print("=== Testing togenerator function ===")

# Create some sample forms to test
import awkward.forms as forms

# Test with different form types
test_forms = [
    forms.NumpyForm(primitive="float64"),
    forms.NumpyForm(primitive="int32"),
    forms.EmptyForm(),
    forms.RegularForm(forms.NumpyForm("float32"), size=10),
    forms.ListOffsetForm("i64", forms.NumpyForm("int64")),
]

print("Testing togenerator with different forms:")
for form in test_forms:
    try:
        generator = cling.togenerator(form, flatlist_as_rvec=False)
        print(f"  {type(form).__name__} -> {type(generator).__name__}")
        
        # Check if generator has expected methods
        has_generate = hasattr(generator, 'generate')
        has_class_type = hasattr(generator, 'class_type')
        has_value_type = hasattr(generator, 'value_type')
        print(f"    Has methods: generate={has_generate}, class_type={has_class_type}, value_type={has_value_type}")
        
        # Test class_type and value_type
        if has_class_type:
            ct = generator.class_type()
            print(f"    class_type: {ct}")
        if has_value_type:
            vt = generator.value_type()
            print(f"    value_type: {vt}")
            
    except Exception as e:
        print(f"  {type(form).__name__} -> Error: {e}")

# Test with flatlist_as_rvec=True
print("\n=== Testing with flatlist_as_rvec=True ===")
for form in test_forms[:2]:  # Just test a couple
    try:
        gen_false = cling.togenerator(form, flatlist_as_rvec=False)
        gen_true = cling.togenerator(form, flatlist_as_rvec=True)
        
        # Check if they produce different results
        ct_false = gen_false.class_type()
        ct_true = gen_true.class_type()
        
        print(f"{type(form).__name__}:")
        print(f"  flatlist_as_rvec=False: {ct_false}")
        print(f"  flatlist_as_rvec=True: {ct_true}")
        print(f"  Different: {ct_false != ct_true}")
    except Exception as e:
        print(f"{type(form).__name__}: Error - {e}")

# Test idempotence - calling togenerator twice should produce equivalent generators
print("\n=== Testing idempotence property ===")
for form in test_forms[:3]:
    try:
        gen1 = cling.togenerator(form, flatlist_as_rvec=False)
        gen2 = cling.togenerator(form, flatlist_as_rvec=False)
        
        # They should be equal or at least produce the same class_type
        ct1 = gen1.class_type()
        ct2 = gen2.class_type()
        
        print(f"{type(form).__name__}: class_type match = {ct1 == ct2}")
    except Exception as e:
        print(f"{type(form).__name__}: Error - {e}")

# Test generate_headers, generate_ArrayView, etc.
print("\n=== Testing header generation functions ===")

# Create a mock compiler that just collects the output
class MockCompiler:
    def __init__(self):
        self.compiled = []
    
    def __call__(self, code):
        self.compiled.append(code)
        return None

compiler = MockCompiler()

# Test header generation functions
try:
    headers = cling.generate_headers(compiler, use_cached=False)
    print(f"generate_headers returned {len(headers)} chars of code")
    print(f"Headers contain '#include': {'#include' in headers}")
    
    array_view = cling.generate_ArrayView(compiler, use_cached=False)
    print(f"generate_ArrayView returned {len(array_view)} chars of code")
    print(f"ArrayView contains 'namespace awkward': {'namespace awkward' in array_view}")
    
    record_view = cling.generate_RecordView(compiler, use_cached=False)
    print(f"generate_RecordView returned {len(record_view)} chars of code")
    
    array_builder = cling.generate_ArrayBuilder(compiler, use_cached=False)
    print(f"generate_ArrayBuilder returned {len(array_builder)} chars of code")
except Exception as e:
    print(f"Error in header generation: {e}")

# Check cache behavior
print("\n=== Testing cache behavior ===")
compiler2 = MockCompiler()
headers1 = cling.generate_headers(compiler2, use_cached=True)
headers2 = cling.generate_headers(compiler2, use_cached=True)
print(f"Cached headers are identical: {headers1 is headers2}")

# Clear cache and test again
cling.cache.clear()
compiler3 = MockCompiler()
headers3 = cling.generate_headers(compiler3, use_cached=True)
headers4 = cling.generate_headers(compiler3, use_cached=True)
print(f"After cache clear, cached headers are identical: {headers3 is headers4}")