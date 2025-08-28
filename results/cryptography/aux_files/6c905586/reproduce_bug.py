import cryptography.utils as utils

class Example:
    call_count = 0
    
    @utils.cached_property  
    def my_property(self):
        Example.call_count += 1
        return 42

obj = Example()

# First access
value1 = obj.my_property
print(f"First access: {value1}, call_count: {Example.call_count}")

# The cached attribute has an unusable name
cached_attrs = [attr for attr in dir(obj) if attr.startswith('_cached_')]
print(f"Cached attributes: {cached_attrs}")

# We can't easily access or delete the cache programmatically
expected_cache_name = '_cached_my_property'
actual_cache_name = cached_attrs[0] if cached_attrs else None

print(f"Expected cache name: {expected_cache_name}")
print(f"Actual cache name: {actual_cache_name}")
print(f"Can access by expected name: {hasattr(obj, expected_cache_name)}")

# This makes it impossible to clear the cache in a clean way
try:
    delattr(obj, expected_cache_name)
    print("Successfully deleted cache")
except AttributeError as e:
    print(f"Cannot delete cache: {e}")