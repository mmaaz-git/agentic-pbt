import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

print("Bug 1: _join_elements expects tuple but documentation doesn't specify this")
print("="*60)

from pyramid.url import _join_elements

# This fails with TypeError: unhashable type: 'list'
try:
    result = _join_elements(['path', 'to', 'resource'])
    print(f"Success: {result}")
except TypeError as e:
    print(f"Error: {e}")
    print("The function uses @lru_cache which requires hashable arguments")
    print("But nowhere in the code is it documented that elements must be a tuple")
    
    # This works:
    result = _join_elements(('path', 'to', 'resource'))
    print(f"Works with tuple: {result}")

print("\n" + "="*60)
print("Bug 2: urlencode crashes on Unicode surrogate characters")
print("="*60)

from pyramid.encode import urlencode

# This fails with UnicodeEncodeError
try:
    # Using chr(0xd800) to create surrogate character
    result = urlencode([(chr(0xd800), 'value')])
    print(f"Success: {result}")
except UnicodeEncodeError as e:
    print(f"Error: {e}")
    print("The function crashes when trying to encode surrogate characters")
    print("Surrogate characters (U+D800-U+DFFF) are not valid UTF-8")

print("\n" + "="*60)
print("Bug 3: parse_url_overrides crashes on surrogate characters in query")
print("="*60)

from pyramid.url import parse_url_overrides

class MockRequest:
    def __init__(self):
        self.application_url = "http://example.com"

request = MockRequest()
kw = {'_query': {chr(0xd800): 'test'}}

try:
    app_url, qs, anchor = parse_url_overrides(request, kw)
    print(f"Success: {app_url}, {qs}, {anchor}")
except UnicodeEncodeError as e:
    print(f"Error: {e}")
    print("parse_url_overrides also crashes on surrogate characters in query dicts")