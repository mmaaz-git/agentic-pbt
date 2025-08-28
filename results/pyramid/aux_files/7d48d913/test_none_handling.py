import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.encode import urlencode

print("Testing None value handling in urlencode")
print("="*60)

# Test single None value
result = urlencode([('key', None)])
print(f"Single None: '{result}'")
assert result == 'key=', f"Expected 'key=' but got '{result}'"

# Test multiple None values
result = urlencode([('a', None), ('b', None)])
print(f"Multiple None: '{result}'")
assert result == 'a=&b=', f"Expected 'a=&b=' but got '{result}'"

# Test mixed None and regular values
result = urlencode([('a', 'value'), ('b', None), ('c', 'test')])
print(f"Mixed: '{result}'")
assert result == 'a=value&b=&c=test', f"Expected 'a=value&b=&c=test' but got '{result}'"

print("\nAll tests passed! None handling works correctly.")