from requests.cookies import RequestsCookieJar, create_cookie

jar = RequestsCookieJar()
jar.set('test', '')

# Look at the actual cookie created
for cookie in jar:
    print(f"Cookie name: {cookie.name!r}")
    print(f"Cookie value: {cookie.value!r}")
    print(f"Cookie value truthiness: {bool(cookie.value)}")

# Check what _find_no_duplicates returns
try:
    result = jar._find_no_duplicates('test')
    print(f"\n_find_no_duplicates returns: {result!r}")
except Exception as e:
    print(f"\n_find_no_duplicates raises: {e}")

# Look at the source of _find_no_duplicates behavior
print("\nThe issue is in _find_no_duplicates:")
print("It has 'if toReturn:' which treats empty string as False!")
print("This is the bug - it should be 'if toReturn is not None:'")