"""Edge case tests for htmldate.meta module to find real bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from unittest.mock import patch, MagicMock, PropertyMock
import pytest
from hypothesis import given, strategies as st, settings, assume, example
import re

import htmldate.meta
from htmldate.validators import is_valid_date, is_valid_format, filter_ymd_candidate
from htmldate.core import compare_reference
from htmldate.extractors import try_date_expr
from htmldate.utils import Extractor


@settings(max_examples=1000)
@given(st.data())
def test_reset_caches_with_mock_cache_clear_failure(data):
    """Test if reset_caches handles exceptions from cache_clear() correctly."""
    
    # Pick which function's cache_clear should fail
    functions_to_fail = data.draw(st.sets(
        st.sampled_from([
            'compare_reference',
            'filter_ymd_candidate', 
            'is_valid_date',
            'is_valid_format',
            'try_date_expr'
        ]),
        min_size=0,
        max_size=5
    ))
    
    original_clears = {}
    
    try:
        # Mock cache_clear to raise exception for selected functions
        for func_name in functions_to_fail:
            if func_name == 'compare_reference':
                from htmldate.core import compare_reference
                original_clears[func_name] = compare_reference.cache_clear
                compare_reference.cache_clear = MagicMock(side_effect=RuntimeError(f"Mock error in {func_name}"))
            elif func_name == 'filter_ymd_candidate':
                from htmldate.validators import filter_ymd_candidate
                original_clears[func_name] = filter_ymd_candidate.cache_clear
                filter_ymd_candidate.cache_clear = MagicMock(side_effect=RuntimeError(f"Mock error in {func_name}"))
            elif func_name == 'is_valid_date':
                from htmldate.validators import is_valid_date
                original_clears[func_name] = is_valid_date.cache_clear
                is_valid_date.cache_clear = MagicMock(side_effect=RuntimeError(f"Mock error in {func_name}"))
            elif func_name == 'is_valid_format':
                from htmldate.validators import is_valid_format
                original_clears[func_name] = is_valid_format.cache_clear
                is_valid_format.cache_clear = MagicMock(side_effect=RuntimeError(f"Mock error in {func_name}"))
            elif func_name == 'try_date_expr':
                from htmldate.extractors import try_date_expr
                original_clears[func_name] = try_date_expr.cache_clear
                try_date_expr.cache_clear = MagicMock(side_effect=RuntimeError(f"Mock error in {func_name}"))
        
        # reset_caches should raise the exception, not handle it silently
        if functions_to_fail:
            with pytest.raises(RuntimeError):
                htmldate.meta.reset_caches()
        else:
            # Should work normally
            htmldate.meta.reset_caches()
            
    finally:
        # Restore original functions
        for func_name, original_clear in original_clears.items():
            if func_name == 'compare_reference':
                from htmldate.core import compare_reference
                compare_reference.cache_clear = original_clear
            elif func_name == 'filter_ymd_candidate':
                from htmldate.validators import filter_ymd_candidate
                filter_ymd_candidate.cache_clear = original_clear
            elif func_name == 'is_valid_date':
                from htmldate.validators import is_valid_date
                is_valid_date.cache_clear = original_clear
            elif func_name == 'is_valid_format':
                from htmldate.validators import is_valid_format
                is_valid_format.cache_clear = original_clear
            elif func_name == 'try_date_expr':
                from htmldate.extractors import try_date_expr
                try_date_expr.cache_clear = original_clear


@settings(max_examples=500)
@given(st.data())
def test_cache_clear_attribute_missing(data):
    """Test behavior when cache_clear attribute is missing from functions."""
    
    function_names = data.draw(st.sets(
        st.sampled_from([
            'compare_reference',
            'filter_ymd_candidate',
            'is_valid_date', 
            'is_valid_format',
            'try_date_expr'
        ]),
        min_size=1,
        max_size=5
    ))
    
    saved_attrs = {}
    
    try:
        # Remove cache_clear from selected functions
        for func_name in function_names:
            if func_name == 'compare_reference':
                from htmldate.core import compare_reference
                if hasattr(compare_reference, 'cache_clear'):
                    saved_attrs[func_name] = compare_reference.cache_clear
                    del compare_reference.cache_clear
            elif func_name == 'filter_ymd_candidate':
                from htmldate.validators import filter_ymd_candidate
                if hasattr(filter_ymd_candidate, 'cache_clear'):
                    saved_attrs[func_name] = filter_ymd_candidate.cache_clear
                    del filter_ymd_candidate.cache_clear
            elif func_name == 'is_valid_date':
                from htmldate.validators import is_valid_date
                if hasattr(is_valid_date, 'cache_clear'):
                    saved_attrs[func_name] = is_valid_date.cache_clear
                    del is_valid_date.cache_clear
            elif func_name == 'is_valid_format':
                from htmldate.validators import is_valid_format
                if hasattr(is_valid_format, 'cache_clear'):
                    saved_attrs[func_name] = is_valid_format.cache_clear
                    del is_valid_format.cache_clear
            elif func_name == 'try_date_expr':
                from htmldate.extractors import try_date_expr
                if hasattr(try_date_expr, 'cache_clear'):
                    saved_attrs[func_name] = try_date_expr.cache_clear
                    del try_date_expr.cache_clear
        
        # This should raise AttributeError
        with pytest.raises(AttributeError):
            htmldate.meta.reset_caches()
            
    finally:
        # Restore attributes
        for func_name, cache_clear in saved_attrs.items():
            if func_name == 'compare_reference':
                from htmldate.core import compare_reference
                compare_reference.cache_clear = cache_clear
            elif func_name == 'filter_ymd_candidate':
                from htmldate.validators import filter_ymd_candidate
                filter_ymd_candidate.cache_clear = cache_clear
            elif func_name == 'is_valid_date':
                from htmldate.validators import is_valid_date  
                is_valid_date.cache_clear = cache_clear
            elif func_name == 'is_valid_format':
                from htmldate.validators import is_valid_format
                is_valid_format.cache_clear = cache_clear
            elif func_name == 'try_date_expr':
                from htmldate.extractors import try_date_expr
                try_date_expr.cache_clear = cache_clear


@settings(max_examples=100)
@given(st.text())
def test_reset_caches_with_corrupted_module_state(module_corruption):
    """Test reset_caches when the module is in a corrupted state."""
    
    # Save original reset_caches
    original_reset = htmldate.meta.reset_caches
    
    try:
        # Try various module corruptions
        if len(module_corruption) % 3 == 0:
            # Replace reset_caches with a non-callable
            htmldate.meta.reset_caches = module_corruption
            with pytest.raises((TypeError, AttributeError)):
                htmldate.meta.reset_caches()
        elif len(module_corruption) % 3 == 1:
            # Make reset_caches None
            htmldate.meta.reset_caches = None
            with pytest.raises(TypeError):
                htmldate.meta.reset_caches()
        else:
            # Normal case
            htmldate.meta.reset_caches()
            
    finally:
        # Restore
        htmldate.meta.reset_caches = original_reset


@settings(max_examples=500)
@given(
    st.text(min_size=1),
    st.text(min_size=1)
)
def test_charset_function_name_changes(new_name1, new_name2):
    """Test that reset_caches handles changed function names in charset_normalizer."""
    
    # Create mock functions with different names
    mock_func1 = MagicMock()
    mock_func1.cache_clear = MagicMock()
    
    mock_func2 = MagicMock()
    mock_func2.cache_clear = MagicMock()
    
    # Save originals
    original_encoding = getattr(htmldate.meta, 'encoding_languages', None)
    original_suspicious = getattr(htmldate.meta, 'is_suspiciously_successive_range', None)
    
    try:
        # Replace with renamed versions
        setattr(htmldate.meta, new_name1, mock_func1)
        setattr(htmldate.meta, new_name2, mock_func2)
        
        # Remove originals to simulate rename
        if hasattr(htmldate.meta, 'encoding_languages'):
            del htmldate.meta.encoding_languages
        if hasattr(htmldate.meta, 'is_suspiciously_successive_range'):
            del htmldate.meta.is_suspiciously_successive_range
        
        # Should handle this gracefully (logs error but doesn't crash)
        htmldate.meta.reset_caches()
        
        # The new functions won't be cleared (they're not known to reset_caches)
        mock_func1.cache_clear.assert_not_called()
        mock_func2.cache_clear.assert_not_called()
        
    finally:
        # Clean up
        if hasattr(htmldate.meta, new_name1):
            delattr(htmldate.meta, new_name1)
        if hasattr(htmldate.meta, new_name2):
            delattr(htmldate.meta, new_name2)
        
        # Restore originals
        if original_encoding:
            htmldate.meta.encoding_languages = original_encoding
        if original_suspicious:
            htmldate.meta.is_suspiciously_successive_range = original_suspicious


if __name__ == "__main__":
    print("Running edge case tests...")
    test_cache_clear_attribute_missing()
    test_reset_caches_with_corrupted_module_state()
    print("Edge case tests completed!")