import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.encode import urlencode, url_quote, quote_plus

print("Testing space encoding behavior")
print("="*60)

# Test how spaces are encoded
key_with_space = " "
value = ""

print(f"Key: '{key_with_space}', Value: '{value}'")
print(f"url_quote(key): '{url_quote(key_with_space, '')}'")
print(f"quote_plus(key): '{quote_plus(key_with_space, '')}'")

result = urlencode([(key_with_space, value)])
print(f"urlencode result: '{result}'")

# Test with None value
result_none = urlencode([(key_with_space, None)])
print(f"urlencode with None value: '{result_none}'")

print("\nChecking the default quote_via parameter...")
# Look at urlencode signature
import inspect
sig = inspect.signature(urlencode)
print(f"urlencode signature: {sig}")

# The issue is that url_quote converts space to %20
# but urlencode uses quote_plus which converts space to +
# This is correct behavior, my test was wrong