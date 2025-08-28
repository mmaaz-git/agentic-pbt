#!/usr/bin/env python3
"""
Edge case testing for trino.dbapi to find potential bugs
"""

import sys
import math
from datetime import datetime, date, time as dt_time, timezone, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo
import uuid

sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from trino.dbapi import Cursor, Connection, TimeBoundLRUCache
from unittest.mock import Mock

def test_edge_cases():
    print("Testing edge cases in trino.dbapi")
    print("=" * 60)
    
    bugs_found = []
    
    # Setup cursor for parameter formatting tests
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    # Test 1: Very large integers (beyond 64-bit)
    print("\n[TEST 1] Large integer formatting")
    try:
        # Python supports arbitrary precision integers, but SQL BIGINT is 64-bit
        large_int = 2**63  # Just beyond BIGINT max
        result = cursor._format_prepared_param(large_int)
        print(f"  2^63 = {large_int}")
        print(f"  Formatted as: {result}")
        # Check comment at line 531: "TODO represent numbers exceeding 64-bit (BIGINT) as DECIMAL"
        if "DECIMAL" not in result:
            print("  ⚠ WARNING: Large integer not converted to DECIMAL as TODO suggests")
            print("  This could cause overflow in database")
            bugs_found.append("Large integers beyond 64-bit are not converted to DECIMAL")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
    
    # Test 2: DateTime with nanosecond precision
    print("\n[TEST 2] DateTime with microsecond formatting")
    try:
        # Create datetime with microseconds
        dt = datetime(2024, 1, 1, 12, 0, 0, 123456)
        result = cursor._format_prepared_param(dt)
        print(f"  DateTime: {dt}")
        print(f"  Formatted as: {result}")
        # Check if microseconds are preserved
        if "123456" not in result and "123456000" not in result:
            print("  ✗ BUG: Microseconds lost in formatting")
            bugs_found.append("DateTime microseconds not preserved")
        else:
            print("  ✓ Microseconds preserved")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
    
    # Test 3: Empty collections
    print("\n[TEST 3] Empty collection formatting")
    try:
        empty_list = []
        empty_dict = {}
        empty_tuple = ()
        
        list_result = cursor._format_prepared_param(empty_list)
        dict_result = cursor._format_prepared_param(empty_dict)
        tuple_result = cursor._format_prepared_param(empty_tuple)
        
        print(f"  Empty list: {list_result}")
        print(f"  Empty dict: {dict_result}")
        print(f"  Empty tuple: {tuple_result}")
        
        if list_result != "ARRAY[]":
            print(f"  ✗ BUG: Empty list formatted incorrectly")
            bugs_found.append("Empty list formatting issue")
        if tuple_result != "ROW()":
            print(f"  ✗ BUG: Empty tuple formatted incorrectly")
            bugs_found.append("Empty tuple formatting issue")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
    
    # Test 4: Nested collections
    print("\n[TEST 4] Nested collection formatting")
    try:
        nested_list = [[1, 2], [3, 4]]
        result = cursor._format_prepared_param(nested_list)
        print(f"  Nested list: {nested_list}")
        print(f"  Formatted as: {result}")
        
        # Should be ARRAY[ARRAY[1,2],ARRAY[3,4]]
        if "ARRAY[ARRAY[" not in result:
            print("  ✗ BUG: Nested arrays not formatted correctly")
            bugs_found.append("Nested array formatting issue")
        else:
            print("  ✓ Nested arrays formatted correctly")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
    
    # Test 5: Special string characters
    print("\n[TEST 5] Special string character escaping")
    try:
        # Test various special characters
        test_strings = [
            ("\\n", "newline"),
            ("\\t", "tab"),
            ("\\r", "carriage return"),
            ("\\", "backslash"),
            ("\\'", "backslash quote"),
            ("''", "two single quotes"),
        ]
        
        for test_str, desc in test_strings:
            result = cursor._format_prepared_param(test_str)
            print(f"  {desc}: {repr(test_str)} -> {result}")
            # Only single quotes should be escaped
            if "'" in test_str and test_str != "'":
                expected_quotes = test_str.count("'") * 2 + 2
                actual_quotes = result.count("'")
                if actual_quotes != expected_quotes:
                    print(f"    ✗ BUG: Quote escaping issue")
                    bugs_found.append(f"Quote escaping issue with {repr(test_str)}")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
    
    # Test 6: TimeBoundLRUCache thread safety
    print("\n[TEST 6] LRU Cache with zero/negative TTL")
    try:
        # Test with zero TTL
        cache = TimeBoundLRUCache(capacity=5, ttl_seconds=0)
        cache.put("key", "value")
        result = cache.get("key")
        if result is not None:
            print("  ✗ BUG: Zero TTL should expire immediately")
            bugs_found.append("Zero TTL doesn't expire immediately")
        else:
            print("  ✓ Zero TTL expires immediately")
            
        # Test with negative TTL
        try:
            cache = TimeBoundLRUCache(capacity=5, ttl_seconds=-1)
            cache.put("key", "value")
            result = cache.get("key")
            print("  ⚠ Negative TTL accepted, result:", result)
        except Exception:
            print("  ✓ Negative TTL rejected")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
    
    # Test 7: Decimal edge cases
    print("\n[TEST 7] Decimal edge cases")
    try:
        test_decimals = [
            Decimal("Infinity"),
            Decimal("-Infinity"),
            Decimal("NaN"),
        ]
        
        for dec in test_decimals:
            try:
                result = cursor._format_prepared_param(dec)
                print(f"  {dec} -> {result}")
                # These special values might not be handled
                print(f"  ⚠ Special decimal {dec} formatted as {result}")
            except Exception as e:
                print(f"  Special decimal {dec} raised: {e}")
    except Exception as e:
        print(f"  Note: Special decimals not supported in this Python version")
    
    # Test 8: Time with timezone edge cases
    print("\n[TEST 8] Time with timezone formatting")
    try:
        # Create time with UTC timezone
        utc_tz = timezone.utc
        time_with_tz = dt_time(12, 30, 45, 123456, tzinfo=utc_tz)
        result = cursor._format_prepared_param(time_with_tz)
        print(f"  Time with UTC: {time_with_tz}")
        print(f"  Formatted as: {result}")
        
        # Test with named timezone
        try:
            named_tz = ZoneInfo("America/New_York")
            time_with_named_tz = dt_time(12, 30, 45, 123456, tzinfo=named_tz)
            result2 = cursor._format_prepared_param(time_with_named_tz)
            print(f"  Time with named TZ: {time_with_named_tz}")
            print(f"  Formatted as: {result2}")
        except Exception as e:
            print(f"  Named timezone error: {e}")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
    
    print("\n" + "=" * 60)
    if bugs_found:
        print(f"POTENTIAL ISSUES FOUND: {len(bugs_found)}")
        for bug in bugs_found:
            print(f"  - {bug}")
    else:
        print("No clear bugs found in edge case testing")
    
    return bugs_found

if __name__ == "__main__":
    bugs = test_edge_cases()