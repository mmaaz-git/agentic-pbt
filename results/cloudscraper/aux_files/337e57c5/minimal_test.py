#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

# Simple property tests that can be evaluated statically
import inspect

# Test 1: Check exception hierarchy
from cloudscraper.exceptions import (
    CloudflareException,
    CloudflareLoopProtection,
    CloudflareCode1020,
    CloudflareIUAMError
)

print("Testing exception hierarchy...")
assert issubclass(CloudflareLoopProtection, CloudflareException)
assert issubclass(CloudflareCode1020, CloudflareException)
assert issubclass(CloudflareIUAMError, CloudflareException)
print("✅ Exception hierarchy is correct")

# Test 2: Check module structure
import cloudscraper
print(f"Module version: {cloudscraper.__version__}")
assert hasattr(cloudscraper, 'CloudScraper')
assert hasattr(cloudscraper, 'create_scraper')
print("✅ Module structure is correct")

# Test 3: Check class attributes
from cloudscraper import CipherSuiteAdapter
expected_attrs = ['ssl_context', 'max_retries', 'config']
for attr in expected_attrs:
    assert attr in CipherSuiteAdapter.__attrs__
print("✅ CipherSuiteAdapter has expected attributes")

print("\nAll static property tests passed!")