import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.urldispatch as urldispatch

# Test different patterns
test_patterns = ['foo', '0', 'api/test', '{id}', 'users/{id}']

for pattern in test_patterns:
    print(f"\n=== Testing pattern: {pattern!r} ===")
    
    # Create route
    route = urldispatch.Route('test', pattern)
    print(f"route.pattern = {route.pattern!r} (stored value)")
    print(f"route.path = {route.path!r} (alias)")
    
    # The matcher is created by _compile_route
    # Let's see what it actually matches
    test_paths = [pattern, '/' + pattern, '//' + pattern]
    for path in test_paths:
        result = route.match(path)
        if result is not None:
            print(f"  route.match({path!r}) = {result}")
    
    # Also test generate
    try:
        generated = route.generate({})
        print(f"  route.generate({{}}) = {generated!r}")
    except Exception as e:
        print(f"  route.generate({{}}) raised: {e}")

print("\n=== Analysis ===")
print("The bug: Route.pattern stores the original pattern without normalization")
print("But _compile_route internally adds '/' prefix for matching")
print("This causes Route.pattern to be inconsistent with what the route actually matches")