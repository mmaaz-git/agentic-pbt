#!/usr/bin/env python3
"""Investigate the bugs found in azure.core."""

from azure.core.utils import parse_connection_string, CaseInsensitiveDict

print("=== Bug 1: parse_connection_string strips non-breaking space ===")
# The key '\xa00' (non-breaking space + '0') is incorrectly modified
key_with_nbsp = '\xa00'
conn_str = f"{key_with_nbsp}=value"
print(f"Original key: repr={repr(key_with_nbsp)}")
print(f"Connection string: {repr(conn_str)}")

result = parse_connection_string(conn_str, case_sensitive_keys=True)
print(f"Parsed keys: {list(result.keys())}")
print(f"Expected key: {repr(key_with_nbsp)}")
print(f"Actual key: {repr(list(result.keys())[0])}")
print(f"Keys match: {list(result.keys())[0] == key_with_nbsp}")
print()

print("=== Bug 2: parse_connection_string duplicate detection with spaces ===")
# Keys that differ only in leading/trailing spaces aren't detected as duplicates
conn_str = " A=value1;a=value2"
print(f"Connection string: {repr(conn_str)}")
try:
    result = parse_connection_string(conn_str, case_sensitive_keys=False)
    print(f"No error raised! Result: {dict(result)}")
except ValueError as e:
    print(f"ValueError raised: {e}")
print()

print("=== Bug 3: CaseInsensitiveDict fails with Unicode case folding ===")
# The micro sign 'µ' uppercases to Greek capital Mu 'Μ', causing issues
ci_dict = CaseInsensitiveDict({'µ': 'micro'})
print(f"Original key: 'µ'")
print(f"'µ'.upper() = {repr('µ'.upper())}")
print(f"'µ'.lower() = {repr('µ'.lower())}")

print(f"ci_dict['µ'] = {ci_dict.get('µ')}")
print(f"ci_dict['Μ'] (uppercase) = {ci_dict.get('Μ')}")
print(f"ci_dict['μ'] (lowercase Greek mu) = {ci_dict.get('μ')}")
print()

print("=== Bug 4: German ß case handling ===")
# German sharp s 'ß' uppercases to 'SS'
ci_dict = CaseInsensitiveDict()
ci_dict['ß'] = 'lower'
ci_dict['SS'] = 'upper'
ci_dict['Ss'] = 'title'

print(f"'ß'.upper() = {repr('ß'.upper())}")
print(f"'ß'.lower() = {repr('ß'.lower())}")
print(f"Dict keys: {list(ci_dict.keys())}")
print(f"Dict length: {len(ci_dict)} (expected 1)")
print()

print("=== Root cause analysis ===")
print("The issues stem from:")
print("1. parse_connection_string strips keys (.strip() called on split results)")
print("2. CaseInsensitiveDict uses .lower() for normalization, which doesn't handle Unicode case folding properly")
print("3. Python's .lower() and .upper() don't always round-trip for Unicode characters")