import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.urldispatch as urldispatch

# Test case from Hypothesis
pattern = '0'
route = urldispatch.Route('test', pattern)

print(f"Input pattern: {pattern!r}")
print(f"Route pattern: {route.pattern!r}")
print(f"Route path: {route.path!r}")

# The pattern should start with '/' according to the code (line 130-131)
# But it doesn't!

# Let's also check what happens with the internal _compile_route function
matcher, generator = urldispatch._compile_route(pattern)
print(f"\nAfter _compile_route:")
print(f"Pattern was internally processed")

# Check if it matches anything
test_paths = ['0', '/0', '//0']
for path in test_paths:
    result = matcher(path)
    print(f"matcher({path!r}) = {result}")