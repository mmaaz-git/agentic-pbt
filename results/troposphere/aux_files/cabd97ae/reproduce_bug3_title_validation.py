#!/usr/bin/env python3
"""Minimal reproduction for title validation bug."""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

import troposphere.accessanalyzer as aa

# Bug: Title validation rejects valid Unicode letters
# The Greek letter µ (mu) is a valid letter but is rejected

print("Testing with Unicode letter 'µ' (Greek letter mu)...")
try:
    analyzer = aa.Analyzer(title="µ", Type="ACCOUNT")
    print("Success - created analyzer with title 'µ'")
except ValueError as e:
    print(f"Failed with error: {e}")

print("\nTesting with other Unicode letters...")
test_chars = ["α", "β", "γ", "π", "λ", "Ω", "中", "日", "한"]
for char in test_chars:
    try:
        analyzer = aa.Analyzer(title=char, Type="ACCOUNT")
        print(f"Success - created analyzer with title '{char}'")
    except ValueError as e:
        print(f"Failed for '{char}': {e}")

print("\nThe regex used is: ^[a-zA-Z0-9]+$")
print("This only accepts ASCII letters and digits, not Unicode letters.")