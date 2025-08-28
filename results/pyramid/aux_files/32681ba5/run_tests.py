#!/usr/bin/env python3
"""Run the property-based tests directly."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from test_pyramid_router import *
import traceback

def run_test_class(test_class):
    """Run all test methods in a test class."""
    print(f"\n{'='*60}")
    print(f"Running {test_class.__name__}")
    print('='*60)
    
    for attr_name in dir(test_class):
        if attr_name.startswith('test_'):
            test_method = getattr(test_class, attr_name)
            if callable(test_method):
                print(f"\n  Running {attr_name}...", end=' ')
                try:
                    # Create instance and run test
                    instance = test_class()
                    method = getattr(instance, attr_name)
                    method()
                    print("✓ PASSED")
                except Exception as e:
                    print(f"✗ FAILED")
                    print(f"    Error: {e}")
                    traceback.print_exc()

# Run all test classes
test_classes = [
    TestPathTraversalNormalization,
    TestRoutePatternCompilation,
    TestCallbackOrdering,
    TestPathQuoting,
    TestResourceTreeTraverser,
    TestRoutesMapper
]

for test_class in test_classes:
    run_test_class(test_class)

print("\n" + "="*60)
print("Test run complete!")
print("="*60)