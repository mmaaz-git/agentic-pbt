#!/usr/bin/env python3
"""Minimal reproduction of route compilation bug with regex special characters"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

# Create resolver
resolver = ApiGatewayResolver()

# Test 1: Route with question mark fails
try:
    route = "/test?query=value"
    compiled = resolver._compile_regex(route)
    print(f"✓ Successfully compiled route: {route}")
except Exception as e:
    print(f"✗ Failed to compile route '/test?query=value'")
    print(f"  Error: {e}")

# Test 2: Route with brackets fails
try:
    route = "/test[id]/path"
    compiled = resolver._compile_regex(route)
    print(f"✓ Successfully compiled route: {route}")
except Exception as e:
    print(f"✗ Failed to compile route '/test[id]/path'")
    print(f"  Error: {e}")

# Test 3: Route with parentheses fails
try:
    route = "/test(v1)/path"
    compiled = resolver._compile_regex(route)
    print(f"✓ Successfully compiled route: {route}")
except Exception as e:
    print(f"✗ Failed to compile route '/test(v1)/path'")
    print(f"  Error: {e}")

# Test 4: Route with dollar sign fails
try:
    route = "/test$/path"
    compiled = resolver._compile_regex(route)
    print(f"✓ Successfully compiled route: {route}")
except Exception as e:
    print(f"✗ Failed to compile route '/test$/path'")
    print(f"  Error: {e}")

print("\n--- Even if compilation succeeds, matching fails ---")

# Test 5: Even when compilation succeeds, matching fails
route = "/test?/end"
compiled = resolver._compile_regex(route)
test_path = "/test?/end"
match = compiled.match(test_path)

if match:
    print(f"✓ Route '{route}' matched path '{test_path}'")
else:
    print(f"✗ Route '{route}' failed to match identical path '{test_path}'")
    print(f"  This is a bug: the route should match its own pattern!")