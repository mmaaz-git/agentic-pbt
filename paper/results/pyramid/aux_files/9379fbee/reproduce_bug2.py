import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from pyramid.threadlocal import RequestContext, get_current_request, manager

# Clear manager to ensure clean state
manager.clear()

# Simulate the test scenario more precisely
# In the test, we push items to manager BEFORE using RequestContext
items = ["item1", "item2", "item3"]
for item in items:
    manager.push({"item": item})

print("After pushing items, stack:", manager.stack)
print("Stack length:", len(manager.stack))

# Now use RequestContext
mock_request = Mock()
mock_request.registry = {"test": "registry"}

ctx = RequestContext(mock_request)

# Begin should push
ctx.begin()
print("After begin, stack length:", len(manager.stack))

# End should pop
ctx.end()
print("After end, stack length:", len(manager.stack))
print("Stack contents:", manager.stack)

# Now try to get current request
try:
    result = get_current_request()
    print(f"get_current_request() returned: {result}")
except KeyError as e:
    print(f"KeyError raised: {e}")
    print("Manager get() returns:", manager.get())
    print("Stack top item:", manager.stack[-1] if manager.stack else "Empty stack")