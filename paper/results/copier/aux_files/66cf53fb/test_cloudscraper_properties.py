#!/usr/bin/env python3
"""Property-based tests for cloudscraper library using Hypothesis."""

import sys
import os
import re

sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest
import cloudscraper
from cloudscraper import CloudScraper, CipherSuiteAdapter
from cloudscraper.user_agent import User_Agent  
from cloudscraper.cloudflare import Cloudflare


# Test 1: User_Agent platform validation property
@given(st.text(min_size=1))
def test_user_agent_invalid_platform_raises_error(platform):
    """Invalid platforms should raise RuntimeError."""
    valid_platforms = ['linux', 'windows', 'darwin', 'android', 'ios']
    assume(platform not in valid_platforms)
    
    with pytest.raises(RuntimeError) as exc:
        User_Agent(browser={'platform': platform})
    
    assert 'is not valid, valid platforms are' in str(exc.value)


# Test 2: User_Agent browser validation property
@given(st.text(min_size=1))
def test_user_agent_invalid_browser_raises_error(browser):
    """Invalid browsers should raise RuntimeError."""
    valid_browsers = ['chrome', 'firefox']
    assume(browser not in valid_browsers)
    
    with pytest.raises(RuntimeError) as exc:
        User_Agent(browser={'browser': browser})
    
    assert 'browser is not valid, valid browsers are' in str(exc.value)


# Test 3: User_Agent desktop/mobile constraint
@given(st.booleans(), st.booleans())
def test_user_agent_desktop_mobile_constraint(desktop, mobile):
    """Cannot have both desktop and mobile disabled."""
    if not desktop and not mobile:
        with pytest.raises(RuntimeError) as exc:
            User_Agent(browser={'desktop': desktop, 'mobile': mobile})
        assert "can't have mobile and desktop disabled at the same time" in str(exc.value)
    else:
        # Should not raise when at least one is True
        ua = User_Agent(browser={'desktop': desktop, 'mobile': mobile})
        assert ua is not None


# Test 4: CipherSuiteAdapter source_address type validation
@given(st.one_of(
    st.text(min_size=1),
    st.tuples(st.text(), st.integers(min_value=0, max_value=65535)),
    st.integers(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text())
))
def test_cipher_suite_adapter_source_address_validation(source_address):
    """source_address must be string or (ip, port) tuple."""
    adapter = None
    
    if isinstance(source_address, str):
        # String should be converted to tuple
        adapter = CipherSuiteAdapter(source_address=source_address)
        assert adapter.source_address == (source_address, 0)
    elif isinstance(source_address, tuple) and len(source_address) == 2:
        # Valid tuple should be accepted
        adapter = CipherSuiteAdapter(source_address=source_address)
        assert adapter.source_address == source_address
    else:
        # Everything else should raise TypeError
        with pytest.raises(TypeError) as exc:
            CipherSuiteAdapter(source_address=source_address)
        assert "source_address must be IP address string or (ip, port) tuple" in str(exc.value)


# Test 5: Cloudflare.unescape HTML entity handling
@given(st.text())
def test_cloudflare_unescape_preserves_non_entities(text):
    """Text without HTML entities should be preserved."""
    # Avoid text that contains HTML entities
    assume('&' not in text or not re.search(r'&[a-zA-Z]+;|&#\d+;|&#x[0-9a-fA-F]+;', text))
    
    result = Cloudflare.unescape(text)
    assert result == text


# Test 6: Cloudflare.unescape handles common HTML entities
@given(st.sampled_from([
    ('&lt;', '<'),
    ('&gt;', '>'),
    ('&amp;', '&'),
    ('&quot;', '"'),
    ('&#39;', "'"),
    ('&#x27;', "'"),
    ('&#x2F;', '/'),
]))
def test_cloudflare_unescape_common_entities(entity_pair):
    """Common HTML entities should be properly unescaped."""
    entity, expected = entity_pair
    result = Cloudflare.unescape(entity)
    assert result == expected


# Test 7: CloudScraper solveDepth protection
@given(st.integers(min_value=0, max_value=10))
def test_cloudscraper_solve_depth_initialization(depth):
    """solveDepth should be properly initialized."""
    scraper = CloudScraper(solveDepth=depth)
    assert scraper.solveDepth == depth
    assert scraper._solveDepthCnt == 0


# Test 8: CloudScraper headers Accept-Encoding with allow_brotli
@given(st.booleans())
def test_user_agent_brotli_encoding(allow_brotli):
    """Accept-Encoding should reflect allow_brotli setting."""
    ua = User_Agent(allow_brotli=allow_brotli)
    
    if ua.headers and 'Accept-Encoding' in ua.headers:
        encodings = ua.headers['Accept-Encoding']
        
        if not allow_brotli:
            # br should not be in Accept-Encoding when allow_brotli is False
            assert 'br' not in encodings.split(',')
        # Note: we can't assert br IS there when allow_brotli=True because
        # it depends on the randomly selected user agent


# Test 9: CloudScraper session attributes inheritance
@given(
    st.dictionaries(st.text(min_size=1), st.text()),
    st.dictionaries(st.text(min_size=1), st.text())
)
def test_cloudscraper_create_scraper_inherits_session_attrs(headers, params):
    """create_scraper should inherit session attributes."""
    import requests
    sess = requests.Session()
    sess.headers.update(headers)
    sess.params = params
    
    scraper = CloudScraper.create_scraper(sess=sess)
    
    # Headers should be inherited
    for key, value in headers.items():
        assert scraper.headers.get(key) == value
    
    # Params should be inherited
    assert scraper.params == params


# Test 10: Exception hierarchy validation
def test_exception_hierarchy():
    """All Cloudflare exceptions should inherit from CloudflareException."""
    from cloudscraper.exceptions import (
        CloudflareException,
        CloudflareLoopProtection,
        CloudflareCode1020,
        CloudflareIUAMError,
        CloudflareChallengeError,
        CloudflareSolveError,
        CloudflareCaptchaError,
        CloudflareCaptchaProvider
    )
    
    exceptions = [
        CloudflareLoopProtection,
        CloudflareCode1020,
        CloudflareIUAMError,
        CloudflareChallengeError,
        CloudflareSolveError,
        CloudflareCaptchaError,
        CloudflareCaptchaProvider
    ]
    
    for exc_class in exceptions:
        assert issubclass(exc_class, CloudflareException)


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    pytest.main([__file__, '-v', '--tb=short'])