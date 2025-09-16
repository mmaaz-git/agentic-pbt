#!/usr/bin/env python3
"""Execute property-based tests directly."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aiohttp-retry_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import traceback
from aiohttp_retry.client import _url_to_urls
from aiohttp_retry.retry_options import (
    ExponentialRetry, RandomRetry, ListRetry, FibonacciRetry, JitterRetry
)
from yarl import URL

def run_test(test_func, test_name):
    """Run a single test and report results."""
    print(f"\nRunning {test_name}...")
    try:
        test_func()
        print(f"✓ {test_name} passed")
        return True
    except Exception as e:
        print(f"✗ {test_name} failed:")
        print(f"  {str(e)}")
        traceback.print_exc()
        return False

# Test functions
def test_url_string():
    """Test URL string conversion."""
    for url_str in ["http://example.com", "https://test.org", "ftp://server.net"]:
        result = _url_to_urls(url_str)
        assert isinstance(result, tuple)
        assert len(result) == 1
        assert result[0] == url_str

def test_url_list():
    """Test URL list conversion."""
    url_list = ["http://a.com", "http://b.com", "http://c.com"]
    result = _url_to_urls(url_list)
    assert isinstance(result, tuple)
    assert len(result) == len(url_list)
    assert all(r == u for r, u in zip(result, url_list))

def test_empty_list():
    """Test empty list raises error."""
    try:
        _url_to_urls([])
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "you can pass url by str or list/tuple with attempts count size" in str(e)

def test_exponential_bounds():
    """Test exponential retry bounds."""
    retry = ExponentialRetry(start_timeout=0.1, max_timeout=10.0, factor=2.0)
    for attempt in range(10):
        timeout = retry.get_timeout(attempt)
        assert timeout >= 0.1
        assert timeout <= 10.0

def test_random_bounds():
    """Test random retry bounds."""
    retry = RandomRetry(min_timeout=1.0, max_timeout=5.0)
    for attempt in range(20):
        timeout = retry.get_timeout(attempt)
        assert timeout >= 1.0
        assert timeout <= 5.0

def test_list_indexing():
    """Test list retry indexing."""
    timeouts = [0.5, 1.0, 2.0, 4.0]
    retry = ListRetry(timeouts=timeouts)
    assert retry.attempts == len(timeouts)
    for i in range(len(timeouts)):
        assert retry.get_timeout(i) == timeouts[i]

def test_list_out_of_bounds():
    """Test list retry out of bounds."""
    timeouts = [0.5, 1.0]
    retry = ListRetry(timeouts=timeouts)
    try:
        retry.get_timeout(5)
        assert False, "Should have raised IndexError"
    except IndexError:
        pass

def test_fibonacci_sequence():
    """Test Fibonacci retry sequence."""
    retry = FibonacciRetry(multiplier=1.0, max_timeout=100.0)
    
    # Get first few timeouts
    timeouts = []
    for i in range(5):
        timeout = retry.get_timeout(i)
        timeouts.append(timeout)
    
    # The expected Fibonacci values
    expected = [1.0, 2.0, 3.0, 5.0, 8.0]
    for actual, exp in zip(timeouts, expected):
        assert actual == exp, f"Expected {exp}, got {actual}"

def test_fibonacci_state_bug():
    """Test Fibonacci retry state mutation bug."""
    retry1 = FibonacciRetry(multiplier=1.0, max_timeout=100.0)
    retry2 = FibonacciRetry(multiplier=1.0, max_timeout=100.0)
    
    # Both should give same sequence when called fresh
    seq1 = [retry1.get_timeout(i) for i in range(3)]
    seq2 = [retry2.get_timeout(i) for i in range(3)]
    
    print(f"  Sequence 1: {seq1}")
    print(f"  Sequence 2: {seq2}")
    
    # This SHOULD be true but might fail due to state mutation
    assert seq1 == seq2, f"Fresh instances should give same sequence: {seq1} != {seq2}"

def test_yarl_url():
    """Test YARL URL support."""
    yarl_url = URL("https://example.com")
    result = _url_to_urls(yarl_url)
    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0] == yarl_url

def test_invalid_types():
    """Test invalid URL types."""
    for invalid in [123, 45.6, {"key": "value"}, None]:
        try:
            _url_to_urls(invalid)
            # If we get here without exception for certain types, that might be OK
            # depending on implementation
            print(f"  Warning: {type(invalid)} did not raise error")
        except (ValueError, TypeError, AttributeError):
            pass  # Expected

# Run all tests
def main():
    tests = [
        (test_url_string, "URL string conversion"),
        (test_url_list, "URL list conversion"),
        (test_empty_list, "Empty list error"),
        (test_exponential_bounds, "Exponential retry bounds"),
        (test_random_bounds, "Random retry bounds"),
        (test_list_indexing, "List retry indexing"),
        (test_list_out_of_bounds, "List retry out of bounds"),
        (test_fibonacci_sequence, "Fibonacci sequence"),
        (test_fibonacci_state_bug, "Fibonacci state mutation"),
        (test_yarl_url, "YARL URL support"),
        (test_invalid_types, "Invalid URL types"),
    ]
    
    passed = 0
    failed = 0
    
    print("=" * 50)
    print("Running Property-Based Tests")
    print("=" * 50)
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    if failed > 0:
        print("\n⚠️ BUGS FOUND! Check the failures above.")
        return 1
    else:
        print("\n✅ All tests passed!")
        return 0

if __name__ == "__main__":
    exit(main())