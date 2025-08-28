import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.shared.functions import slice_dictionary

# Minimal reproduction of the slice_dictionary bug
data = {'0': 0, '00': 0}
chunk_size = 1

print(f"Original dictionary: {data}")
print(f"Chunk size: {chunk_size}")

chunks = list(slice_dictionary(data, chunk_size))
print(f"Chunks generated: {chunks}")

# Reconstruct the dictionary
reconstructed = {}
for chunk in chunks:
    reconstructed.update(chunk)

print(f"Reconstructed dictionary: {reconstructed}")

if reconstructed != data:
    print(f"\nBUG FOUND: Data loss during slicing!")
    print(f"Missing keys: {set(data.keys()) - set(reconstructed.keys())}")
    print("\nThe bug is in the implementation - it uses itertools.islice incorrectly,"
          "\ncausing it to skip keys when generating chunks.")