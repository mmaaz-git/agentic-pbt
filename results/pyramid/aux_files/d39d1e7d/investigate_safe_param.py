import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.encode import url_quote
from urllib.parse import quote

# Test case from hypothesis
text = '\x80'
safe = '\x80'

print(f"Testing: text='{repr(text)}', safe='{repr(safe)}'")

# Test pyramid's url_quote
result = url_quote(text, safe=safe)
print(f"pyramid url_quote('{repr(text)}', safe='{repr(safe)}') = '{result}'")

# Check if the character appears in the result
print(f"Character '\\x80' in result: {'\x80' in result}")
print(f"Result bytes: {result.encode('utf-8')}")

# Compare with standard library
std_result = quote(text.encode('utf-8'), safe=safe)
print(f"stdlib quote('{repr(text)}'.encode('utf-8'), safe='{repr(safe)}') = '{std_result}'")

# Let's trace through what pyramid does
print("\nTracing pyramid's url_quote logic:")
cls = text.__class__
print(f"  cls = {cls}")
if cls is str:
    val = text.encode('utf-8')
    print(f"  Encoding to UTF-8: {repr(val)}")
    
# Now it calls _url_quote from urllib.parse
from urllib.parse import quote as _url_quote
final = _url_quote(val, safe=safe)
print(f"  Calling _url_quote({repr(val)}, safe='{repr(safe)}') = '{final}'")

# Check what happens with safe as bytes
print("\nTrying with safe as bytes:")
safe_bytes = safe.encode('utf-8')
result2 = _url_quote(val, safe=safe_bytes)
print(f"  _url_quote({repr(val)}, safe={repr(safe_bytes)}) = '{result2}'")