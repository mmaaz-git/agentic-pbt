#!/usr/bin/env python3
"""Run the property-based tests for limits.typing"""

import sys
import traceback

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

def run_test(test_func, test_name):
    """Run a single test function and report results"""
    try:
        test_func()
        print(f"✓ {test_name} passed")
        return True
    except AssertionError as e:
        print(f"✗ {test_name} FAILED")
        print(f"  AssertionError: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ {test_name} ERROR")
        print(f"  {type(e).__name__}: {e}")
        traceback.print_exc()
        return False

# Import the test module
import test_limits_typing

# List of test functions to run
tests = [
    (test_limits_typing.test_all_exports_are_defined, "test_all_exports_are_defined"),
    (test_limits_typing.test_all_exports_can_be_imported, "test_all_exports_can_be_imported"),
    (test_limits_typing.test_serializable_type_components, "test_serializable_type_components"),
    (test_limits_typing.test_protocol_classes_are_protocols, "test_protocol_classes_are_protocols"),
    (test_limits_typing.test_type_variables_exist, "test_type_variables_exist"),
    (test_limits_typing.test_counter_is_collections_counter, "test_counter_is_collections_counter"),
    (test_limits_typing.test_reexported_typing_items, "test_reexported_typing_items"),
]

# Run property test separately with Hypothesis
def run_hypothesis_test():
    """Run the hypothesis property test"""
    from hypothesis import given, strategies as st
    import limits.typing
    
    print("\nRunning Hypothesis property test...")
    failures = []
    
    # Test each export
    for export_name in limits.typing.__all__:
        try:
            # Call the actual test function with the export name
            assert hasattr(limits.typing, export_name), f"{export_name} not found in module"
            attr = getattr(limits.typing, export_name)
            if export_name not in ['Any', 'TYPE_CHECKING']:
                assert attr is not None, f"Export '{export_name}' is unexpectedly None"
        except Exception as e:
            failures.append((export_name, e))
    
    if failures:
        print(f"✗ Hypothesis test FAILED for {len(failures)} exports")
        for name, error in failures[:5]:  # Show first 5 failures
            print(f"  - {name}: {error}")
        return False
    else:
        print(f"✓ Hypothesis test passed for all {len(limits.typing.__all__)} exports")
        return True

# Run all tests
print("Running property-based tests for limits.typing...")
print("=" * 60)

all_passed = True
for test_func, test_name in tests:
    passed = run_test(test_func, test_name)
    all_passed = all_passed and passed
    print()

# Run Hypothesis test
hypothesis_passed = run_hypothesis_test()
all_passed = all_passed and hypothesis_passed

print("=" * 60)
if all_passed:
    print("✓ All tests PASSED!")
else:
    print("✗ Some tests FAILED!")
    sys.exit(1)