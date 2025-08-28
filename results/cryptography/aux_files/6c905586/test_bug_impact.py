import cryptography.utils as utils

# Test if the bug causes actual problems in typical usage

class MyClass:
    def __init__(self):
        self.compute_count = 0
    
    @utils.cached_property
    def expensive_computation(self):
        self.compute_count += 1
        return sum(range(1000))

# Normal usage - does caching work?
obj = MyClass()
result1 = obj.expensive_computation
result2 = obj.expensive_computation
print(f"Caching works: {obj.compute_count == 1}")  # Should be True

# The bug: cache attribute name contains function object representation
attrs = [a for a in dir(obj) if '_cached_' in a]
print(f"Cache attribute name: {attrs[0] if attrs else 'None'}")

# This is problematic because:
# 1. The attribute name is not predictable/stable
# 2. It's not human-readable  
# 3. It's impossible to programmatically clear the cache
# 4. The name includes memory addresses which change between runs

# Additionally, check if the function name itself could cause issues
def create_property_with_name(name):
    """Create a cached property with a specific function name"""
    def prop_func(self):
        return 42
    prop_func.__name__ = name
    return utils.cached_property(prop_func)

class TestNaming:
    # What happens with special names?
    strange_prop = create_property_with_name("prop-with-dashes")

try:
    obj2 = TestNaming()
    val = obj2.strange_prop
    print(f"Works with strange names: True")
except:
    print(f"Works with strange names: False")

# The real issue: the cached name should use func.__name__, not str(func)
print(f"\nThe bug: Line 118 uses f'_cached_{{func}}' instead of f'_cached_{{func.__name__}}'")