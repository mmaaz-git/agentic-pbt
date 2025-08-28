from hypothesis import given, strategies as st, assume
from requests.sessions import SessionRedirectMixin


@given(
    old_port=st.integers(min_value=1, max_value=65535),
    new_port=st.integers(min_value=65536, max_value=99999)
)
def test_should_strip_auth_invalid_port_crash(old_port, new_port):
    """Test that should_strip_auth crashes on invalid port numbers"""
    mixin = SessionRedirectMixin()
    
    old_url = f"http://example.com:{old_port}/"
    new_url = f"http://example.com:{new_port}/"  # Invalid port
    
    # This will raise ValueError for invalid ports
    result = mixin.should_strip_auth(old_url, new_url)


if __name__ == "__main__":
    # Run the test - it will fail immediately
    try:
        test_should_strip_auth_invalid_port_crash()
    except ValueError as e:
        print(f"Property test found the bug: {e}")
        print("Failing input: old_port=1, new_port=65536")