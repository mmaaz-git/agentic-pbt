#!/usr/bin/env python3
"""Minimal reproduction of bugs found in copier._tools."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

import copier._tools as tools

print("=" * 60)
print("Bug 1: normalize_git_path fails with non-UTF8 byte")
print("-" * 60)
try:
    path = '\x80'
    print(f"Input: {repr(path)}")
    result = tools.normalize_git_path(path)
    print(f"Result: {repr(result)}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("Bug 2: normalize_git_path fails with trailing backslash")
print("-" * 60)
try:
    path = '\\'
    print(f"Input: {repr(path)}")
    result = tools.normalize_git_path(path)
    print(f"Result: {repr(result)}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("Bug 3: escape_git_path is not idempotent")
print("-" * 60)
path = '#'
print(f"Original: {repr(path)}")
escaped1 = tools.escape_git_path(path)
print(f"Escaped once: {repr(escaped1)}")
escaped2 = tools.escape_git_path(escaped1)
print(f"Escaped twice: {repr(escaped2)}")
print(f"Are they equal? {escaped1 == escaped2}")

print("\n" + "=" * 60)
print("Bug 4: Another case - Unicode character causing issues")
print("-" * 60)
path = 'Ā'  # Unicode character U+0100
print(f"Original: {repr(path)}")
escaped = tools.escape_git_path(path)
print(f"Escaped: {repr(escaped)}")
normalized = tools.normalize_git_path(escaped)
print(f"Normalized after escape: {repr(normalized)}")
re_escaped = tools.escape_git_path(normalized)
print(f"Re-escaped: {repr(re_escaped)}")
print(f"Are escaped and re-escaped equal? {escaped == re_escaped}")