"""Minimal reproduction of slice_dictionary bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.shared.functions import slice_dictionary

# Failing case from Hypothesis
data = {'0': 0, '00': 0}
chunk_size = 1

print(f"Original dictionary: {data}")
print(f"Chunk size: {chunk_size}")
print(f"Expected: Two chunks, each with one key-value pair")
print()

# Get the chunks
chunks = list(slice_dictionary(data, chunk_size))

print(f"Number of chunks returned: {len(chunks)}")
for i, chunk in enumerate(chunks):
    print(f"  Chunk {i}: {chunk}")

# Try to reconstruct
reconstructed = {}
for chunk in chunks:
    reconstructed.update(chunk)

print()
print(f"Reconstructed: {reconstructed}")
print(f"Original:      {data}")
print(f"Are they equal? {reconstructed == data}")

if reconstructed != data:
    missing_keys = set(data.keys()) - set(reconstructed.keys())
    print(f"Missing keys: {missing_keys}")

# Let's trace through the function logic
print("\n--- Debugging the function logic ---")
print("Looking at the source code of slice_dictionary...")

import itertools

def slice_dictionary_debug(data: dict, chunk_size: int):
    """Debug version with print statements"""
    print(f"Data has {len(data)} items")
    print(f"Iterating in ranges: 0 to {len(data)} with step {chunk_size}")
    
    for i in range(0, len(data), chunk_size):
        print(f"\n  Range iteration {i}:")
        # The bug is here - itertools.islice only takes chunk_size items from the beginning each time!
        sliced_keys = list(itertools.islice(data, chunk_size))
        print(f"    islice(data, {chunk_size}) returns keys: {sliced_keys}")
        chunk = {dict_key: data[dict_key] for dict_key in sliced_keys}
        print(f"    Generated chunk: {chunk}")
        yield chunk

print("\nRunning debug version:")
debug_chunks = list(slice_dictionary_debug(data, chunk_size))