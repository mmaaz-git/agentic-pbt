"""Simplified property tests to investigate failures"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from cloudscraper.user_agent import User_Agent

# Test 1: Simple test with default parameters
print("Test 1: Creating User_Agent with default parameters")
try:
    ua = User_Agent()
    print(f"Success! Headers: {ua.headers}")
    print(f"Accept-Encoding: {ua.headers.get('Accept-Encoding')}")
except Exception as e:
    print(f"Failed: {e}")

# Test 2: Test with allow_brotli=False
print("\nTest 2: Creating User_Agent with allow_brotli=False")
try:
    ua = User_Agent(allow_brotli=False)
    encoding = ua.headers.get('Accept-Encoding', '')
    print(f"Accept-Encoding: {encoding}")
    print(f"Contains 'br': {'br' in encoding}")
except Exception as e:
    print(f"Failed: {e}")

# Test 3: Test with allow_brotli=True
print("\nTest 3: Creating User_Agent with allow_brotli=True")
try:
    ua = User_Agent(allow_brotli=True)
    encoding = ua.headers.get('Accept-Encoding', '')
    print(f"Accept-Encoding: {encoding}")
    print(f"Contains 'br': {'br' in encoding}")
except Exception as e:
    print(f"Failed: {e}")

# Test 4: Test with specific browser and platform
print("\nTest 4: Creating User_Agent with chrome on windows")
try:
    ua = User_Agent(browser={'browser': 'chrome', 'platform': 'windows'})
    print(f"User-Agent: {ua.headers.get('User-Agent')}")
except Exception as e:
    print(f"Failed: {e}")

# Test 5: Test with mobile only
print("\nTest 5: Creating User_Agent with mobile only")
try:
    ua = User_Agent(browser={'desktop': False, 'mobile': True, 'platform': 'android'})
    print(f"User-Agent: {ua.headers.get('User-Agent')}")
except Exception as e:
    print(f"Failed: {e}")

# Test 6: Test with desktop only
print("\nTest 6: Creating User_Agent with desktop only")
try:
    ua = User_Agent(browser={'desktop': True, 'mobile': False, 'platform': 'windows'})
    print(f"User-Agent: {ua.headers.get('User-Agent')}")
except Exception as e:
    print(f"Failed: {e}")

# Test 7: Test multiple calls with different allow_brotli values
print("\nTest 7: Testing multiple instances with different allow_brotli")
for i in range(5):
    for allow_brotli in [True, False]:
        ua = User_Agent(allow_brotli=allow_brotli)
        encoding = ua.headers.get('Accept-Encoding', '')
        has_br = 'br' in encoding
        expected = allow_brotli
        if has_br != expected:
            print(f"BUG FOUND! allow_brotli={allow_brotli}, but 'br' in encoding = {has_br}")
            print(f"  Full Accept-Encoding: {encoding}")
            print(f"  Headers: {ua.headers}")
            break