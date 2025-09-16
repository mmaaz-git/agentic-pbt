#!/usr/bin/env python3
"""Reproduce the None/empty string handling bug in optional properties."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.amplify import App, CustomRule

print("Testing None handling for optional properties:")
print()

# Test 1: App with None for optional Description property
print("1. App with Description=None (optional property):")
try:
    app = App('TestApp', Name='Test', Description=None)
    print("  SUCCESS: App created with Description=None")
except TypeError as e:
    print(f"  BUG: {e}")

print()

# Test 2: App without Description property at all
print("2. App without Description property:")
try:
    app = App('TestApp', Name='Test')
    print("  SUCCESS: App created without Description")
except Exception as e:
    print(f"  ERROR: {e}")

print()

# Test 3: CustomRule with empty string for optional Status
print("3. CustomRule with Status='' (empty string for optional property):")
try:
    rule = CustomRule(Source='src', Target='tgt', Status='')
    print("  SUCCESS: CustomRule created with Status=''")
except TypeError as e:
    print(f"  BUG: {e}")

print()

# Test 4: CustomRule with None for optional Status
print("4. CustomRule with Status=None:")
try:
    rule = CustomRule(Source='src', Target='tgt', Status=None)
    print("  SUCCESS: CustomRule created with Status=None")
except TypeError as e:
    print(f"  BUG: {e}")

print()

# Test 5: CustomRule without Status property
print("5. CustomRule without Status property:")
try:
    rule = CustomRule(Source='src', Target='tgt')
    print("  SUCCESS: CustomRule created without Status")
except Exception as e:
    print(f"  ERROR: {e}")