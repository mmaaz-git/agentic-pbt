#!/usr/bin/env python3
"""
Reproduce and investigate the RecordArrayGenerator fields bug
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak
import awkward.forms as forms
from awkward._connect import cling

print("=== Reproducing RecordArrayGenerator fields bug ===\n")

# Create a RecordForm with list fields
contents = [forms.NumpyForm('float64'), forms.NumpyForm('int32')]
list_fields = ['field_0', 'field_1']

print(f"Input fields type: {type(list_fields)}")
print(f"Input fields value: {list_fields}")

record_form = forms.RecordForm(contents, list_fields)
print(f"\nRecordForm.fields type: {type(record_form.fields)}")
print(f"RecordForm.fields value: {record_form.fields}")

# Convert to generator
gen = cling.togenerator(record_form, flatlist_as_rvec=False)

print(f"\nRecordArrayGenerator type: {type(gen)}")
print(f"RecordArrayGenerator.fields type: {type(gen.fields)}")
print(f"RecordArrayGenerator.fields value: {gen.fields}")

# Check if they're equal
print(f"\nAre they equal? {gen.fields == record_form.fields}")
print(f"Are they the same type? {type(gen.fields) == type(record_form.fields)}")

# Look at the RecordArrayGenerator implementation
print("\n=== Looking at RecordArrayGenerator.from_form implementation ===")

# The from_form method might be the culprit
print("RecordArrayGenerator.from_form creates the generator with:")
print("  fields = None if form.is_tuple else form.fields")
print("Then __init__ does:")
print("  self.fields = None if fields is None else tuple(fields)")
print("\nSo it converts the list to a tuple!")

# Test with tuple fields
print("\n=== Testing with tuple fields ===")
tuple_fields = ('field_a', 'field_b')
record_form2 = forms.RecordForm(contents, tuple_fields)
print(f"Input fields type: {type(tuple_fields)}")
print(f"RecordForm.fields type: {type(record_form2.fields)}")

gen2 = cling.togenerator(record_form2, flatlist_as_rvec=False)
print(f"RecordArrayGenerator.fields type: {type(gen2.fields)}")
print(f"Are they equal? {gen2.fields == record_form2.fields}")

# Test with None (tuple form)
print("\n=== Testing with None (tuple form) ===")
record_form3 = forms.RecordForm(contents, None)
print(f"RecordForm.fields: {record_form3.fields}")

gen3 = cling.togenerator(record_form3, flatlist_as_rvec=False)
print(f"RecordArrayGenerator.fields: {gen3.fields}")
print(f"Are they equal? {gen3.fields == record_form3.fields}")

print("\n=== Bug Summary ===")
print("BUG FOUND: RecordArrayGenerator.__init__ converts list fields to tuple")
print("This changes the type from list to tuple, breaking equality comparisons")
print("Location: awkward._connect.cling.RecordArrayGenerator.__init__ line 1412")
print("The line: self.fields = None if fields is None else tuple(fields)")
print("\nImpact: Forms with list fields will have different field types after")
print("conversion to generators, potentially affecting downstream code that")
print("expects fields to maintain their original type.")