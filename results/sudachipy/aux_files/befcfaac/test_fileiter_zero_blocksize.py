import sys
from io import BytesIO

sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.response import FileIter

print("Testing FileIter with block_size=0")
print("=" * 50)

# Test with some content
content = b"Hello, World!"
file_obj = BytesIO(content)

# Create FileIter with block_size=0
file_iter = FileIter(file_obj, block_size=0)

print(f"Original content: {content}")
print(f"Block size: 0")
print()

# Try to iterate
print("Attempting to iterate...")
chunks = []
max_iterations = 10

for i in range(max_iterations):
    try:
        chunk = next(file_iter)
        chunks.append(chunk)
        print(f"  Iteration {i}: got chunk of length {len(chunk)}: {repr(chunk)}")
        if len(chunk) == 0 and i > 0:
            # This could cause infinite loop!
            print("  WARNING: Got empty chunk but didn't raise StopIteration!")
            print("  This will cause an infinite loop in normal iteration!")
            break
    except StopIteration:
        print(f"  StopIteration raised after {i} iterations")
        break

print()
print(f"Total chunks collected: {len(chunks)}")
print(f"Concatenated result: {b''.join(chunks)}")

# Now test what happens in a real for loop with a timeout
print("\nTesting in a for loop (with safety limit)...")
file_obj2 = BytesIO(b"Test")
file_iter2 = FileIter(file_obj2, block_size=0)

iteration_count = 0
for chunk in file_iter2:
    iteration_count += 1
    print(f"  Got chunk: {repr(chunk)}")
    if iteration_count > 5:
        print("  STOPPED: Infinite loop detected!")
        break

print(f"\nConclusion: FileIter with block_size=0 causes infinite loop returning empty bytes")