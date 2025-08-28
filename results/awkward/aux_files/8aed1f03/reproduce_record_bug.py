"""Minimal reproduction of the record field preservation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak

# Create an ArrayBuilder
builder = ak.ArrayBuilder()

# Add first record with only field 'x'
builder.begin_record()
builder.field("x").integer(0)
builder.end_record()

# Add second record with fields 'x' and 'y'
builder.begin_record()
builder.field("x").integer(0)
builder.field("y").integer(0)
builder.end_record()

# Get the result
result = builder.snapshot().to_list()

print("Expected: [{'x': 0}, {'x': 0, 'y': 0}]")
print(f"Actual:   {result}")

# Check if this is a bug
first_record = result[0]
second_record = result[1]

print(f"\nFirst record keys: {set(first_record.keys())}")
print(f"Second record keys: {set(second_record.keys())}")

if 'y' in first_record:
    print("\nBUG CONFIRMED: First record has field 'y' when it shouldn't!")
    print(f"First record value for 'y': {first_record['y']}")
else:
    print("\nNo bug found - records have correct fields")