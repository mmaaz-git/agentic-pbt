#!/usr/bin/env python3
"""Introspect and test cloudscraper properties."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

import cloudscraper
from cloudscraper import CloudScraper, CipherSuiteAdapter
from cloudscraper.user_agent import User_Agent
from cloudscraper.cloudflare import Cloudflare

print("Testing cloudscraper properties...")
print("="*60)

# Test 1: Invalid platform raises error
print("\nTest 1: Invalid platform validation")
try:
    User_Agent(browser={'platform': 'invalid_platform'})
    print("❌ FAILED: Should have raised RuntimeError for invalid platform")
except RuntimeError as e:
    if 'is not valid, valid platforms are' in str(e):
        print("✅ PASSED: Invalid platform correctly raises RuntimeError")
    else:
        print(f"❌ FAILED: Wrong error message: {e}")

# Test 2: Invalid browser raises error
print("\nTest 2: Invalid browser validation")
try:
    User_Agent(browser={'browser': 'invalid_browser'})
    print("❌ FAILED: Should have raised RuntimeError for invalid browser")
except RuntimeError as e:
    if 'browser is not valid, valid browsers are' in str(e):
        print("✅ PASSED: Invalid browser correctly raises RuntimeError")
    else:
        print(f"❌ FAILED: Wrong error message: {e}")

# Test 3: Desktop/mobile constraint
print("\nTest 3: Desktop/mobile constraint")
try:
    User_Agent(browser={'desktop': False, 'mobile': False})
    print("❌ FAILED: Should have raised RuntimeError when both are False")
except RuntimeError as e:
    if "can't have mobile and desktop disabled at the same time" in str(e):
        print("✅ PASSED: Correctly prevents both desktop and mobile being False")
    else:
        print(f"❌ FAILED: Wrong error message: {e}")

# Test 4: Source address string conversion
print("\nTest 4: Source address string conversion")
adapter = CipherSuiteAdapter(source_address="127.0.0.1")
if adapter.source_address == ("127.0.0.1", 0):
    print("✅ PASSED: String source_address correctly converted to tuple")
else:
    print(f"❌ FAILED: Expected ('127.0.0.1', 0), got {adapter.source_address}")

# Test 5: Source address invalid type
print("\nTest 5: Source address invalid type rejection")
try:
    CipherSuiteAdapter(source_address=12345)
    print("❌ FAILED: Should have raised TypeError for integer source_address")
except TypeError as e:
    if "source_address must be IP address string or (ip, port) tuple" in str(e):
        print("✅ PASSED: Invalid source_address type correctly raises TypeError")
    else:
        print(f"❌ FAILED: Wrong error message: {e}")

# Test 6: HTML entity unescaping
print("\nTest 6: HTML entity unescaping")
test_cases = [
    ('&lt;', '<'),
    ('&gt;', '>'),
    ('&amp;', '&'),
    ('&quot;', '"'),
]

all_passed = True
for entity, expected in test_cases:
    result = Cloudflare.unescape(entity)
    if result == expected:
        print(f"  ✅ {entity} -> {result}")
    else:
        print(f"  ❌ {entity} -> {result} (expected {expected})")
        all_passed = False

if all_passed:
    print("✅ PASSED: All HTML entities correctly unescaped")
else:
    print("❌ FAILED: Some HTML entities not correctly unescaped")

# Test 7: CloudScraper initialization
print("\nTest 7: CloudScraper initialization")
scraper = CloudScraper(solveDepth=5)
if scraper.solveDepth == 5 and scraper._solveDepthCnt == 0:
    print("✅ PASSED: CloudScraper correctly initializes solveDepth")
else:
    print(f"❌ FAILED: solveDepth={scraper.solveDepth}, _solveDepthCnt={scraper._solveDepthCnt}")

print("\n" + "="*60)
print("Testing complete!")