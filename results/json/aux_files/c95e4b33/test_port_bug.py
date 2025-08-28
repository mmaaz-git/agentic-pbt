from requests.sessions import SessionRedirectMixin

# Test the bug: should_strip_auth crashes when port is at boundary (65535) and we add 1
mixin = SessionRedirectMixin()

# This should work
old_url = "http://example.com:65535/"
new_url = "http://example.com:65535/"
try:
    result = mixin.should_strip_auth(old_url, new_url)
    print(f"Same port 65535: should_strip = {result}")
except Exception as e:
    print(f"Error with same port: {e}")

# This will crash when comparing ports
old_url = "http://example.com:65535/"
new_url = "http://example.com:65536/"  # Invalid port, but requests doesn't validate before parsing
try:
    result = mixin.should_strip_auth(old_url, new_url)
    print(f"Different ports (65535 -> 65536): should_strip = {result}")
except ValueError as e:
    print(f"ValueError when port out of range: {e}")
    print("BUG: should_strip_auth crashes on invalid port numbers in new_url")

# Further test: what if both are invalid?
old_url = "http://example.com:99999/"
new_url = "http://example.com:99999/"
try:
    result = mixin.should_strip_auth(old_url, new_url)
    print(f"Both invalid ports: should_strip = {result}")
except ValueError as e:
    print(f"ValueError with both invalid: {e}")