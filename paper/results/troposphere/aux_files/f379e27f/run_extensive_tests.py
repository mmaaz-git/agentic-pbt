#!/usr/bin/env python3
"""Run extensive property-based tests with more examples."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import settings
from test_oam_properties import *

# Run each test with more examples
print("Running extensive property-based tests for troposphere.oam...")
print("Testing with 1000 examples per test...")
print("=" * 60)

tests = [
    ("test_linkfilter_round_trip", test_linkfilter_round_trip),
    ("test_linkconfiguration_round_trip", test_linkconfiguration_round_trip),
    ("test_link_round_trip", test_link_round_trip),
    ("test_sink_round_trip", test_sink_round_trip),
    ("test_link_with_configuration_round_trip", test_link_with_configuration_round_trip),
    ("test_link_equality", test_link_equality),
]

passed = 0
failed = 0

for test_name, test_func in tests:
    print(f"\nTesting {test_name}...")
    try:
        # Create a new test with more examples
        test_with_settings = settings(max_examples=1000)(test_func)
        test_with_settings()
        print(f"✓ {test_name} passed with 1000 examples")
        passed += 1
    except Exception as e:
        print(f"✗ {test_name} failed: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

print("\n" + "=" * 60)
print(f"Results: {passed} passed, {failed} failed")

if failed == 0:
    print("\n✅ All property-based tests passed with extensive testing!")
else:
    print(f"\n❌ {failed} test(s) failed")