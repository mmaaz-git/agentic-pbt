from requests.sessions import SessionRedirectMixin

# Minimal reproduction of the bug
mixin = SessionRedirectMixin()

# A malformed URL with invalid port can crash should_strip_auth
old_url = "http://example.com/"
new_url = "http://example.com:70000/"  # Invalid port > 65535

try:
    result = mixin.should_strip_auth(old_url, new_url)
    print(f"Result: {result}")
except ValueError as e:
    print(f"CRASH: {e}")
    print("\nThis is a bug because:")
    print("1. should_strip_auth is meant to handle redirects")
    print("2. A server could send a malformed Location header with invalid port")
    print("3. The function should handle this gracefully, not crash")