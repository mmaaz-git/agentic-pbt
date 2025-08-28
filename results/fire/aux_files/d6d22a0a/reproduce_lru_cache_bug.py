import fire.test_components_py3 as components

# Minimal reproduction of LRU cache bug
print("Testing lru_cache_decorated with list input:")
try:
    result = components.lru_cache_decorated([1, 2, 3])
    print(f"Result: {result}")
except TypeError as e:
    print(f"Error: {e}")

print("\nTesting LruCacheDecoratedMethod with list input:")
try:
    obj = components.LruCacheDecoratedMethod()
    result = obj.lru_cache_in_class([1, 2, 3])
    print(f"Result: {result}")
except TypeError as e:
    print(f"Error: {e}")

print("\nTesting with hashable input (should work):")
print(f"lru_cache_decorated(42) = {components.lru_cache_decorated(42)}")
obj = components.LruCacheDecoratedMethod()
print(f"lru_cache_in_class(42) = {obj.lru_cache_in_class(42)}")