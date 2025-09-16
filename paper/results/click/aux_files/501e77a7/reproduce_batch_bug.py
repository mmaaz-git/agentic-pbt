from click.core import batch

print("Bug reproduction for click.core.batch function")
print("=" * 50)

# Bug 1: Elements lost when input smaller than batch_size
print("\nBug 1: Elements lost when len(input) < batch_size")
items = [1, 2, 3]
batch_size = 5
result = batch(items, batch_size)
print(f"Input: {items}")
print(f"Batch size: {batch_size}")
print(f"Output: {result}")
print(f"Expected: [(1, 2, 3)]")
print(f"Lost elements: {items}")

# Bug 2: Trailing elements lost when not forming complete batch
print("\nBug 2: Trailing elements lost")
items = [1, 2, 3, 4, 5]
batch_size = 2
result = batch(items, batch_size)
flattened = [item for b in result for item in b]
print(f"Input: {items}")
print(f"Batch size: {batch_size}")
print(f"Output: {result}")
print(f"Flattened output: {flattened}")
print(f"Expected flattened: {items}")
print(f"Lost element: {5}")

# How the bug happens
print("\n" + "=" * 50)
print("Why this happens:")
print("The batch function uses: zip(*repeat(iter(iterable), batch_size))")
print("This creates batch_size references to the SAME iterator.")
print("zip() stops when it can't get an element from ALL iterators.")
print("Since they're the same iterator, remaining elements < batch_size are lost.")

# Correct implementation
def batch_correct(iterable, batch_size):
    """Correct implementation that preserves all elements"""
    import itertools
    it = iter(iterable)
    while True:
        batch = tuple(itertools.islice(it, batch_size))
        if not batch:
            break
        yield batch

print("\n" + "=" * 50)
print("Testing correct implementation:")
for items, batch_size in [([1, 2, 3], 5), ([1, 2, 3, 4, 5], 2)]:
    result = list(batch_correct(items, batch_size))
    flattened = [item for b in result for item in b]
    print(f"\nInput: {items}, batch_size: {batch_size}")
    print(f"Output: {result}")
    print(f"Preserves all elements: {flattened == items}")