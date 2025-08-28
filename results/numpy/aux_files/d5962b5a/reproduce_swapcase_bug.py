import numpy as np
import numpy.char as nc

# Bug: numpy.char.swapcase silently truncates when output exceeds dtype size
arr = np.array(['ß'])  # Creates dtype '<U1' (1 character)
result = nc.swapcase(arr)

print(f"Input: {arr[0]}")
print(f"Expected: 'SS' (German ß uppercases to SS)")
print(f"Actual: {result[0]}")
print(f"Bug: Result is truncated from 'SS' to 'S'")

# The issue is that swapcase doesn't resize the array dtype when needed
print(f"\nInput dtype: {arr.dtype}")
print(f"Output dtype: {result.dtype}")
print("The output dtype should be <U2 to accommodate 'SS', but it remains <U1")