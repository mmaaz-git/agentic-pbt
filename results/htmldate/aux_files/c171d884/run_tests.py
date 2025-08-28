#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

import traceback
from hypothesis import given, strategies as st, settings
from test_htmldate_extractors import *

def run_test(test_func, test_name):
    print(f"\nRunning {test_name}...")
    try:
        # Run with more examples to find bugs
        test_with_settings = settings(max_examples=500)(test_func)
        test_with_settings()
        print(f"✅ {test_name} passed")
        return True
    except AssertionError as e:
        print(f"❌ {test_name} FAILED")
        print(f"   Error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ {test_name} CRASHED")
        print(f"   Error: {e}")
        traceback.print_exc()
        return False

# Run all tests
tests = [
    (test_correct_year_invariant, "test_correct_year_invariant"),
    (test_try_swap_values_logic, "test_try_swap_values_logic"),
    (test_trim_text_invariant, "test_trim_text_invariant"),
    (test_url_date_extraction, "test_url_date_extraction"),
    (test_regex_parse_robustness, "test_regex_parse_robustness"),
    (test_custom_parse_iso_format, "test_custom_parse_iso_format"),
    (test_custom_parse_yyyymmdd, "test_custom_parse_yyyymmdd"),
    (test_correct_year_century_boundary, "test_correct_year_century_boundary"),
    (test_try_swap_values_edge_cases, "test_try_swap_values_edge_cases"),
]

results = []
for test_func, test_name in tests:
    results.append(run_test(test_func, test_name))

print("\n" + "="*50)
print("SUMMARY")
print("="*50)
passed = sum(results)
total = len(results)
print(f"Tests passed: {passed}/{total}")

if passed < total:
    print("\n⚠️ Some tests failed. Investigating failures...")
else:
    print("\n✅ All tests passed!")