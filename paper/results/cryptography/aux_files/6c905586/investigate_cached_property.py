import cryptography.utils as utils

# Investigate the cached_property implementation
class TestClass:
    @utils.cached_property
    def my_prop(self):
        return 42

obj = TestClass()

# Access the property
print(f"Property value: {obj.my_prop}")

# Check what attribute name is actually used for caching
print(f"Object attributes after access: {[attr for attr in dir(obj) if not attr.startswith('__')]}")

# Let's trace through the code
def test_func(self):
    return 99

# What does cached_property return?
cached_func = utils.cached_property(test_func)
print(f"cached_property returns: {type(cached_func)}")
print(f"cached_property func: {cached_func}")

# The issue is in line 118 of utils.py:
# cached_name = f"_cached_{func}"
# This uses the function object itself in the f-string, not its name!

# Let's verify this
print(f"Function object: {test_func}")
print(f"What gets created: _cached_{test_func}")