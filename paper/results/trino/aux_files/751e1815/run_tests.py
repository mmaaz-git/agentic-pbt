#!/usr/bin/env python3

import sys
import traceback
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from test_trino_dbapi import *

print("=" * 60)
print("Running Property-Based Tests for trino.dbapi")
print("=" * 60)

test_functions = [
    (test_lru_cache_capacity_constraint, "LRU Cache Capacity Constraint"),
    (test_lru_cache_ttl_expiration, "LRU Cache TTL Expiration"),
    (test_lru_cache_eviction_order, "LRU Cache Eviction Order"),
    (test_format_prepared_param_special_floats, "Format Special Float Values"),
    (test_format_prepared_param_string_escaping, "Format String Escaping"),
    (test_format_prepared_param_bytes, "Format Bytes"),
    (test_format_prepared_param_list, "Format List"),
    (test_format_prepared_param_dict, "Format Dictionary"),
    (test_format_prepared_param_decimal, "Format Decimal"),
    (test_dbapi_type_object_case_insensitive, "DBAPITypeObject Case Insensitive"),
    (test_format_prepared_param_date, "Format Date"),
    (test_format_prepared_param_time_without_tz, "Format Time without TZ"),
    (test_format_prepared_param_bool, "Format Boolean"),
    (test_format_prepared_param_int, "Format Integer"),
    (test_format_prepared_param_none, "Format None"),
    (test_format_prepared_param_uuid, "Format UUID"),
    (test_format_prepared_param_tuple, "Format Tuple"),
    (test_connection_url_parsing, "Connection URL Parsing"),
]

passed = 0
failed = 0
errors = []

for test_func, test_name in test_functions:
    try:
        print(f"\nTesting: {test_name}...", end=" ")
        test_func()
        print("✓ PASSED")
        passed += 1
    except AssertionError as e:
        print(f"✗ FAILED")
        print(f"  Failure: {e}")
        failed += 1
        errors.append((test_name, e, None))
    except Exception as e:
        print(f"✗ ERROR")
        print(f"  Error: {e}")
        tb = traceback.format_exc()
        failed += 1
        errors.append((test_name, e, tb))

print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")

if errors:
    print("\n" + "=" * 60)
    print("DETAILED FAILURES:")
    for test_name, error, tb in errors:
        print(f"\n{test_name}:")
        print(f"  {error}")
        if tb:
            print(f"  Traceback:\n{tb}")

print("=" * 60)