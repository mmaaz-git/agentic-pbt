#!/usr/bin/env python3
"""Bug reproduction: is_ipv4_address crashes on null character"""

import requests.utils

# Test case 1: Direct null character
try:
    result = requests.utils.is_ipv4_address('\x00')
    print(f"Result for '\\x00': {result}")
except ValueError as e:
    print(f"ERROR: is_ipv4_address('\\x00') raised ValueError: {e}")

# Test case 2: Null character in middle of string  
try:
    result = requests.utils.is_ipv4_address('192.168\x00.1.1')
    print(f"Result for '192.168\\x00.1.1': {result}")
except ValueError as e:
    print(f"ERROR: is_ipv4_address('192.168\\x00.1.1') raised ValueError: {e}")

# Show how this could happen in practice
from urllib.parse import urlparse

url = 'http://example.com\x00.evil.com/path'
parsed = urlparse(url)
print(f"\nPractical example:")
print(f"URL: {url!r}")
print(f"Parsed hostname: {parsed.hostname!r}")

# This would crash in should_bypass_proxies
try:
    if parsed.hostname:
        result = requests.utils.is_ipv4_address(parsed.hostname)
        print(f"is_ipv4_address(parsed.hostname) = {result}")
except ValueError as e:
    print(f"ERROR: is_ipv4_address(parsed.hostname) raised ValueError: {e}")
    print("This would crash should_bypass_proxies() function!")