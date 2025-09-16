#!/usr/bin/env python3
"""Run property-based tests for cloudscraper."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

import traceback
from hypothesis import given, strategies as st, assume, settings

import cloudscraper
from cloudscraper import CloudScraper, CipherSuiteAdapter
from cloudscraper.user_agent import User_Agent  
from cloudscraper.cloudflare import Cloudflare


def run_test(test_name, test_func):
    """Run a single test and report results."""
    print(f"\n{'='*60}")
    print(f"Running: {test_name}")
    print('='*60)
    
    try:
        test_func()
        print(f"✅ PASSED: {test_name}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {test_name}")
        print(f"Error: {e}")
        traceback.print_exc()
        return False


# Test 1: Invalid platform handling
@given(st.text(min_size=1))
@settings(max_examples=100)
def test_invalid_platform(platform):
    valid_platforms = ['linux', 'windows', 'darwin', 'android', 'ios']
    assume(platform not in valid_platforms)
    
    try:
        User_Agent(browser={'platform': platform})
        raise AssertionError(f"Expected RuntimeError for invalid platform '{platform}'")
    except RuntimeError as e:
        assert 'is not valid, valid platforms are' in str(e)


# Test 2: Source address validation
@given(st.one_of(
    st.text(min_size=1),
    st.tuples(st.text(), st.integers(min_value=0, max_value=65535)),
    st.integers(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text())
))
@settings(max_examples=100)
def test_source_address(source_address):
    if isinstance(source_address, str):
        adapter = CipherSuiteAdapter(source_address=source_address)
        assert adapter.source_address == (source_address, 0)
    elif isinstance(source_address, tuple) and len(source_address) == 2:
        adapter = CipherSuiteAdapter(source_address=source_address)
        assert adapter.source_address == source_address
    else:
        try:
            CipherSuiteAdapter(source_address=source_address)
            raise AssertionError(f"Expected TypeError for invalid source_address type: {type(source_address)}")
        except TypeError as e:
            assert "source_address must be IP address string or (ip, port) tuple" in str(e)


# Test 3: HTML entity unescaping
@given(st.sampled_from([
    ('&lt;', '<'),
    ('&gt;', '>'),
    ('&amp;', '&'),
    ('&quot;', '"'),
    ('&#39;', "'"),
    ('&#x27;', "'"),
    ('&#x2F;', '/'),
]))
@settings(max_examples=50)
def test_html_unescape(entity_pair):
    entity, expected = entity_pair
    result = Cloudflare.unescape(entity)
    assert result == expected, f"Failed to unescape {entity}: got {result}, expected {expected}"


# Test 4: Desktop/mobile constraint
@given(st.booleans(), st.booleans())
@settings(max_examples=50)
def test_desktop_mobile(desktop, mobile):
    if not desktop and not mobile:
        try:
            User_Agent(browser={'desktop': desktop, 'mobile': mobile})
            raise AssertionError("Expected RuntimeError when both desktop and mobile are False")
        except RuntimeError as e:
            assert "can't have mobile and desktop disabled at the same time" in str(e)
    else:
        ua = User_Agent(browser={'desktop': desktop, 'mobile': mobile})
        assert ua is not None


# Test 5: Invalid browser handling
@given(st.text(min_size=1))
@settings(max_examples=100)  
def test_invalid_browser(browser):
    valid_browsers = ['chrome', 'firefox']
    assume(browser not in valid_browsers)
    
    try:
        User_Agent(browser={'browser': browser})
        raise AssertionError(f"Expected RuntimeError for invalid browser '{browser}'")
    except RuntimeError as e:
        assert 'browser is not valid, valid browsers are' in str(e)


# Main test runner
def main():
    tests = [
        ("Invalid platform validation", test_invalid_platform),
        ("Source address type validation", test_source_address),
        ("HTML entity unescaping", test_html_unescape),
        ("Desktop/mobile constraint", test_desktop_mobile),
        ("Invalid browser validation", test_invalid_browser),
    ]
    
    passed = 0
    failed = 0
    
    print("\n" + "="*60)
    print("Starting Property-Based Testing for cloudscraper")
    print("="*60)
    
    for test_name, test_func in tests:
        if run_test(test_name, test_func):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n✅ All property-based tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed!")


if __name__ == "__main__":
    main()