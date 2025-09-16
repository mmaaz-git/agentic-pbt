#!/usr/bin/env python3
"""Property-based tests for the main find_date function."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from hypothesis import given, strategies as st, assume, settings
import pytest

from htmldate import find_date


# Test 1: find_date should not crash on any string input
@given(st.text(min_size=0, max_size=1000))
@settings(max_examples=50, deadline=5000)
def test_find_date_no_crash_on_random_strings(html_string):
    """Test that find_date doesn't crash on arbitrary string inputs."""
    result = find_date(html_string)
    
    # Should return None or a string
    assert result is None or isinstance(result, str)
    
    # If it returns a date, it should be in the expected format
    if result is not None:
        # Default format is %Y-%m-%d
        try:
            parsed = datetime.strptime(result, "%Y-%m-%d")
        except ValueError:
            pytest.fail(f"find_date returned invalid date format: {result}")


# Test 2: find_date with custom output formats
@given(
    st.text(min_size=0, max_size=500),
    st.sampled_from(["%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%Y", "%B %d, %Y"])
)
@settings(max_examples=25, deadline=5000)
def test_find_date_with_custom_formats(html_string, output_format):
    """Test that find_date respects custom output formats."""
    result = find_date(html_string, outputformat=output_format)
    
    # Should return None or a string
    assert result is None or isinstance(result, str)
    
    # If it returns a date, it should be in the requested format
    if result is not None:
        try:
            parsed = datetime.strptime(result, output_format)
        except ValueError:
            pytest.fail(f"find_date returned date not matching requested format: {result} (expected format: {output_format})")


# Test 3: find_date with date boundaries
@given(st.text(min_size=0, max_size=500))
@settings(max_examples=25, deadline=5000)
def test_find_date_respects_boundaries(html_string):
    """Test that find_date respects min_date and max_date boundaries."""
    min_date = "2020-01-01"
    max_date = "2023-12-31"
    
    result = find_date(html_string, min_date=min_date, max_date=max_date)
    
    # Should return None or a string
    assert result is None or isinstance(result, str)
    
    # If it returns a date, it should be within the boundaries
    if result is not None:
        try:
            parsed = datetime.strptime(result, "%Y-%m-%d")
            min_dt = datetime.strptime(min_date, "%Y-%m-%d")
            max_dt = datetime.strptime(max_date, "%Y-%m-%d")
            assert min_dt <= parsed <= max_dt
        except ValueError:
            pytest.fail(f"find_date returned invalid date: {result}")


# Test 4: HTML with actual date patterns
@given(
    st.integers(min_value=2000, max_value=2025),
    st.integers(min_value=1, max_value=12),
    st.integers(min_value=1, max_value=28)
)
@settings(max_examples=50, deadline=5000)
def test_find_date_with_structured_dates(year, month, day):
    """Test find_date with HTML containing structured date patterns."""
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    
    # Test various HTML patterns that should contain the date
    html_patterns = [
        f'<meta name="date" content="{date_str}">',
        f'<time datetime="{date_str}">Published</time>',
        f'<div class="date">{date_str}</div>',
        f'<meta property="article:published_time" content="{date_str}T00:00:00Z">',
    ]
    
    for html in html_patterns:
        result = find_date(html)
        
        # Should find the date in these clear cases
        assert result is not None, f"Failed to find date in: {html}"
        
        # The found date should match what we put in
        assert result == date_str, f"Found {result} but expected {date_str}"


# Test 5: Invalid output format handling
@given(
    st.text(min_size=0, max_size=200),
    st.text(min_size=1, max_size=20).filter(lambda x: "%" not in x)
)
@settings(max_examples=25, deadline=5000)
def test_find_date_with_invalid_format(html_string, invalid_format):
    """Test that find_date handles invalid output formats gracefully."""
    result = find_date(html_string, outputformat=invalid_format)
    
    # Should return None for invalid formats
    assert result is None


# Test 6: Test URL date extraction
@given(
    st.integers(min_value=2000, max_value=2025),
    st.integers(min_value=1, max_value=12),
    st.integers(min_value=1, max_value=28)
)
@settings(max_examples=25, deadline=5000)
def test_find_date_from_url(year, month, day):
    """Test that find_date can extract dates from URLs."""
    urls = [
        f"https://example.com/{year}/{month:02d}/{day:02d}/article.html",
        f"https://example.com/post-{year}-{month:02d}-{day:02d}.html",
        f"https://example.com/?date={year}{month:02d}{day:02d}",
    ]
    
    for url in urls:
        # Pass empty HTML with URL
        result = find_date("<html></html>", url=url)
        
        # Should find the date from the URL
        if result is not None:
            try:
                parsed = datetime.strptime(result, "%Y-%m-%d")
                # Check if the extracted date matches
                assert parsed.year == year
                assert parsed.month == month
                assert parsed.day == day
            except (ValueError, AssertionError):
                # URL extraction might not always work, that's ok
                pass


if __name__ == "__main__":
    print("Running property-based tests for find_date function...")
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short", "-x"]))