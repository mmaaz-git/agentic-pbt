"""Minimal reproduction of slice_dictionary bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.shared.functions import slice_dictionary

# Test case 1: Lost key issue
print("=== Test Case 1: Lost Key Issue ===")
data1 = {'0': 0, '00': 0}
chunk_size1 = 1

print(f"Original dictionary: {data1}")
print(f"Chunk size: {chunk_size1}")

chunks1 = list(slice_dictionary(data1, chunk_size1))
print(f"Chunks: {chunks1}")

reconstructed1 = {}
for chunk in chunks1:
    reconstructed1.update(chunk)
print(f"Reconstructed: {reconstructed1}")
print(f"Lost keys: {set(data1.keys()) - set(reconstructed1.keys())}")
print()

# Test case 2: Duplicate items issue  
print("=== Test Case 2: Duplicate Items Issue ===")
data2 = {'0': 0, '1': 0, '2': 0}
chunk_size2 = 2

print(f"Original dictionary: {data2}")
print(f"Chunk size: {chunk_size2}")

chunks2 = list(slice_dictionary(data2, chunk_size2))
print(f"Chunks: {chunks2}")

total_items = sum(len(chunk) for chunk in chunks2)
print(f"Total items in chunks: {total_items}")
print(f"Original items: {len(data2)}")
print(f"Items duplicated: {total_items - len(data2)}")

# Let's check each chunk
for i, chunk in enumerate(chunks2):
    print(f"  Chunk {i}: {chunk}")
print()

# Let's also test a simple case to understand the pattern
print("=== Test Case 3: Simple Dictionary ===")
data3 = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5}
chunk_size3 = 2

print(f"Original dictionary: {data3}")
print(f"Chunk size: {chunk_size3}")

chunks3 = list(slice_dictionary(data3, chunk_size3))
print(f"Chunks: {chunks3}")

for i, chunk in enumerate(chunks3):
    print(f"  Chunk {i}: {chunk} (size: {len(chunk)})")

total_items3 = sum(len(chunk) for chunk in chunks3)
print(f"Total items in chunks: {total_items3}")
print(f"Original items: {len(data3)}")