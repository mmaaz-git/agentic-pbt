import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')
from isort import sorting

# Trace through the natural sorting implementation
def trace_natural_keys(text):
    """Trace the _natural_keys function."""
    print(f"\nTracing _natural_keys('{text}'):")
    
    # Step 1: regex split
    split_result = re.split(r"(\d+)", text)
    print(f"  re.split(r'(\\d+)', '{text}') = {split_result}")
    
    # Step 2: apply _atoi to each part
    result = []
    for part in split_result:
        atoi_result = sorting._atoi(part)
        result.append(atoi_result)
        print(f"    _atoi('{part}') = {atoi_result!r} (type: {type(atoi_result).__name__})")
    
    print(f"  Final result: {result}")
    return result

# Test cases
test_strings = [
    "file10",
    "file2", 
    "file1",
    "",
    "123",
    "abc",
    "a1b2c3",
]

print("=" * 60)
print("TRACING NATURAL KEYS IMPLEMENTATION")
print("=" * 60)

for s in test_strings:
    trace_natural_keys(s)

# Now test the full naturally function
print("\n" + "=" * 60)
print("TESTING FULL NATURALLY FUNCTION")
print("=" * 60)

test_lists = [
    ["file10", "file2", "file1"],
    ["", "a", ""],
    ["10", "2", "1"],
    [],
]

for test_list in test_lists:
    result = sorting.naturally(test_list)
    print(f"\nnaturally({test_list})")
    print(f"  Result: {result}")

# Test with custom key
print("\n" + "=" * 60)
print("TESTING WITH CUSTOM KEY")
print("=" * 60)

def custom_key(x):
    return x.upper()

test = ["File10", "file2", "FILE1"]
result = sorting.naturally(test, key=custom_key)
print(f"naturally({test}, key=str.upper)")
print(f"  Result: {result}")