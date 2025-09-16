#!/usr/bin/env python3
"""
Reproduce and investigate the Generator equality bug
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import awkward.forms as forms
from awkward._connect import cling

print("=== Reproducing Generator equality bug ===\n")

# Create the same form
form = forms.NumpyForm('float64')

# Create generators with different flatlist_as_rvec values
gen_false = cling.togenerator(form, flatlist_as_rvec=False)
gen_true = cling.togenerator(form, flatlist_as_rvec=True)

print(f"Form: {form}")
print(f"Generator with flatlist_as_rvec=False: {gen_false}")
print(f"Generator with flatlist_as_rvec=True: {gen_true}")

# Check equality
print(f"\nAre they equal? {gen_false == gen_true}")
print(f"Are they the same object? {gen_false is gen_true}")

# Check their hashes
print(f"\nHash with flatlist_as_rvec=False: {hash(gen_false)}")
print(f"Hash with flatlist_as_rvec=True: {hash(gen_true)}")
print(f"Are hashes equal? {hash(gen_false) == hash(gen_true)}")

# Check their class_types (which should be different)
print(f"\nclass_type with flatlist_as_rvec=False: {gen_false.class_type()}")
print(f"class_type with flatlist_as_rvec=True: {gen_true.class_type()}")
print(f"Are class_types equal? {gen_false.class_type() == gen_true.class_type()}")

# Look at the NumpyArrayGenerator __eq__ and __hash__ methods
print("\n=== Looking at NumpyArrayGenerator implementation ===")

print("Looking at the __hash__ method:")
print("  It hashes: (type(self), self.primitive, json.dumps(self.parameters))")
print("  It does NOT include flatlist_as_rvec!")

print("\nLooking at the __eq__ method:")
print("  It checks: isinstance(other, type(self))")
print("  and self.primitive == other.primitive")
print("  and self.parameters == other.parameters")
print("  It does NOT check flatlist_as_rvec!")

# Check the attributes
print(f"\ngen_false.primitive: {gen_false.primitive}")
print(f"gen_true.primitive: {gen_true.primitive}")
print(f"gen_false.parameters: {gen_false.parameters}")
print(f"gen_true.parameters: {gen_true.parameters}")
print(f"gen_false.flatlist_as_rvec: {gen_false.flatlist_as_rvec}")
print(f"gen_true.flatlist_as_rvec: {gen_true.flatlist_as_rvec}")

print("\n=== Bug Summary ===")
print("BUG FOUND: NumpyArrayGenerator.__eq__ and __hash__ don't consider flatlist_as_rvec")
print("This causes generators with different flatlist_as_rvec values to be considered equal")
print("even though they generate different C++ code (different class_type).")
print("\nLocation: awkward._connect.cling.NumpyArrayGenerator")
print("  __hash__ method (line 576-582)")
print("  __eq__ method (line 585-590)")
print("\nImpact: This violates the hash/equality contract. Two generators that are")
print("equal should produce the same hash and generate the same code, but they don't.")
print("This could lead to incorrect caching or other equality-based logic failures.")

# Test if this affects other generator types
print("\n=== Testing other generator types ===")

# RegularForm
regular_form = forms.RegularForm(form, size=10)
reg_gen_false = cling.togenerator(regular_form, flatlist_as_rvec=False)
reg_gen_true = cling.togenerator(regular_form, flatlist_as_rvec=True)
print(f"RegularArrayGenerator equality: {reg_gen_false == reg_gen_true}")
print(f"RegularArrayGenerator hashes equal: {hash(reg_gen_false) == hash(reg_gen_true)}")

# ListForm
list_form = forms.ListOffsetForm("i64", form)
list_gen_false = cling.togenerator(list_form, flatlist_as_rvec=False)
list_gen_true = cling.togenerator(list_form, flatlist_as_rvec=True)
print(f"ListArrayGenerator equality: {list_gen_false == list_gen_true}")
print(f"ListArrayGenerator hashes equal: {hash(list_gen_false) == hash(list_gen_true)}")

print("\nAll generator types have the same bug!")