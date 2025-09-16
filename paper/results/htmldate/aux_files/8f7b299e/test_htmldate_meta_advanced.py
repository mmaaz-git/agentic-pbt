"""Advanced property-based tests for htmldate.meta module to find potential bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc
import weakref
from unittest.mock import patch, MagicMock
import pytest
from hypothesis import given, strategies as st, settings, assume, example

import htmldate.meta
from htmldate.validators import is_valid_date, is_valid_format, filter_ymd_candidate
from htmldate.core import compare_reference
from htmldate.extractors import try_date_expr
from htmldate.utils import Extractor


@settings(max_examples=500, deadline=5000)
@given(
    st.integers(min_value=2, max_value=10),
    st.lists(st.text(min_size=5, max_size=10), min_size=10, max_size=50)
)
def test_concurrent_reset_caches(num_threads, test_dates):
    """Test that concurrent calls to reset_caches() don't cause issues."""
    earliest = datetime(2020, 1, 1)
    latest = datetime(2025, 12, 31)
    
    def populate_and_reset():
        # Populate cache
        for i, date_str in enumerate(test_dates[:5]):
            try:
                test_date = f"2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}"
                is_valid_date(test_date, "%Y-%m-%d", earliest, latest)
            except:
                pass
        
        # Reset caches
        htmldate.meta.reset_caches()
        
        # Populate again
        for i, date_str in enumerate(test_dates[5:10]):
            try:
                test_date = f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}"
                is_valid_date(test_date, "%Y-%m-%d", earliest, latest)
            except:
                pass
        
        return True
    
    # Run concurrent resets
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(populate_and_reset) for _ in range(num_threads)]
        results = [f.result() for f in as_completed(futures)]
    
    # Verify all completed successfully
    assert all(results)
    
    # Final reset should work
    htmldate.meta.reset_caches()
    assert is_valid_date.cache_info().currsize == 0


@settings(max_examples=100)
@given(st.integers(min_value=10, max_value=100))
def test_reset_during_active_caching(num_operations):
    """Test resetting caches while they're being actively used."""
    earliest = datetime(2020, 1, 1)
    latest = datetime(2025, 12, 31)
    results = []
    
    def cache_user():
        for i in range(num_operations):
            date = f"2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}"
            result = is_valid_date(date, "%Y-%m-%d", earliest, latest)
            results.append(result)
            if i == num_operations // 2:
                # Reset in the middle
                htmldate.meta.reset_caches()
    
    # Run the test
    cache_user()
    
    # Cache should be smaller than num_operations if reset worked
    final_size = is_valid_date.cache_info().currsize
    assert final_size < num_operations


@given(
    st.lists(
        st.tuples(
            st.integers(min_value=1990, max_value=2030),
            st.integers(min_value=1, max_value=12),
            st.integers(min_value=1, max_value=28)
        ),
        min_size=1,
        max_size=100
    )
)
def test_cache_memory_consistency(date_tuples):
    """Test that clearing caches actually allows garbage collection."""
    earliest = datetime(1990, 1, 1)
    latest = datetime(2040, 12, 31)
    
    # Create many cache entries
    for year, month, day in date_tuples:
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        is_valid_date(date_str, "%Y-%m-%d", earliest, latest)
    
    initial_cache_size = is_valid_date.cache_info().currsize
    
    # Clear caches
    htmldate.meta.reset_caches()
    
    # Force garbage collection
    gc.collect()
    
    # Cache should be empty
    assert is_valid_date.cache_info().currsize == 0


