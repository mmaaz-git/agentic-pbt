import requests
from unittest.mock import Mock, patch

# Test if this can happen during actual redirect handling
session = requests.Session()

# Mock a response with invalid port in Location header
mock_response = Mock()
mock_response.is_redirect = True
mock_response.status_code = 302
mock_response.headers = {'Location': 'http://example.com:99999/path'}
mock_response.url = 'http://example.com/original'
mock_response.request = Mock()
mock_response.request.url = 'http://example.com/original'
mock_response.raw = Mock()
mock_response.content = b''
mock_response.history = []

mock_request = Mock()
mock_request.url = 'http://example.com/original'
mock_request.copy = Mock(return_value=Mock())

# Try to resolve redirects - this should trigger should_strip_auth
try:
    # This is what happens internally during redirect resolution
    redirect_url = mock_response.headers['Location']
    
    # Session will try to check if auth should be stripped
    should_strip = session.should_strip_auth(
        mock_response.request.url, 
        redirect_url
    )
    print(f"Should strip auth: {should_strip}")
except ValueError as e:
    print(f"BUG CONFIRMED: ValueError during redirect handling: {e}")
    print("\nImpact: A malicious or misconfigured server sending invalid")
    print("port numbers in Location headers will crash the client")