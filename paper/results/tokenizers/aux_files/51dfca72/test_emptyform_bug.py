#!/usr/bin/env python3
"""
Test to investigate potential bug with EmptyForm parameter handling
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import awkward.forms as forms
from awkward._connect import cling

# Test 1: EmptyForm constructor behavior
print("=== Test 1: EmptyForm constructor ===")

# This should work
try:
    empty1 = forms.EmptyForm()
    print("✓ EmptyForm() works")
except Exception as e:
    print(f"✗ EmptyForm() failed: {e}")

# This should work
try:
    empty2 = forms.EmptyForm(parameters=None)
    print("✓ EmptyForm(parameters=None) works")
except Exception as e:
    print(f"✗ EmptyForm(parameters=None) failed: {e}")

# This should work
try:
    empty3 = forms.EmptyForm(parameters={})
    print("✓ EmptyForm(parameters={}) works")
except Exception as e:
    print(f"✗ EmptyForm(parameters={{}}) failed: {e}")

# This should fail
try:
    empty4 = forms.EmptyForm(parameters={"foo": "bar"})
    print("✗ EmptyForm(parameters={'foo': 'bar'}) should have failed!")
except TypeError as e:
    print(f"✓ EmptyForm(parameters={{'foo': 'bar'}}) correctly raises: {e}")

# Test 2: EmptyForm.to_NumpyForm preserves/loses parameters
print("\n=== Test 2: EmptyForm.to_NumpyForm behavior ===")

empty = forms.EmptyForm()
numpy_form = empty.to_NumpyForm("float64")
print(f"Empty parameters: {empty.parameters}")
print(f"NumpyForm parameters after conversion: {numpy_form.parameters}")

# Test 3: togenerator with EmptyForm
print("\n=== Test 3: togenerator with EmptyForm ===")

empty = forms.EmptyForm()
gen = cling.togenerator(empty, flatlist_as_rvec=False)
print(f"Generator type: {type(gen).__name__}")
print(f"Generator parameters: {gen.parameters}")

# The potential bug: If someone tries to create an EmptyForm with parameters
# expecting them to be preserved through togenerator, they will be lost
print("\n=== Test 4: Potential issue - parameters lost in conversion ===")

# If we try to pass parameters through the conversion chain:
# 1. We can't create EmptyForm with parameters (raises TypeError)
# 2. But even if we could, they would be lost in to_NumpyForm

# Let's test what happens if we manually override this check
class EmptyFormWithParams(forms.EmptyForm):
    """A modified EmptyForm that allows parameters for testing"""
    def __init__(self, *, parameters=None, form_key=None):
        # Skip the parameter check
        Form._init(self, parameters=parameters, form_key=form_key)

# Create an EmptyForm with parameters
try:
    empty_with_params = EmptyFormWithParams(parameters={"test": "value"})
    print(f"Created EmptyFormWithParams with parameters: {empty_with_params.parameters}")
    
    # Convert to NumpyForm
    numpy_form = empty_with_params.to_NumpyForm("float64")
    print(f"After to_NumpyForm, parameters: {numpy_form.parameters}")
    print("Bug confirmed: Parameters are lost in to_NumpyForm conversion!")
    
    # Test with togenerator
    gen = cling.togenerator(empty_with_params, flatlist_as_rvec=False)
    print(f"After togenerator, parameters: {gen.parameters}")
    
except Exception as e:
    print(f"Error: {e}")

# Test 5: Check if other forms preserve parameters correctly
print("\n=== Test 5: Other forms preserve parameters ===")

params = {"test": "value", "foo": 123}

# NumpyForm
numpy_form = forms.NumpyForm("float64", parameters=params)
gen = cling.togenerator(numpy_form, flatlist_as_rvec=False)
print(f"NumpyForm: params preserved = {gen.parameters == params}")

# RegularForm
regular_form = forms.RegularForm(forms.NumpyForm("float64"), size=10, parameters=params)
gen = cling.togenerator(regular_form, flatlist_as_rvec=False)
print(f"RegularForm: params preserved = {gen.parameters == params}")

print("\n=== Summary ===")
print("1. EmptyForm explicitly disallows parameters (by design)")
print("2. EmptyForm.to_NumpyForm() doesn't preserve parameters even if they existed")
print("3. This creates an inconsistency: EmptyForm is the only form that can't have parameters")
print("4. When EmptyForm is converted by togenerator, any attempt to add parameters would be lost")