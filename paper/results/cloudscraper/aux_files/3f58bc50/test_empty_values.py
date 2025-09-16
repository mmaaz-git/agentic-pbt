"""Test empty string validation for both browser and platform"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from cloudscraper.user_agent import User_Agent

# Test empty platform
print("Test: Empty platform string")
try:
    ua = User_Agent(browser={'platform': '', 'browser': 'chrome'})
    print(f"BUG CONFIRMED: Empty platform was accepted!")
    print(f"Selected platform: '{ua.platform}'")
    print(f"User-Agent: {ua.headers['User-Agent']}")
except RuntimeError as e:
    print(f"Correctly rejected: {e}")

# Test both empty
print("\nTest: Both browser and platform empty")
try:
    ua = User_Agent(browser={'browser': '', 'platform': ''})
    print(f"BUG CONFIRMED: Both empty strings were accepted!")
    print(f"Selected browser: '{ua.browser}'")
    print(f"Selected platform: '{ua.platform}'")
    print(f"User-Agent: {ua.headers['User-Agent']}")
except RuntimeError as e:
    print(f"Correctly rejected: {e}")