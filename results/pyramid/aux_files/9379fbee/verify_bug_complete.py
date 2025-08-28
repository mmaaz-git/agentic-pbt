import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.threadlocal import manager, get_current_request, get_current_registry

# Test 1: get_current_request() with non-request items on stack
print("Test 1: get_current_request() with non-request items")
manager.clear()
manager.push({"foo": "bar"})  # Push item without 'request' key

try:
    result = get_current_request()
    print(f"  Result: {result}")
except KeyError as e:
    print(f"  BUG: KeyError raised: {e}")
    print(f"  Stack contains: {manager.get()}")

# Test 2: get_current_registry() with non-registry items on stack  
print("\nTest 2: get_current_registry() with non-registry items")
manager.clear()
manager.push({"foo": "bar"})  # Push item without 'registry' key

try:
    result = get_current_registry()
    print(f"  Result: {result}")
except KeyError as e:
    print(f"  BUG: KeyError raised: {e}")
    print(f"  Stack contains: {manager.get()}")

# Test 3: Both functions should handle missing keys gracefully
print("\nTest 3: Empty dict on stack")
manager.clear()
manager.push({})  # Empty dict - no 'request' or 'registry' keys

try:
    req = get_current_request()
    print(f"  get_current_request() returned: {req}")
except KeyError as e:
    print(f"  BUG in get_current_request(): KeyError: {e}")

try:
    reg = get_current_registry()
    print(f"  get_current_registry() returned: {reg}")
except KeyError as e:
    print(f"  BUG in get_current_registry(): KeyError: {e}")

print("\nConclusion: Both functions fail when stack items lack expected keys")