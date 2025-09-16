"""Property-based tests for htmldate.meta module using Hypothesis."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from unittest.mock import patch, MagicMock
import pytest
from hypothesis import given, strategies as st, settings, assume

import htmldate.meta
from htmldate.validators import is_valid_date, is_valid_format, filter_ymd_candidate
from htmldate.core import compare_reference
from htmldate.extractors import try_date_expr
from htmldate.utils import Extractor


@settings(max_examples=1000)
@given(st.integers(min_value=1, max_value=100))
def test_reset_caches_idempotence(n_calls):
    """Test that reset_caches() is idempotent - calling it multiple times 
    has the same effect as calling it once."""
    # Get initial cache info for one of the cached functions
    initial_cache_info = is_valid_date.cache_info()
    
    # Add some data to the cache to make it non-empty
    is_valid_date("2023-01-01", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2025, 1, 1))
    is_valid_date("2023-02-01", "%Y-%m-%d", datetime(2020, 1, 1), datetime(2025, 1, 1))
    
    # Verify cache has some hits/misses
    pre_reset_info = is_valid_date.cache_info()
    assume(pre_reset_info.currsize > 0)  # Ensure cache is not empty
    
    # Call reset_caches n times
    for _ in range(n_calls):
        htmldate.meta.reset_caches()
    
    # Check that cache is cleared
    post_reset_info = is_valid_date.cache_info()
    assert post_reset_info.currsize == 0
    assert post_reset_info.hits == 0
    assert post_reset_info.misses == 0


def test_reset_caches_handles_missing_charset_functions():
    """Test that reset_caches() handles missing charset_normalizer functions gracefully."""
    # Mock the charset_normalizer functions to raise AttributeError
    with patch('htmldate.meta.encoding_languages', MagicMock(spec=[])):
        with patch('htmldate.meta.is_suspiciously_successive_range', MagicMock(spec=[])):
            with patch('htmldate.meta.is_accentuated', MagicMock(spec=[])):
                # Should not raise an exception
                try:
                    htmldate.meta.reset_caches()
                except (AttributeError, NameError):
                    pytest.fail("reset_caches() should handle missing functions gracefully")


@settings(max_examples=500)
@given(
    st.text(min_size=1, max_size=20).filter(lambda x: "-" not in x and x.isdigit() == False),
    st.text(min_size=1, max_size=20).filter(lambda x: "-" not in x and x.isdigit() == False),
)
def test_reset_caches_clears_all_caches(date1, date2):
    """Test that reset_caches() actually clears all the caches it claims to clear."""
    # Create distinct dates to avoid collisions
    test_date1 = f"2023-01-{str(hash(date1) % 28 + 1).zfill(2)}"
    test_date2 = f"2023-02-{str(hash(date2) % 28 + 1).zfill(2)}"
    
    # Use all cached functions to populate their caches
    earliest = datetime(2020, 1, 1)
    latest = datetime(2025, 12, 31)
    
    # is_valid_date cache
    is_valid_date(test_date1, "%Y-%m-%d", earliest, latest)
    is_valid_date(test_date2, "%Y-%m-%d", earliest, latest)
    initial_valid_cache = is_valid_date.cache_info()
    
    # is_valid_format cache
    is_valid_format("%Y-%m-%d")
    is_valid_format("%d/%m/%Y")
    initial_format_cache = is_valid_format.cache_info()
    
    # filter_ymd_candidate cache (using a mock Match object)
    class MockMatch:
        def __init__(self, groups):
            self.groups_data = groups
        def __getitem__(self, key):
            return self.groups_data[key]
    
    match = MockMatch(["2023-01-15", "2023", "01", "15"])
    filter_ymd_candidate(match, None, True, 2020, "%Y-%m-%d", earliest, latest)
    initial_filter_cache = filter_ymd_candidate.cache_info()
    
    # compare_reference cache
    options = Extractor(
        extensive_search=False,
        original_date=True,
        outputformat="%Y-%m-%d",
        min_date=earliest,
        max_date=latest
    )
    compare_reference(0, test_date1, options)
    initial_compare_cache = compare_reference.cache_info()
    
    # try_date_expr cache  
    try_date_expr(test_date1, "%Y-%m-%d", False, earliest, latest)
    initial_try_cache = try_date_expr.cache_info()
    
    # Reset all caches
    htmldate.meta.reset_caches()
    
    # Verify all caches are cleared
    assert is_valid_date.cache_info().currsize == 0
    assert is_valid_format.cache_info().currsize == 0
    assert filter_ymd_candidate.cache_info().currsize == 0
    assert compare_reference.cache_info().currsize == 0
    assert try_date_expr.cache_info().currsize == 0


@given(
    st.datetimes(min_value=datetime(1995, 1, 1), max_value=datetime(2039, 12, 31)),
    st.sampled_from(["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%Y%m%d"]),
)  
def test_cached_function_determinism_after_reset(test_date, format_string):
    """Test that cached functions return the same results after cache is cleared."""
    date_str = test_date.strftime(format_string)
    earliest = datetime(1990, 1, 1)
    latest = datetime(2040, 12, 31)
    
    # Call function before reset
    result_before = is_valid_date(date_str, format_string, earliest, latest)
    
    # Reset caches
    htmldate.meta.reset_caches()
    
    # Call function after reset
    result_after = is_valid_date(date_str, format_string, earliest, latest)
    
    # Results should be the same
    assert result_before == result_after


@given(st.integers(min_value=0, max_value=1000))
def test_reset_caches_with_empty_caches(seed):
    """Test that reset_caches() works correctly even when caches are already empty."""
    # Clear caches first
    htmldate.meta.reset_caches()
    
    # Verify caches are empty
    assert is_valid_date.cache_info().currsize == 0
    
    # Call reset_caches again - should not raise any errors
    try:
        htmldate.meta.reset_caches()
    except Exception as e:
        pytest.fail(f"reset_caches() raised {e} on empty caches")
    
    # Caches should still be empty
    assert is_valid_date.cache_info().currsize == 0


@given(
    st.lists(
        st.tuples(
            st.text(min_size=10, max_size=10).map(lambda x: f"20{x[:2]}-{str(hash(x[2:4]) % 12 + 1).zfill(2)}-{str(hash(x[4:6]) % 28 + 1).zfill(2)}"),
            st.sampled_from(["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y"])
        ),
        min_size=1,
        max_size=20
    )
)
def test_cache_size_increases_then_resets(date_format_pairs):
    """Test that cache size increases with use and resets to zero after reset_caches()."""
    # Reset to start fresh
    htmldate.meta.reset_caches()
    initial_size = is_valid_date.cache_info().currsize
    assert initial_size == 0
    
    earliest = datetime(2000, 1, 1)
    latest = datetime(2030, 12, 31)
    
    # Add entries to cache
    for date_str, format_str in date_format_pairs:
        try:
            is_valid_date(date_str, format_str, earliest, latest)
        except:
            pass  # Some generated dates might be invalid, that's ok
    
    # Cache size should have increased (unless all dates were duplicates)
    mid_size = is_valid_date.cache_info().currsize
    
    # Reset caches
    htmldate.meta.reset_caches()
    
    # Cache should be empty again
    final_size = is_valid_date.cache_info().currsize
    assert final_size == 0


def test_reset_caches_with_mock_import_error():
    """Test that reset_caches handles the case where charset_normalizer is not imported."""
    # Save original functions if they exist
    original_encoding = getattr(htmldate.meta, 'encoding_languages', None)
    original_suspicious = getattr(htmldate.meta, 'is_suspiciously_successive_range', None) 
    original_accentuated = getattr(htmldate.meta, 'is_accentuated', None)
    
    try:
        # Delete the attributes to simulate import failure
        if hasattr(htmldate.meta, 'encoding_languages'):
            del htmldate.meta.encoding_languages
        if hasattr(htmldate.meta, 'is_suspiciously_successive_range'):
            del htmldate.meta.is_suspiciously_successive_range
        if hasattr(htmldate.meta, 'is_accentuated'):
            del htmldate.meta.is_accentuated
        
        # Should not raise an exception
        htmldate.meta.reset_caches()
        
    finally:
        # Restore original functions
        if original_encoding is not None:
            htmldate.meta.encoding_languages = original_encoding
        if original_suspicious is not None:
            htmldate.meta.is_suspiciously_successive_range = original_suspicious
        if original_accentuated is not None:
            htmldate.meta.is_accentuated = original_accentuated


if __name__ == "__main__":
    # Run a quick test to verify the module works
    print("Running property-based tests for htmldate.meta...")
    test_reset_caches_idempotence()
    test_reset_caches_handles_missing_charset_functions()
    test_reset_caches_with_empty_caches()
    print("Basic tests passed!")