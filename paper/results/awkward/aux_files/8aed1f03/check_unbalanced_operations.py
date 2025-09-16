"""Check if unbalanced operations are allowed or should raise errors"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import awkward as ak

print("Testing unbalanced list operations...")
builder1 = ak.ArrayBuilder()
builder1.begin_list()
builder1.integer(1)
# Missing end_list()

try:
    result = builder1.snapshot()
    print(f"Snapshot succeeded with unbalanced list: {result.to_list()}")
    print("This means unbalanced lists are auto-closed (not a bug)")
except Exception as e:
    print(f"Snapshot failed with error: {e}")
    print("This means unbalanced lists are not allowed (expected behavior)")

print("\nTesting unbalanced record operations...")
builder2 = ak.ArrayBuilder()
builder2.begin_record()
builder2.field("x").integer(1)
# Missing end_record()

try:
    result = builder2.snapshot()
    print(f"Snapshot succeeded with unbalanced record: {result.to_list()}")
    print("This means unbalanced records are auto-closed (not a bug)")
except Exception as e:
    print(f"Snapshot failed with error: {e}")
    print("This means unbalanced records are not allowed (expected behavior)")