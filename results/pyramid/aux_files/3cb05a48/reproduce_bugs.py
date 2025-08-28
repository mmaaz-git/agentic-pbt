#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.request import Request
from pyramid.url import parse_url_overrides
import urllib.parse

print("Bug 1: IPv6 addresses are mangled in _partial_application_url")
print("=" * 60)

request = Request.blank('/')
request.environ['wsgi.url_scheme'] = 'http'
request.environ['SERVER_NAME'] = 'default.com'
request.environ['SERVER_PORT'] = '80'

# Test case 1: Plain IPv6 address
ipv6 = '::1'
port = '8080'
url = request._partial_application_url(host=ipv6, port=port)
print(f"Input: host='{ipv6}', port='{port}'")
print(f"Expected: 'http://[::1]:8080' or similar")
print(f"Got: '{url}'")
print()

# Test case 2: Bracketed IPv6 address
ipv6_bracketed = '[::1]'
port = '8080'
url = request._partial_application_url(host=ipv6_bracketed, port=port)
print(f"Input: host='{ipv6_bracketed}', port='{port}'")
print(f"Expected: 'http://[::1]:8080'")
print(f"Got: '{url}'")
print()

print("\nBug 2: Query parameters with spaces as keys are lost")
print("=" * 60)

request = Request.blank('/')
kw = {'_query': {' ': 'value'}}  # Space as key
app_url, qs, frag = parse_url_overrides(request, kw)
print(f"Input query dict: {{' ': 'value'}}")
print(f"Generated query string: '{qs}'")
print(f"Parsing back the query string:")
parsed = urllib.parse.parse_qs(qs[1:] if qs else '')
print(f"Parsed: {parsed}")
print(f"Key ' ' is missing!")
print()

# More test cases
kw = {'_query': {'key with spaces': 'value'}}
app_url, qs, frag = parse_url_overrides(request, kw)
print(f"Input query dict: {{'key with spaces': 'value'}}")
print(f"Generated query string: '{qs}'")
parsed = urllib.parse.parse_qs(qs[1:] if qs else '')
print(f"Parsed: {parsed}")
print()

print("\nBug 3: Empty host causes invalid URLs")
print("=" * 60)

request = Request.blank('/')
request.environ['wsgi.url_scheme'] = 'http'
request.environ['SERVER_NAME'] = 'default.com'
request.environ['SERVER_PORT'] = '80'
del request.environ['HTTP_HOST']  # Remove HTTP_HOST

# Test with empty host
try:
    url = request._partial_application_url(host='', port='8080')
    print(f"Input: host='', port='8080'")
    print(f"Generated URL: '{url}'")
    print(f"This creates an invalid URL with just ':8080'")
except Exception as e:
    print(f"Exception: {e}")