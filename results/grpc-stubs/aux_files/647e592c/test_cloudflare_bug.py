#!/usr/bin/env python3
"""Test to demonstrate the None vs False bug in challenge detection methods."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from cloudscraper.cloudflare import Cloudflare


class MockResponse:
    """Minimal mock HTTP response for testing."""
    def __init__(self, headers=None, status_code=200, text=''):
        self.headers = headers or {}
        self.status_code = status_code
        self.text = text


def test_is_IUAM_Challenge_return_value():
    """Test that is_IUAM_Challenge always returns a boolean, never None."""
    
    # Test case 1: Cloudflare server, correct status code, but no matching text patterns
    # This triggers the bug where None is returned instead of False
    resp = MockResponse(
        headers={'Server': 'cloudflare'},
        status_code=503,
        text='some text without the required patterns'
    )
    
    result = Cloudflare.is_IUAM_Challenge(resp)
    print(f"Test 1 - Partial match (cloudflare + 503):")
    print(f"  Result: {result}")
    print(f"  Type: {type(result)}")
    print(f"  Expected: False (boolean)")
    print(f"  Bug: Returns {result} instead of False\n")
    
    # Demonstrate the bug affects boolean logic
    if result is False:
        print("  Comparison with False: result is False = True")
    else:
        print("  Comparison with False: result is False = False")
    
    if result == False:
        print("  Comparison with False: result == False = True")
    else:
        print("  Comparison with False: result == False = False")
    
    if not result:
        print("  Boolean evaluation: not result = True")
    else:
        print("  Boolean evaluation: not result = False")
    
    print("\n  Problem: None and False are both falsy, but they are different values.")
    print("  This can cause issues in code that specifically checks for False.")
    
    # Test case 2: Similar bug in is_Captcha_Challenge
    resp2 = MockResponse(
        headers={'Server': 'cloudflare'},
        status_code=403,
        text='some text without the required patterns'
    )
    
    result2 = Cloudflare.is_Captcha_Challenge(resp2)
    print(f"\nTest 2 - is_Captcha_Challenge with partial match:")
    print(f"  Result: {result2}")
    print(f"  Type: {type(result2)}")
    print(f"  Expected: False (boolean)")
    print(f"  Bug: Returns {result2} instead of False")
    
    # Test case 3: is_Firewall_Blocked has the same issue
    resp3 = MockResponse(
        headers={'Server': 'cloudflare'},
        status_code=403,
        text='some text without error code'
    )
    
    result3 = Cloudflare.is_Firewall_Blocked(resp3)
    print(f"\nTest 3 - is_Firewall_Blocked with partial match:")
    print(f"  Result: {result3}")
    print(f"  Type: {type(result3)}")
    print(f"  Expected: False (boolean)")
    print(f"  Bug: Returns {result3} instead of False")
    
    return result, result2, result3


def test_all_challenge_methods_consistency():
    """Test that all challenge detection methods consistently return booleans."""
    
    test_responses = [
        MockResponse(),  # Empty response
        MockResponse(headers={'Server': 'cloudflare'}),  # Just cloudflare header
        MockResponse(headers={'Server': 'cloudflare'}, status_code=503),  # Header + status
        MockResponse(headers={'Server': 'cloudflare'}, status_code=403),  # Header + different status
        MockResponse(headers={'Server': 'cloudflare'}, status_code=429),  # Header + another status
        MockResponse(text='/cdn-cgi/images/trace/jsch/'),  # Just text pattern
        MockResponse(headers={'Server': 'nginx'}),  # Non-cloudflare server
    ]
    
    methods = [
        ('is_IUAM_Challenge', Cloudflare.is_IUAM_Challenge),
        ('is_Captcha_Challenge', Cloudflare.is_Captcha_Challenge),
        ('is_Firewall_Blocked', Cloudflare.is_Firewall_Blocked),
    ]
    
    print("\nConsistency check - all methods should return boolean True or False:")
    print("-" * 60)
    
    bugs_found = []
    for i, resp in enumerate(test_responses, 1):
        print(f"\nResponse {i}: Server={resp.headers.get('Server', 'None')}, "
              f"Status={resp.status_code}, Has text={bool(resp.text)}")
        
        for method_name, method_func in methods:
            result = method_func(resp)
            is_bool = isinstance(result, bool)
            print(f"  {method_name:20} -> {result!r:6} (bool: {is_bool})")
            
            if not is_bool:
                bugs_found.append((i, method_name, result))
    
    if bugs_found:
        print("\n" + "=" * 60)
        print("BUGS FOUND:")
        for resp_num, method, result in bugs_found:
            print(f"  Response {resp_num}, {method} returned {result!r} instead of boolean")
    
    return bugs_found


if __name__ == "__main__":
    print("Testing Cloudflare challenge detection methods for None vs False bug")
    print("=" * 70)
    
    # Run the specific bug demonstration
    test_is_IUAM_Challenge_return_value()
    
    print("\n" + "=" * 70)
    
    # Run consistency check
    bugs = test_all_challenge_methods_consistency()
    
    print("\n" + "=" * 70)
    print("SUMMARY:")
    if bugs:
        print(f"Found {len(bugs)} cases where None is returned instead of False")
        print("This is a bug because these functions should always return boolean values.")
        print("\nWhy this matters:")
        print("1. API inconsistency - functions named 'is_*' should return booleans")
        print("2. Explicit False checks (x is False) will fail when None is returned")
        print("3. Type hints would be incorrect if they specify '-> bool'")
    else:
        print("No bugs found - all methods consistently return boolean values")