"""Testing for edge cases and potential bugs"""
import sys
import re
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from cloudscraper.user_agent import User_Agent

print("Testing edge cases...")

# Test 1: Empty string browser name
print("\n=== Test 1: Empty string browser name ===")
try:
    ua = User_Agent(browser={'browser': '', 'platform': 'windows'})
    print(f"Unexpectedly succeeded with empty browser name!")
    print(f"User-Agent: {ua.headers.get('User-Agent')}")
except RuntimeError as e:
    print(f"Correctly raised RuntimeError: {e}")
except Exception as e:
    print(f"Unexpected error: {type(e).__name__}: {e}")

# Test 2: Platform with mixed case
print("\n=== Test 2: Platform with mixed case ===")
try:
    ua = User_Agent(browser={'platform': 'Linux'})  # Should be 'linux'
    print(f"Unexpectedly succeeded with 'Linux' (mixed case)")
    print(f"User-Agent: {ua.headers.get('User-Agent')}")
except RuntimeError as e:
    print(f"Correctly raised RuntimeError: {e}")
except Exception as e:
    print(f"Unexpected error: {type(e).__name__}: {e}")

# Test 3: Browser with mixed case  
print("\n=== Test 3: Browser with mixed case ===")
try:
    ua = User_Agent(browser={'browser': 'Chrome', 'platform': 'windows'})  # Should be 'chrome'
    print(f"Unexpectedly succeeded with 'Chrome' (mixed case)")
    print(f"User-Agent: {ua.headers.get('User-Agent')}")
except RuntimeError as e:
    print(f"Correctly raised RuntimeError: {e}")
except Exception as e:
    print(f"Unexpected error: {type(e).__name__}: {e}")

# Test 4: Platform=None with browser specified
print("\n=== Test 4: Platform=None with browser specified ===")
try:
    ua = User_Agent(browser={'browser': 'chrome', 'platform': None})
    print(f"Succeeded with platform=None")
    print(f"User-Agent: {ua.headers.get('User-Agent')}")
    print(f"Selected platform: {ua.platform}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# Test 5: Custom user agent that doesn't match any pattern
print("\n=== Test 5: Custom user agent that doesn't match ===")
try:
    ua = User_Agent(custom="MyCustomBot/1.0")
    print(f"Custom UA succeeded")
    print(f"User-Agent: {ua.headers.get('User-Agent')}")
    print(f"Accept-Encoding: {ua.headers.get('Accept-Encoding')}")
    # Check if br is removed when allow_brotli=False (default)
    if 'br' in ua.headers.get('Accept-Encoding', ''):
        print("BUG: Custom UA has 'br' in Accept-Encoding even with allow_brotli=False (default)")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# Test 6: Custom user agent with allow_brotli=False
print("\n=== Test 6: Custom user agent with allow_brotli=False ===")
try:
    ua = User_Agent(custom="MyCustomBot/1.0", allow_brotli=False)
    encoding = ua.headers.get('Accept-Encoding', '')
    print(f"Accept-Encoding: {encoding}")
    if 'br' in encoding:
        print("BUG FOUND: Custom UA has 'br' in Accept-Encoding despite allow_brotli=False")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# Test 7: Browser name with special regex characters
print("\n=== Test 7: Browser with special regex characters ===")
special_chars = ['[', ']', '(', ')', '.', '*', '+', '?', '{', '}', '|', '^', '$', '\\']
for char in special_chars:
    browser_name = f"test{char}browser"
    try:
        ua = User_Agent(browser={'browser': browser_name, 'platform': 'windows'})
        print(f"Unexpectedly succeeded with browser name containing '{char}'")
    except RuntimeError as e:
        # Check if the error message is properly escaped
        error_str = str(e)
        if char in ['[', ']', '(', ')', '.', '*', '+', '?', '{', '}', '|', '^', '$', '\\']:
            # These characters have special meaning in regex
            if re.search(re.escape(browser_name), error_str):
                # Good - the character is in the error message
                pass
            else:
                print(f"Potential issue: Special char '{char}' may cause regex problems in error message")
    except Exception as e:
        print(f"Unexpected error with '{char}': {type(e).__name__}: {e}")

# Test 8: Platform filtering accuracy
print("\n=== Test 8: Platform filtering (android should be mobile only) ===")
ua = User_Agent(browser={'platform': 'android', 'desktop': False, 'mobile': True})
user_agent = ua.headers.get('User-Agent', '')
if 'Android' not in user_agent:
    print(f"BUG: Android platform selected but User-Agent doesn't contain 'Android': {user_agent}")
else:
    print("Android platform correctly generates Android User-Agent")

# Test 9: iOS platform
print("\n=== Test 9: iOS platform filtering ===")
ua = User_Agent(browser={'platform': 'ios', 'desktop': False, 'mobile': True})
user_agent = ua.headers.get('User-Agent', '')
if 'iPhone' not in user_agent and 'iPad' not in user_agent:
    print(f"BUG: iOS platform selected but User-Agent doesn't contain iPhone/iPad: {user_agent}")
else:
    print("iOS platform correctly generates iOS User-Agent")

# Test 10: Inconsistent mobile/desktop combinations
print("\n=== Test 10: Desktop platform with mobile-only setting ===")
try:
    # Windows is typically desktop, but requesting mobile only
    ua = User_Agent(browser={'platform': 'windows', 'desktop': False, 'mobile': True})
    user_agent = ua.headers.get('User-Agent', '')
    print(f"User-Agent for windows with mobile-only: {user_agent}")
    # This might not have any mobile Windows browsers, check if it fails gracefully
except Exception as e:
    print(f"Error (expected if no mobile Windows browsers): {e}")