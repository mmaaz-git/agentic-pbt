import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.shared.cache_dict import LRUDict

# Test LRUDict.get() with falsy values
cache = LRUDict(max_items=3)

print("Testing LRUDict.get() with falsy values...")
print("-" * 40)

# Add three items, middle one is falsy (0)
cache["a"] = "first"
cache["b"] = 0  # falsy value
cache["c"] = "third"

print(f"Initial cache (3 items): {dict(cache)}")
print(f"Order (oldest to newest): {list(cache.keys())}")

# Access the falsy value using get()
value = cache.get("b")
print(f"\nAccessed cache.get('b') = {value}")
print(f"Order after get('b'): {list(cache.keys())}")
print("Expected order: ['a', 'c', 'b'] (b should move to end)")

# Add a fourth item to trigger eviction
cache["d"] = "fourth"
print(f"\nAfter adding 'd' (triggers eviction): {dict(cache)}")
print(f"Keys remaining: {list(cache.keys())}")

if "b" not in cache:
    print("\nBUG CONFIRMED: Key 'b' (with value 0) was evicted!")
    print("This happened because get() doesn't call move_to_end() for falsy values.")
    print("The bug is on line 29-30 of cache_dict.py:")
    print("    if item:  # <- This check is wrong!")
    print("        self.move_to_end(key=key)")
elif "a" not in cache:
    print("\nCorrect behavior: Key 'a' was evicted (oldest unused item)")
else:
    print("\nUnexpected state - checking what was evicted...")
    print(f"Current keys: {list(cache.keys())}")

print("\n" + "=" * 40)
print("Testing with another falsy value (empty string)...")
cache2 = LRUDict(max_items=3)
cache2["x"] = "first"
cache2["y"] = ""  # empty string
cache2["z"] = "third"

print(f"Initial: {dict(cache2)}")
value = cache2.get("y")
print(f"After get('y'): value={value!r}")
cache2["w"] = "fourth"
print(f"After adding 'w': {dict(cache2)}")

if "y" not in cache2:
    print("BUG: Empty string key 'y' was evicted despite recent access!")