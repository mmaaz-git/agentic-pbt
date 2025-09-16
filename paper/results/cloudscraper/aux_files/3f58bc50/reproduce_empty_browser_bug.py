"""Reproduction script for empty browser name validation bug"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from cloudscraper.user_agent import User_Agent

print("Testing browser name validation...")
print("=" * 50)

# Test 1: Empty string should be invalid
print("\nTest 1: Empty string as browser name")
try:
    ua = User_Agent(browser={'browser': '', 'platform': 'windows'})
    print(f"❌ BUG: Empty browser name was accepted!")
    print(f"   Generated User-Agent: {ua.headers['User-Agent']}")
    print(f"   This violates the documented validation logic")
except RuntimeError as e:
    print(f"✓ Correctly rejected: {e}")

# Test 2: Non-empty invalid name is properly rejected
print("\nTest 2: Invalid browser name 'safari'")
try:
    ua = User_Agent(browser={'browser': 'safari', 'platform': 'windows'})
    print(f"❌ Incorrectly accepted invalid browser 'safari'")
except RuntimeError as e:
    print(f"✓ Correctly rejected: {e}")

# Test 3: Valid browser is accepted
print("\nTest 3: Valid browser name 'chrome'")
try:
    ua = User_Agent(browser={'browser': 'chrome', 'platform': 'windows'})
    print(f"✓ Correctly accepted valid browser 'chrome'")
except RuntimeError as e:
    print(f"❌ Incorrectly rejected: {e}")

print("\n" + "=" * 50)
print("ISSUE: Empty string bypasses browser validation")
print("Expected: RuntimeError for invalid browser names")
print("Actual: Empty string is silently accepted")
print("Root cause: Empty string evaluates to False in Python")
print("            so 'if self.browser' check fails")