"""Test the extent of the record field preservation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak

print("Test 1: Records with progressively more fields")
builder = ak.ArrayBuilder()

# Record 1: only field 'a'
builder.begin_record()
builder.field("a").integer(1)
builder.end_record()

# Record 2: fields 'a' and 'b'
builder.begin_record()
builder.field("a").integer(2)
builder.field("b").integer(20)
builder.end_record()

# Record 3: fields 'a', 'b', and 'c'
builder.begin_record()
builder.field("a").integer(3)
builder.field("b").integer(30)
builder.field("c").integer(300)
builder.end_record()

result = builder.snapshot().to_list()
print("Expected: [{'a': 1}, {'a': 2, 'b': 20}, {'a': 3, 'b': 30, 'c': 300}]")
print(f"Actual:   {result}")

print("\n" + "="*60)
print("Test 2: Records with different field sets")
builder2 = ak.ArrayBuilder()

# Record 1: fields 'x' and 'y'
builder2.begin_record()
builder2.field("x").integer(1)
builder2.field("y").integer(10)
builder2.end_record()

# Record 2: fields 'y' and 'z' (no 'x')
builder2.begin_record()
builder2.field("y").integer(20)
builder2.field("z").integer(200)
builder2.end_record()

# Record 3: only field 'z'
builder2.begin_record()
builder2.field("z").integer(300)
builder2.end_record()

result2 = builder2.snapshot().to_list()
print("Expected: [{'x': 1, 'y': 10}, {'y': 20, 'z': 200}, {'z': 300}]")
print(f"Actual:   {result2}")

print("\n" + "="*60)
print("Test 3: Mixed types in record fields")
builder3 = ak.ArrayBuilder()

# Record 1: integer field
builder3.begin_record()
builder3.field("value").integer(42)
builder3.end_record()

# Record 2: float field with same name
builder3.begin_record()
builder3.field("value").real(3.14)
builder3.end_record()

# Record 3: string field with same name
builder3.begin_record()
builder3.field("value").string("hello")
builder3.end_record()

result3 = builder3.snapshot().to_list()
print("Expected: [{'value': 42}, {'value': 3.14}, {'value': 'hello'}]")
print(f"Actual:   {result3}")