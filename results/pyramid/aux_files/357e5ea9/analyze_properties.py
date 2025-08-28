#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.renderers as renderers
import re
import json

print("=== Analyzing Properties from pyramid.renderers ===\n")

# 1. JSONP Callback Validation
print("1. JSONP Callback Validation Pattern:")
print(f"   Pattern: {renderers.JSONP_VALID_CALLBACK.pattern}")
print("   Description: Validates JavaScript callback function names")
print("   Property: Should match valid JS function names and reject invalid ones")
print()

# 2. JSON Renderer
print("2. JSON Renderer:")
json_renderer = renderers.JSON()
print("   - Serializes Python objects to JSON")
print("   - Supports custom adapters for non-JSON-serializable objects")
print("   - Objects with __json__ method are automatically serialized")
print("   Property: Round-trip for JSON-serializable objects")
print("   Property: Custom adapters should be used for registered types")
print()

# 3. JSONP Renderer
print("3. JSONP Renderer:")
print("   - Returns JSONP format when callback parameter is present")
print("   - Falls back to plain JSON when no callback")
print("   - Format: '/**/callback(json_data);'")
print("   Property: Output format must match JSONP specification")
print()

# 4. RendererHelper
print("4. RendererHelper:")
print("   - clone() method should create equivalent instances")
print("   - Property: clone preserves name, package, and registry")
print()

# 5. String Renderer Factory
print("5. String Renderer Factory:")
print("   - Converts any value to string using str()")
print("   - Property: Always returns a string")
print()

print("=== Testing specific patterns ===\n")

# Test some callback patterns
test_callbacks = [
    "$callback",
    "_callback",
    "myFunc",
    "obj.method",
    "arr[0]",
    "func123",
    "jQuery123456",
    "invalid.",  # Should fail - ends with dot
    ".invalid",  # Should fail - starts with dot
    "1invalid",  # Should fail - starts with number
    "",          # Should fail - empty
]

for callback in test_callbacks:
    match = renderers.JSONP_VALID_CALLBACK.match(callback)
    print(f"Callback '{callback}': {'VALID' if match else 'INVALID'}")