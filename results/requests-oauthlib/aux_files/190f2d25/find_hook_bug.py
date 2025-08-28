#!/usr/bin/env python3
"""Demonstrate a bug in OAuth2Session compliance hook registration."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/requests-oauthlib_env/lib/python3.13/site-packages')

from requests_oauthlib import OAuth2Session

print("=== Testing Compliance Hook Registration Bug ===\n")

# Looking at the register_compliance_hook method (lines 570-587):
# It adds hooks to a set without validating if they're callable

print("Creating OAuth2Session...")
session = OAuth2Session(client_id="test_client")

print("\nTest 1: Registering None as a hook...")
try:
    # This should fail but might not
    session.register_compliance_hook("protected_request", None)
    
    if None in session.compliance_hook["protected_request"]:
        print("✗ BUG FOUND: None was accepted as a valid hook!")
        print("  This will cause TypeError when hooks are invoked")
        print("\n  When the code tries to call the hook:")
        print("    for hook in self.compliance_hook['protected_request']:")
        print("        url, headers, data = hook(url, headers, data)")
        print("  It will fail with: TypeError: 'NoneType' object is not callable")
    else:
        print("✓ None was somehow not added to the set")
except Exception as e:
    print(f"✓ Good: None was rejected with error: {e}")

print("\nTest 2: Registering a non-callable object...")
try:
    # Try to register a string (non-callable)
    session.register_compliance_hook("protected_request", "not_a_function")
    
    if "not_a_function" in session.compliance_hook["protected_request"]:
        print("✗ BUG FOUND: Non-callable string was accepted as a hook!")
        print("  This will cause TypeError when hooks are invoked")
except Exception as e:
    print(f"✓ Good: Non-callable was rejected with error: {e}")

print("\nTest 3: Registering an integer...")
try:
    session.register_compliance_hook("protected_request", 42)
    
    if 42 in session.compliance_hook["protected_request"]:
        print("✗ BUG FOUND: Integer was accepted as a hook!")
        print("  This will cause TypeError when hooks are invoked")
except Exception as e:
    print(f"✓ Good: Integer was rejected with error: {e}")

print("\nTest 4: Registering a dict...")
try:
    test_dict = {"key": "value"}
    session.register_compliance_hook("protected_request", test_dict)
    
    if test_dict in session.compliance_hook["protected_request"]:
        print("✗ BUG FOUND: Dict was accepted as a hook!")
        print("  This will cause TypeError when hooks are invoked")
except Exception as e:
    print(f"✓ Good: Dict was rejected with error: {e}")

print("\n" + "="*50)
print("\nAnalysis of the bug:")
print("-" * 20)

print("""
The register_compliance_hook method (lines 570-587) does not validate
that the hook parameter is callable before adding it to the set.

The method simply does:
    self.compliance_hook[hook_type].add(hook)

Without checking:
    if not callable(hook):
        raise TypeError("Hook must be callable")

This means non-callable objects (None, strings, numbers, etc.) can be
registered as hooks. When these hooks are later invoked in the code,
it will cause a TypeError at runtime.

For example, in the request method (lines 522-524):
    for hook in self.compliance_hook["protected_request"]:
        log.debug("Invoking hook %s.", hook)
        url, headers, data = hook(url, headers, data)

If hook is None or any non-callable, this will crash with:
    TypeError: 'NoneType' object is not callable

This is a legitimate bug that violates the principle of fail-fast -
errors should be caught at registration time, not at invocation time.
""")