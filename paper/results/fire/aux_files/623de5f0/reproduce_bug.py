"""Minimal reproduction of the cumsums bug with mutable types."""

import fire.test_components as tc

va = tc.VarArgs()

print("Testing with lists:")
result = va.cumsums([1], [2], [3])
print(f"Input: [1], [2], [3]")
print(f"Result: {result}")
print(f"Expected: [[1], [1, 2], [1, 2, 3]]")
print(f"All same object? {result[0] is result[1] is result[2]}")
print()

print("Testing with dictionaries:")
result = va.cumsums({'a': 1}, {'b': 2})
print(f"Input: {{'a': 1}}, {{'b': 2}}")
print(f"Result: {result}")
print("All same object?", result[0] is result[1])
print()

print("Testing with numbers (should work correctly):")
result = va.cumsums(1, 2, 3)
print(f"Input: 1, 2, 3")
print(f"Result: {result}")
print(f"Expected: [1, 3, 6]")
print()

print("Testing with strings (should work correctly):")
result = va.cumsums("a", "b", "c")
print(f"Input: 'a', 'b', 'c'")
print(f"Result: {result}")
print(f"Expected: ['a', 'ab', 'abc']")