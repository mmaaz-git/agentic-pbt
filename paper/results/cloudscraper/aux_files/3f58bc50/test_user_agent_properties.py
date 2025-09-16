"""Property-based tests for cloudscraper.user_agent module"""
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

# Import the User_Agent class directly
from cloudscraper.user_agent import User_Agent


# Property 1: Both desktop and mobile False should raise RuntimeError
@given(
    platform=st.sampled_from(['linux', 'windows', 'darwin', 'android', 'ios']),
    browser=st.sampled_from(['chrome', 'firefox', None])
)
def test_desktop_and_mobile_both_false_raises_error(platform, browser):
    """Test that having both desktop and mobile disabled raises RuntimeError"""
    with pytest.raises(RuntimeError, match="can't have mobile and desktop disabled"):
        User_Agent(browser={'desktop': False, 'mobile': False, 'platform': platform, 'browser': browser})


# Property 2: Invalid browser names should raise RuntimeError
@given(
    invalid_browser=st.text(min_size=1, max_size=50).filter(lambda x: x not in ['chrome', 'firefox'] and x.strip()),
    platform=st.sampled_from(['linux', 'windows', 'darwin', 'android', 'ios'])
)
def test_invalid_browser_raises_error(invalid_browser, platform):
    """Test that invalid browser names raise RuntimeError"""
    with pytest.raises(RuntimeError, match=f'Sorry "{invalid_browser}" browser is not valid'):
        User_Agent(browser={'browser': invalid_browser, 'platform': platform})


# Property 3: Invalid platform names should raise RuntimeError  
@given(
    invalid_platform=st.text(min_size=1, max_size=50).filter(
        lambda x: x not in ['linux', 'windows', 'darwin', 'android', 'ios'] and x.strip()
    ),
    browser=st.sampled_from(['chrome', 'firefox', None])
)
def test_invalid_platform_raises_error(invalid_platform, browser):
    """Test that invalid platform names raise RuntimeError"""
    with pytest.raises(RuntimeError, match=f'Sorry the platform "{invalid_platform}" is not valid'):
        User_Agent(browser={'platform': invalid_platform, 'browser': browser})


# Property 4: Accept-Encoding should not contain 'br' when allow_brotli=False
@given(
    platform=st.sampled_from(['linux', 'windows', 'darwin', 'android', 'ios']),
    browser=st.sampled_from(['chrome', 'firefox', None]),
    desktop=st.booleans(),
    mobile=st.booleans()
)
def test_brotli_encoding_removed_when_disabled(platform, browser, desktop, mobile):
    """Test that 'br' is removed from Accept-Encoding when allow_brotli=False"""
    # Skip invalid combinations
    assume(desktop or mobile)  # At least one must be True
    
    # Create user agent with allow_brotli=False (default)
    ua = User_Agent(
        browser={'platform': platform, 'browser': browser, 'desktop': desktop, 'mobile': mobile},
        allow_brotli=False
    )
    
    # Check that 'br' is not in Accept-Encoding
    assert 'br' not in ua.headers['Accept-Encoding']
    
    # Also verify that the encoding string is properly formatted (no extra commas/spaces)
    encoding = ua.headers['Accept-Encoding']
    assert not encoding.startswith(',')
    assert not encoding.endswith(',')
    assert '  ' not in encoding  # No double spaces
    assert ', ,' not in encoding  # No empty items


# Property 5: Accept-Encoding should contain 'br' when allow_brotli=True
@given(
    platform=st.sampled_from(['linux', 'windows', 'darwin', 'android', 'ios']),
    browser=st.sampled_from(['chrome', 'firefox', None]),
    desktop=st.booleans(),
    mobile=st.booleans()
)
def test_brotli_encoding_present_when_enabled(platform, browser, desktop, mobile):
    """Test that 'br' is kept in Accept-Encoding when allow_brotli=True"""
    # Skip invalid combinations
    assume(desktop or mobile)  # At least one must be True
    
    # Create user agent with allow_brotli=True
    ua = User_Agent(
        browser={'platform': platform, 'browser': browser, 'desktop': desktop, 'mobile': mobile},
        allow_brotli=True
    )
    
    # Check that 'br' is in Accept-Encoding
    assert 'br' in ua.headers['Accept-Encoding']


# Property 6: Valid configurations should always produce valid headers
@given(
    platform=st.sampled_from(['linux', 'windows', 'darwin', 'android', 'ios']),
    browser=st.sampled_from(['chrome', 'firefox', None]),
    desktop=st.booleans(),
    mobile=st.booleans(),
    allow_brotli=st.booleans()
)
def test_valid_configs_produce_valid_headers(platform, browser, desktop, mobile, allow_brotli):
    """Test that valid configurations always produce proper headers"""
    # Skip invalid combinations
    assume(desktop or mobile)  # At least one must be True
    
    # Create user agent
    ua = User_Agent(
        browser={'platform': platform, 'browser': browser, 'desktop': desktop, 'mobile': mobile},
        allow_brotli=allow_brotli
    )
    
    # Verify headers exist and are non-empty
    assert ua.headers is not None
    assert 'User-Agent' in ua.headers
    assert ua.headers['User-Agent']  # Non-empty
    assert 'Accept' in ua.headers
    assert 'Accept-Language' in ua.headers
    assert 'Accept-Encoding' in ua.headers
    
    # Verify cipherSuite exists
    assert ua.cipherSuite is not None
    assert isinstance(ua.cipherSuite, list)
    assert len(ua.cipherSuite) > 0


# Property 7: filterAgents method behavior
@given(
    desktop=st.booleans(),
    mobile=st.booleans(),
    platform=st.sampled_from(['linux', 'windows', 'darwin', 'android', 'ios'])
)
def test_filter_agents_returns_correct_subset(desktop, mobile, platform):
    """Test that filterAgents returns appropriate subset based on settings"""
    import json
    
    # Load the browsers.json to simulate user_agents structure
    with open('/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages/cloudscraper/user_agent/browsers.json', 'r') as fp:
        user_agents = json.load(fp)
    
    # Create a User_Agent instance to access filterAgents
    assume(desktop or mobile)  # Need at least one
    ua = User_Agent(browser={'desktop': desktop, 'mobile': mobile, 'platform': platform})
    
    # Test the filterAgents method directly
    ua.desktop = desktop
    ua.mobile = mobile  
    ua.platform = platform
    filtered = ua.filterAgents(user_agents)
    
    # Verify that filtered results match the settings
    if filtered:  # If there are results
        for browser_name in filtered:
            # The filtered results should only come from requested categories
            found_in_desktop = False
            found_in_mobile = False
            
            if 'desktop' in user_agents['user_agents'] and platform in user_agents['user_agents']['desktop']:
                if browser_name in user_agents['user_agents']['desktop'][platform]:
                    found_in_desktop = True
                    
            if 'mobile' in user_agents['user_agents'] and platform in user_agents['user_agents']['mobile']:
                if browser_name in user_agents['user_agents']['mobile'][platform]:
                    found_in_mobile = True
            
            # Verify the browser was found in appropriate category
            if desktop and not mobile:
                assert found_in_desktop and not found_in_mobile
            elif mobile and not desktop:
                assert found_in_mobile and not found_in_desktop
            # If both are enabled, it could be from either