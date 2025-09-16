import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from pyramid.threadlocal import RequestContext, get_current_request, manager

print("Initial manager stack:", manager.stack)

# Create a mock request
mock_request = Mock()
mock_request.registry = {"test": "registry"}

# Use RequestContext with explicit begin/end
ctx = RequestContext(mock_request)

print("Before begin, stack:", manager.stack)

# Begin pushes to stack
ctx.begin()
print("After begin, stack:", manager.stack)

# End pops from stack
ctx.end()
print("After end, stack:", manager.stack)

# This should return None but raises KeyError instead
try:
    result = get_current_request()
    print(f"get_current_request() returned: {result}")
except KeyError as e:
    print(f"KeyError raised: {e}")
    print("Manager get() returns:", manager.get())