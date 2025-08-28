#!/usr/bin/env python3
"""
Comprehensive test for trino.dbapi to find bugs
"""

import sys
import os
import math
import time
from decimal import Decimal
from datetime import datetime, date, time as dt_time
import traceback

# Add trino to path
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

def run_tests():
    print("=" * 60)
    print("Testing trino.dbapi for bugs")
    print("=" * 60)
    
    from trino.dbapi import TimeBoundLRUCache, Cursor, Connection, DBAPITypeObject
    from unittest.mock import Mock
    
    # Test 1: TimeBoundLRUCache - Check if capacity is strictly enforced
    print("\n[TEST 1] TimeBoundLRUCache capacity enforcement")
    try:
        cache = TimeBoundLRUCache(capacity=3, ttl_seconds=3600)
        
        # Add 4 items to a cache with capacity 3
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        cache.put("key4", "value4")  # This should evict key1
        
        # Check cache size
        actual_size = len(cache.cache)
        if actual_size > 3:
            print(f"  ✗ BUG FOUND: Cache size {actual_size} exceeds capacity 3")
        else:
            print(f"  ✓ Cache capacity correctly enforced: {actual_size} <= 3")
            
        # Check if first key was evicted
        if cache.get("key1") is not None:
            print(f"  ✗ BUG FOUND: key1 should have been evicted but is still present")
        else:
            print(f"  ✓ LRU eviction working correctly")
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        traceback.print_exc()
    
    # Test 2: Format prepared param - bytes formatting case
    print("\n[TEST 2] Bytes formatting case sensitivity")
    try:
        mock_connection = Mock(spec=Connection)
        cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
        
        test_bytes = bytes([0xAB, 0xCD, 0xEF])
        result = cursor._format_prepared_param(test_bytes)
        
        # Check format
        expected_lower = "X'abcdef'"
        expected_upper = "X'ABCDEF'"
        
        if result == expected_lower:
            print(f"  ⚠ POTENTIAL ISSUE: Bytes formatted as lowercase hex: {result}")
            print(f"    Some SQL engines may expect uppercase hex literals")
        elif result == expected_upper:
            print(f"  ✓ Bytes formatted as uppercase hex: {result}")
        else:
            print(f"  ✗ BUG FOUND: Unexpected format: {result}")
            
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        traceback.print_exc()
    
    # Test 3: Format prepared param - special float values
    print("\n[TEST 3] Special float value formatting")
    try:
        mock_connection = Mock(spec=Connection)
        cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
        
        test_cases = [
            (float('inf'), "infinity()"),
            (float('-inf'), "-infinity()"),
            (float('nan'), "nan()"),
        ]
        
        for value, expected in test_cases:
            result = cursor._format_prepared_param(value)
            if result != expected:
                print(f"  ✗ BUG FOUND: {value} formatted as '{result}', expected '{expected}'")
            else:
                print(f"  ✓ {value} correctly formatted as '{result}'")
                
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        traceback.print_exc()
    
    # Test 4: String escaping with single quotes
    print("\n[TEST 4] String escaping with quotes")
    try:
        mock_connection = Mock(spec=Connection)
        cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
        
        test_strings = [
            ("simple", "'simple'"),
            ("it's", "'it''s'"),  # Single quote should be doubled
            ("'quoted'", "'''quoted'''"),  # Multiple quotes
            ("", "''"),  # Empty string
            ("'", "''''"),  # Just a single quote
        ]
        
        for test_str, expected in test_strings:
            result = cursor._format_prepared_param(test_str)
            if result != expected:
                print(f"  ✗ BUG FOUND: '{test_str}' formatted as {result}, expected {expected}")
            else:
                print(f"  ✓ '{test_str}' correctly escaped")
                
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        traceback.print_exc()
    
    # Test 5: DBAPITypeObject case insensitivity
    print("\n[TEST 5] DBAPITypeObject case insensitive comparison")
    try:
        type_obj = DBAPITypeObject("VARCHAR", "CHAR", "TEXT")
        
        test_cases = [
            ("varchar", True),
            ("VARCHAR", True),
            ("VarChar", True),
            ("CHAR", True),
            ("char", True),
            ("text", True),
            ("INTEGER", False),
            ("", False),
        ]
        
        for test_val, should_match in test_cases:
            matches = (type_obj == test_val)
            if matches != should_match:
                print(f"  ✗ BUG FOUND: '{test_val}' match={matches}, expected={should_match}")
            else:
                print(f"  ✓ '{test_val}' comparison correct")
                
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        traceback.print_exc()
    
    # Test 6: Connection URL parsing
    print("\n[TEST 6] Connection URL parsing and port inference")
    try:
        test_cases = [
            ("https://example.com", "https", 443),
            ("http://example.com", "http", 8080),
            ("https://example.com:9999", "https", 9999),
            ("example.com", "http", 8080),  # No scheme defaults to http
        ]
        
        for host, expected_scheme, expected_port in test_cases:
            try:
                conn = Connection(host=host, user="test")
                if conn.http_scheme != expected_scheme:
                    print(f"  ✗ BUG: {host} -> scheme={conn.http_scheme}, expected={expected_scheme}")
                elif conn.port != expected_port:
                    print(f"  ✗ BUG: {host} -> port={conn.port}, expected={expected_port}")
                else:
                    print(f"  ✓ {host} correctly parsed")
                conn.close()
            except Exception as e:
                print(f"  ✗ ERROR parsing {host}: {e}")
                
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        traceback.print_exc()
    
    # Test 7: Decimal formatting
    print("\n[TEST 7] Decimal value formatting")
    try:
        mock_connection = Mock(spec=Connection)
        cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
        
        test_cases = [
            Decimal("123.456"),
            Decimal("0.1"),
            Decimal("-999.999"),
            Decimal("0"),
            Decimal("1e10"),
        ]
        
        for dec_val in test_cases:
            result = cursor._format_prepared_param(dec_val)
            if not result.startswith("DECIMAL '"):
                print(f"  ✗ BUG: {dec_val} doesn't start with DECIMAL '")
            elif not result.endswith("'"):
                print(f"  ✗ BUG: {dec_val} doesn't end with '")
            else:
                # Extract the decimal string
                decimal_str = result[9:-1]
                # Check if it's a valid decimal representation
                try:
                    reconstructed = Decimal(decimal_str)
                    # Decimal representations might differ slightly
                    print(f"  ✓ {dec_val} formatted correctly as {result}")
                except:
                    print(f"  ✗ BUG: Invalid decimal format in {result}")
                    
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        traceback.print_exc()
        
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()