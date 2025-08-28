#!/usr/bin/env python3
"""Property-based tests for htmldate.settings module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from functools import lru_cache
import hypothesis.strategies as st
from hypothesis import given, settings as hyp_settings, assume

# Import the module under test
import htmldate.settings as settings
from htmldate.validators import get_min_date, is_valid_date, is_valid_format
from htmldate.core import compare_reference


# Test 1: Constants are positive integers
def test_cache_size_positive():
    assert isinstance(settings.CACHE_SIZE, int)
    assert settings.CACHE_SIZE > 0


def test_max_file_size_positive():
    assert isinstance(settings.MAX_FILE_SIZE, int)
    assert settings.MAX_FILE_SIZE > 0


def test_max_candidates_positive():
    assert isinstance(settings.MAX_POSSIBLE_CANDIDATES, int)
    assert settings.MAX_POSSIBLE_CANDIDATES > 0


# Test 2: MIN_DATE properties
def test_min_date_is_datetime():
    assert isinstance(settings.MIN_DATE, datetime)


def test_min_date_in_past():
    assert settings.MIN_DATE < datetime.now()


# Test 3: CLEANING_LIST properties
def test_cleaning_list_is_list_of_strings():
    assert isinstance(settings.CLEANING_LIST, list)
    assert all(isinstance(tag, str) for tag in settings.CLEANING_LIST)
    assert len(settings.CLEANING_LIST) > 0


@given(st.sampled_from(settings.CLEANING_LIST))
def test_cleaning_list_contains_valid_html_tags(tag):
    # All tags should be lowercase alphanumeric
    assert tag.isalpha()
    assert tag.islower()
    # Common HTML tags should be reasonable length
    assert 1 <= len(tag) <= 20


# Test 4: Cross-module property - get_min_date respects MIN_DATE
@given(st.one_of(st.none(), 
                  st.datetimes(min_value=datetime(1900, 1, 1), 
                               max_value=datetime(2100, 1, 1))))
def test_get_min_date_respects_minimum(date_input):
    result = get_min_date(date_input)
    assert isinstance(result, datetime)
    if date_input is None:
        assert result == settings.MIN_DATE
    elif date_input < settings.MIN_DATE:
        # Should still respect the MIN_DATE floor
        assert result >= settings.MIN_DATE


# Test 5: is_valid_date respects MIN_DATE boundary
@given(st.datetimes(min_value=datetime(1900, 1, 1), 
                     max_value=datetime(1994, 12, 31)))
def test_dates_before_min_date_invalid(date_before_min):
    # Dates before MIN_DATE should be invalid
    assume(date_before_min < settings.MIN_DATE)
    result = is_valid_date(
        date_before_min,
        "%Y-%m-%d",
        settings.MIN_DATE,
        datetime.now()
    )
    assert result is False


@given(st.datetimes(min_value=settings.MIN_DATE, 
                     max_value=datetime.now()))
def test_dates_after_min_date_valid(valid_date):
    # Dates after MIN_DATE and before now should be valid
    result = is_valid_date(
        valid_date,
        "%Y-%m-%d", 
        settings.MIN_DATE,
        datetime.now()
    )
    assert result is True


# Test 6: Cache size property - lru_cache should work with CACHE_SIZE
@hyp_settings(max_examples=10)
@given(st.integers(min_value=1, max_value=1000000))
def test_lru_cache_with_cache_size(test_value):
    # Create a cached function using the CACHE_SIZE from settings
    @lru_cache(maxsize=settings.CACHE_SIZE)
    def cached_func(x):
        return x * 2
    
    # Should handle calls without errors
    result = cached_func(test_value)
    assert result == test_value * 2
    
    # Cache info should be available
    info = cached_func.cache_info()
    assert info.maxsize == settings.CACHE_SIZE


# Test 7: Output format validation
@given(st.sampled_from(["%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%m/%d/%Y"]))
def test_valid_output_formats(format_string):
    assert is_valid_format(format_string) is True


@given(st.sampled_from(["invalid", "", None, 123, "%q-%w-%e"]))  
def test_invalid_output_formats(format_string):
    assert is_valid_format(format_string) is False


# Test 8: Constants relationships
def test_constants_reasonable_relationships():
    # MAX_FILE_SIZE should be larger than typical web pages
    assert settings.MAX_FILE_SIZE > 1000
    
    # CACHE_SIZE should be reasonable for memory usage
    assert 1 <= settings.CACHE_SIZE <= 1000000
    
    # MAX_POSSIBLE_CANDIDATES should be reasonable for processing
    assert 1 <= settings.MAX_POSSIBLE_CANDIDATES <= 100000


# Test 9: MIN_DATE year property
def test_min_date_year_reasonable():
    # MIN_DATE year should be after the web started (early 1990s)
    assert settings.MIN_DATE.year >= 1990
    # And before current year
    assert settings.MIN_DATE.year <= datetime.now().year