#!/usr/bin/env python3
"""Property-based test demonstrating the None vs False bug in challenge detection."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
from cloudscraper.cloudflare import Cloudflare


class MockResponse:
    """Minimal mock HTTP response for testing."""
    def __init__(self, headers=None, status_code=200, text=''):
        self.headers = headers or {}
        self.status_code = status_code
        self.text = text


# Property: All is_* methods should return boolean values (True or False), never None
@given(
    server_header=st.one_of(
        st.none(),
        st.sampled_from(['cloudflare', 'nginx', 'apache', 'cloudflare-nginx', ''])
    ),
    status_code=st.sampled_from([200, 403, 429, 503, 404, 500]),
    text_content=st.sampled_from(['', 'some text', '/cdn-cgi/images/trace/jsch/', '<form>'])
)
@settings(max_examples=500)
def test_challenge_methods_return_booleans(server_header, status_code, text_content):
    """Test that all is_* challenge detection methods return boolean values."""
    
    headers = {}
    if server_header is not None:
        headers['Server'] = server_header
    
    resp = MockResponse(headers=headers, status_code=status_code, text=text_content)
    
    # Test is_IUAM_Challenge
    result1 = Cloudflare.is_IUAM_Challenge(resp)
    assert isinstance(result1, bool), \
        f"is_IUAM_Challenge returned {type(result1).__name__} ({result1!r}) instead of bool for " \
        f"Server={server_header}, status={status_code}"
    
    # Test is_Captcha_Challenge
    result2 = Cloudflare.is_Captcha_Challenge(resp)
    assert isinstance(result2, bool), \
        f"is_Captcha_Challenge returned {type(result2).__name__} ({result2!r}) instead of bool for " \
        f"Server={server_header}, status={status_code}"
    
    # Test is_Firewall_Blocked
    result3 = Cloudflare.is_Firewall_Blocked(resp)
    assert isinstance(result3, bool), \
        f"is_Firewall_Blocked returned {type(result3).__name__} ({result3!r}) instead of bool for " \
        f"Server={server_header}, status={status_code}"


# Specific test for the bug cases
def test_specific_bug_cases():
    """Test the specific cases where None is returned instead of False."""
    
    # Bug case 1: is_IUAM_Challenge with cloudflare + 503 but no matching text
    resp1 = MockResponse(
        headers={'Server': 'cloudflare'},
        status_code=503,
        text='no matching patterns here'
    )
    result1 = Cloudflare.is_IUAM_Challenge(resp1)
    assert result1 is not None, f"is_IUAM_Challenge returned None for partial match"
    
    # Bug case 2: is_IUAM_Challenge with cloudflare + 429
    resp2 = MockResponse(
        headers={'Server': 'cloudflare'},
        status_code=429,
        text='no matching patterns'
    )
    result2 = Cloudflare.is_IUAM_Challenge(resp2)
    assert result2 is not None, f"is_IUAM_Challenge returned None for cloudflare+429"
    
    # Bug case 3: is_Captcha_Challenge with cloudflare + 403
    resp3 = MockResponse(
        headers={'Server': 'cloudflare'},
        status_code=403,
        text='no matching patterns'
    )
    result3 = Cloudflare.is_Captcha_Challenge(resp3)
    assert result3 is not None, f"is_Captcha_Challenge returned None for cloudflare+403"
    
    # Bug case 4: is_Firewall_Blocked with cloudflare + 403
    resp4 = MockResponse(
        headers={'Server': 'cloudflare'},
        status_code=403,
        text='no error code here'
    )
    result4 = Cloudflare.is_Firewall_Blocked(resp4)
    assert result4 is not None, f"is_Firewall_Blocked returned None for cloudflare+403"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])