#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from hypothesis import given, strategies as st, assume
import htmldate.extractors as extractors
from htmldate.utils import Extractor


@given(st.integers(min_value=0, max_value=200))
def test_correct_year_invariant(year):
    """Test the year correction logic:
    - Years < 100 and >= 90 → 1900 + year (1990-1999)
    - Years < 90 → 2000 + year (2000-2089)
    - Years >= 100 → unchanged
    """
    result = extractors.correct_year(year)
    
    if year < 100:
        if year >= 90:
            assert result == 1900 + year, f"Year {year} should map to {1900 + year}, got {result}"
        else:
            assert result == 2000 + year, f"Year {year} should map to {2000 + year}, got {result}"
    else:
        assert result == year, f"Year {year} should remain unchanged, got {result}"
    
    # Result should always be a 4-digit year in valid range
    assert result >= 1900, f"Result {result} is before 1900"
    assert result <= 2200, f"Result {result} is after 2200"


@given(st.integers(min_value=1, max_value=31), st.integers(min_value=1, max_value=31))
def test_try_swap_values_logic(day, month):
    """Test the swap logic: only swap if month > 12 and day <= 12"""
    result_day, result_month = extractors.try_swap_values(day, month)
    
    if month > 12 and day <= 12:
        # Should swap
        assert result_day == month, f"Expected day={month}, got {result_day}"
        assert result_month == day, f"Expected month={day}, got {result_month}"
    else:
        # Should not swap
        assert result_day == day, f"Day should remain {day}, got {result_day}"
        assert result_month == month, f"Month should remain {month}, got {result_month}"


@given(st.text(min_size=0, max_size=100))
def test_trim_text_invariant(text):
    """Test that trim_text preserves or reduces length"""
    from htmldate.utils import trim_text
    result = trim_text(text)
    
    # Result should never be longer than input
    assert len(result) <= len(text), f"trim_text made text longer: {len(text)} → {len(result)}"
    
    # Result should be a string
    assert isinstance(result, str)


@given(
    st.integers(min_value=1990, max_value=2039),
    st.integers(min_value=1, max_value=12),
    st.integers(min_value=1, max_value=28)  # Using 28 to avoid month-specific day issues
)
def test_url_date_extraction(year, month, day):
    """Test that valid dates in URLs can be extracted"""
    # Create a URL with a date
    url = f"https://example.com/blog/{year}/{month:02d}/{day:02d}/post.html"
    
    # Create extractor options
    options = Extractor(
        extensive_search=False,
        max_date=datetime(2040, 12, 31),
        min_date=datetime(1990, 1, 1),
        original_date=False,
        outputformat="%Y-%m-%d"
    )
    
    result = extractors.extract_url_date(url, options)
    
    # Should extract the date
    expected = f"{year}-{month:02d}-{day:02d}"
    assert result == expected, f"Expected {expected}, got {result}"


@given(st.text(min_size=1, max_size=30, alphabet="0123456789-/."))
def test_regex_parse_robustness(text):
    """Test that regex_parse doesn't crash on arbitrary input"""
    # This should not raise an exception
    result = extractors.regex_parse(text)
    
    # Result should be None or a datetime object
    assert result is None or isinstance(result, datetime)


@given(
    st.integers(min_value=1990, max_value=2039),
    st.integers(min_value=1, max_value=12),
    st.integers(min_value=1, max_value=28)
)
def test_custom_parse_iso_format(year, month, day):
    """Test custom_parse with ISO format strings"""
    date_string = f"{year:04d}-{month:02d}-{day:02d}"
    
    result = extractors.custom_parse(
        date_string,
        "%Y-%m-%d",
        datetime(1990, 1, 1),
        datetime(2040, 12, 31)
    )
    
    # Should successfully parse ISO dates
    assert result == date_string, f"Failed to parse ISO date: {date_string}"


@given(
    st.integers(min_value=1990, max_value=2039),
    st.integers(min_value=1, max_value=12),
    st.integers(min_value=1, max_value=28)
)
def test_custom_parse_yyyymmdd(year, month, day):
    """Test custom_parse with YYYYMMDD format (no separators)"""
    date_string = f"{year:04d}{month:02d}{day:02d}"
    
    result = extractors.custom_parse(
        date_string,
        "%Y-%m-%d",
        datetime(1990, 1, 1),
        datetime(2040, 12, 31)
    )
    
    # Should parse dates without separators
    expected = f"{year:04d}-{month:02d}-{day:02d}"
    assert result == expected, f"Failed to parse YYYYMMDD date: {date_string}"


@given(st.integers(min_value=0, max_value=99))
def test_correct_year_century_boundary(year):
    """Test correct_year at century boundaries"""
    result = extractors.correct_year(year)
    
    # Specific boundary tests
    if year == 89:
        assert result == 2089
    elif year == 90:
        assert result == 1990
    elif year == 99:
        assert result == 1999
    elif year == 0:
        assert result == 2000


@given(
    st.integers(min_value=0, max_value=40),
    st.integers(min_value=0, max_value=40)
)
def test_try_swap_values_edge_cases(day, month):
    """Test try_swap_values with edge cases including zeros"""
    # Should not crash
    result_day, result_month = extractors.try_swap_values(day, month)
    
    # Basic sanity checks
    assert isinstance(result_day, int)
    assert isinstance(result_month, int)
    
    # Values should come from input
    assert {result_day, result_month} == {day, month} or (result_day == month and result_month == day)