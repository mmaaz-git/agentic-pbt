import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.shared.cache_dict import LRUDict

# More detailed test of LRUDict.get() behavior
cache = LRUDict(max_items=3)

print("Detailed LRUDict.get() test")
print("=" * 50)

# Add items
cache["a"] = "truthy"
cache["b"] = 0  # falsy
cache["c"] = "another truthy"

print(f"Initial state: {dict(cache)}")
print(f"Initial order: {list(cache.keys())}")

# Test 1: Access truthy value with get()
print("\nTest 1: Access truthy value 'a' with get()")
val = cache.get("a")
print(f"  Value: {val}")
print(f"  Order after: {list(cache.keys())}")
print(f"  Expected: ['b', 'c', 'a'] (a moved to end)")

# Reset
cache = LRUDict(max_items=3)
cache["a"] = "truthy"
cache["b"] = 0  # falsy
cache["c"] = "another truthy"

print("\nTest 2: Access falsy value 'b' with get()")
val = cache.get("b")
print(f"  Value: {val}")
print(f"  Order after: {list(cache.keys())}")
print(f"  Expected: ['a', 'c', 'b'] (b should move to end)")

if list(cache.keys()) != ['a', 'c', 'b']:
    print("  BUG CONFIRMED: Falsy value not moved to end!")
    
# Test with __getitem__ for comparison
cache = LRUDict(max_items=3)
cache["a"] = "truthy"
cache["b"] = 0  # falsy
cache["c"] = "another truthy"

print("\nTest 3: Access falsy value 'b' with __getitem__ (cache['b'])")
val = cache["b"]
print(f"  Value: {val}")
print(f"  Order after: {list(cache.keys())}")
print(f"  Expected: ['a', 'c', 'b'] (b should move to end)")

# Now let's test eviction behavior
print("\n" + "=" * 50)
print("Testing eviction behavior with get() access patterns")

cache = LRUDict(max_items=3)
cache["a"] = 1
cache["b"] = 0  # falsy
cache["c"] = 3

print(f"Initial: {list(cache.keys())}")

# Access b with get (falsy value - won't move to end due to bug)
cache.get("b")
print(f"After get('b'): {list(cache.keys())}")

# Access a with get (truthy value - will move to end)
cache.get("a") 
print(f"After get('a'): {list(cache.keys())}")

# Now add d - what gets evicted?
cache["d"] = 4
print(f"After adding 'd': {list(cache.keys())}")

# The bug: 'b' wasn't moved when accessed, so it's still in its original position
# and might get evicted incorrectly based on the internal ordering