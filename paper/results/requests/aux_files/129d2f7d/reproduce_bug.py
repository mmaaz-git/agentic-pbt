from requests.hooks import dispatch_hook

# Minimal reproduction of the bug
print("Testing dispatch_hook with non-dict hooks argument...")

# Test with string
try:
    result = dispatch_hook("test", "not a dict", "some data")
    print(f"String hooks: {result}")
except AttributeError as e:
    print(f"String hooks failed: {e}")

# Test with list
try:
    result = dispatch_hook("test", [1, 2, 3], "some data")
    print(f"List hooks: {result}")
except AttributeError as e:
    print(f"List hooks failed: {e}")

# Test with integer
try:
    result = dispatch_hook("test", 42, "some data")
    print(f"Integer hooks: {result}")
except AttributeError as e:
    print(f"Integer hooks failed: {e}")

# Test with set
try:
    result = dispatch_hook("test", {"a", "b"}, "some data")
    print(f"Set hooks: {result}")
except AttributeError as e:
    print(f"Set hooks failed: {e}")

# What should work: dict or None
print("\nCorrect usage (for comparison):")
result = dispatch_hook("test", {"test": lambda x, **k: x + "_modified"}, "data")
print(f"Dict hooks: {result}")

result = dispatch_hook("test", None, "data")
print(f"None hooks: {result}")