@settings(max_examples=200)
@given(
    st.text(min_size=1, max_size=50),
    st.sampled_from(["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%Y%m%d", "%B %d, %Y"])
)
def test_cache_state_after_exception(date_str, format_str):
    """Test that cache state remains consistent even when functions raise exceptions."""
    earliest = datetime(2020, 1, 1)
    latest = datetime(2025, 12, 31)
    
    # Get initial cache state
    initial_info = is_valid_date.cache_info()
    
    # Try to validate a potentially invalid date
    try:
        result = is_valid_date(date_str, format_str, earliest, latest)
    except:
        # If exception occurs, cache should still be in valid state
        pass
    
    # Reset should work regardless of exceptions
    try:
        htmldate.meta.reset_caches()
    except Exception as e:
        pytest.fail(f"reset_caches() failed after exception: {e}")
    
    # Cache should be cleared
    assert is_valid_date.cache_info().currsize == 0


@given(st.integers(min_value=1, max_value=1000))
def test_repeated_reset_memory_leak(num_resets):
    """Test that repeated resets don't cause memory leaks."""
    earliest = datetime(2020, 1, 1)
    latest = datetime(2025, 12, 31)
    
    # Baseline memory state
    gc.collect()
    initial_objects = len(gc.get_objects())
    
    for i in range(min(num_resets, 100)):  # Cap at 100 to avoid timeout
        # Add some cache entries
        is_valid_date(f"2023-01-{(i % 28) + 1:02d}", "%Y-%m-%d", earliest, latest)
        is_valid_format(f"%Y-%m-{i % 30:02d}")
        
        # Reset
        htmldate.meta.reset_caches()
    
    # Force garbage collection
    gc.collect()
    
    # Check that we haven't leaked too many objects
    final_objects = len(gc.get_objects())
    # Allow some growth but not linear with num_resets
    assert final_objects - initial_objects < 1000


@settings(max_examples=100)
@given(
    st.booleans(),
    st.booleans(),
    st.booleans()
)
def test_partial_import_failures(fail_encoding, fail_suspicious, fail_accentuated):
    """Test reset_caches with various combinations of import failures."""
    original_funcs = {}
    
    # Save originals
    for name in ['encoding_languages', 'is_suspiciously_successive_range', 'is_accentuated']:
        if hasattr(htmldate.meta, name):
            original_funcs[name] = getattr(htmldate.meta, name)
    
    try:
        # Selectively remove functions
        if fail_encoding and 'encoding_languages' in original_funcs:
            del htmldate.meta.encoding_languages
        if fail_suspicious and 'is_suspiciously_successive_range' in original_funcs:
            del htmldate.meta.is_suspiciously_successive_range
        if fail_accentuated and 'is_accentuated' in original_funcs:
            del htmldate.meta.is_accentuated
        
        # Should not raise exception
        htmldate.meta.reset_caches()
        
        # Verify htmldate caches are still cleared
        assert is_valid_date.cache_info().currsize == 0
        
    finally:
        # Restore functions
        for name, func in original_funcs.items():
            setattr(htmldate.meta, name, func)


@settings(max_examples=100)
@given(st.data())
def test_cache_function_attributes_preserved(data):
    """Test that cache clearing preserves function attributes and behavior."""
    # Get cache info before
    cache_funcs = [
        is_valid_date,
        is_valid_format, 
        filter_ymd_candidate,
        compare_reference,
        try_date_expr
    ]
    
    # Store original attributes
    original_attrs = {}
    for func in cache_funcs:
        original_attrs[func] = {
            'maxsize': func.cache_info().maxsize,
            'typed': getattr(func, '__wrapped__', func).__code__.co_argcount
        }
    
    # Reset caches
    htmldate.meta.reset_caches()
    
    # Verify attributes are preserved
    for func in cache_funcs:
        assert func.cache_info().maxsize == original_attrs[func]['maxsize']
        assert getattr(func, '__wrapped__', func).__code__.co_argcount == original_attrs[func]['typed']
        # Cache should be empty but functional
        assert func.cache_info().currsize == 0
        assert func.cache_info().hits == 0
        assert func.cache_info().misses == 0


if __name__ == "__main__":
    print("Running advanced property-based tests for htmldate.meta...")
    test_concurrent_reset_caches()
    test_cache_memory_consistency()
    print("Advanced tests completed!")