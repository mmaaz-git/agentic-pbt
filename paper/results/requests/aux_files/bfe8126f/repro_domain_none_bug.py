from requests.cookies import RequestsCookieJar

# Bug 2: AttributeError when setting cookie with explicit domain=None
jar = RequestsCookieJar()

try:
    # This should work - domain=None should mean "no specific domain"
    jar.set('test', 'value', domain=None, path=None)
    print("Success: Cookie set with domain=None")
except AttributeError as e:
    print(f"AttributeError: {e}")
    print("Bug: create_cookie() tries to call .startswith() on None domain")