#!/usr/bin/env python3
"""Check if common real-world JSONP callbacks would fail."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.renderers as renderers

pattern = renderers.JSONP_VALID_CALLBACK

# Common real-world JSONP callback names
real_callbacks = [
    # Short common names
    "cb",           # Common abbreviation for callback
    "fn",           # Common abbreviation for function
    "f",            # Single letter
    "_",            # Underscore only
    "$",            # jQuery style
    
    # jQuery style
    "jQuery",
    "jQuery123456789",
    "$callback",
    
    # Angular/framework style
    "angular.callbacks._0",
    "jsonp_callback",
    
    # With array/object access
    "window.callback",
    "callbacks[0]",
    "obj.method",
    
    # Numbers at start (should fail)
    "0callback",    # Should fail - starts with number
    "1fn",          # Should fail - starts with number
    
    # Dots at end (should fail)
    "callback.",    # Should fail - ends with dot
    "fn.",          # Should fail - ends with dot
    
    # Valid 3+ character names
    "foo",
    "bar",
    "callback",
    "handleResponse",
    "_cb",
    "$fn",
]

print("Testing real-world JSONP callback names:")
print("=" * 50)

for callback in real_callbacks:
    match = pattern.match(callback)
    status = "✓ VALID" if match else "✗ INVALID"
    print(f"{status:12} | '{callback}'")
    
print("\n" + "=" * 50)
print("\nPROBLEM IDENTIFIED:")
print("The regex requires minimum 3 characters, which rejects common valid JavaScript")
print("callback names like 'cb', 'fn', 'f', '_', '$' that are frequently used in practice.")
print("\nThe pattern: ^[$a-z_][$0-9a-z_\.\[\]]+[^.]$")
print("             ↑        ↑                 ↑")
print("           1 char   1+ chars         1 char  = minimum 3 chars")
print("\nThis seems overly restrictive for legitimate use cases.")