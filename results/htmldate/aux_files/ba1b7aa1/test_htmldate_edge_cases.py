#!/usr/bin/env /root/hypothesis-llm/envs/htmldate_env/bin/python
"""Edge case property-based tests for htmldate.core module"""

import re
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from hypothesis import given, strategies as st, settings, assume, example
import math

# Import target modules
from htmldate.core import normalize_match, search_pattern, select_candidate, find_date
from htmldate.validators import plausible_year_filter, is_valid_date
from htmldate.utils import Extractor
from collections import Counter
import re


# Test for potential edge cases in normalize_match
class FakeMatch:
    """Mock Match object for testing normalize_match"""
    def __init__(self, groups):
        self._groups = groups
    
    def groups(self):
        return self._groups


@given(
    day=st.text(min_size=0, max_size=5),
    month=st.text(min_size=0, max_size=5),
    year=st.text(min_size=0, max_size=5)
)
def test_normalize_match_robustness(day, month, year):
    """Test normalize_match with various string inputs"""
    # Only test with strings that could be interpreted as numbers
    if not day or not month or not year:
        return
    
    try:
        # Check if they can be converted to integers
        int_day = int(day)
        int_month = int(month) 
        int_year = int(year)
        
        # Skip if values are too large
        if int_day > 999 or int_month > 999 or int_year > 9999:
            return
            
        fake_match = FakeMatch((day, month, year))
        result = normalize_match(fake_match)
        
        # Should always produce YYYY-MM-DD format
        assert re.match(r'^\d{4}-\d{2}-\d{2}$', result)
        
    except (ValueError, TypeError):
        # Not numeric strings, skip
        pass
    except Exception as e:
        # Any other exception might be a bug
        print(f"Unexpected error with inputs: day={day}, month={month}, year={year}")
        raise


@given(
    year=st.integers(min_value=0, max_value=99),
    month=st.integers(min_value=0, max_value=99),  # Invalid months
    day=st.integers(min_value=0, max_value=99)  # Invalid days
)
def test_normalize_match_invalid_dates(day, month, year):
    """Test normalize_match with potentially invalid date components"""
    year_str = str(year).zfill(2)
    fake_match = FakeMatch((str(day), str(month), year_str))
    
    # normalize_match should still format them, validation happens elsewhere
    result = normalize_match(fake_match)
    
    # Check format is maintained even for invalid dates
    assert re.match(r'^\d{4}-\d{2}-\d{2}$', result)
    
    # Verify zero-padding
    parts = result.split('-')
    assert len(parts[1]) == 2  # month should be zero-padded
    assert len(parts[2]) == 2  # day should be zero-padded


@given(
    htmlstring=st.text(min_size=0, max_size=1000),
    min_year=st.integers(min_value=1900, max_value=2020),
    max_year=st.integers(min_value=2021, max_value=2100)
)
@settings(max_examples=50)  # Reduce examples for performance
def test_plausible_year_filter_boundaries(htmlstring, min_year, max_year):
    """Test plausible_year_filter respects year boundaries"""
    assume(min_year < max_year)
    
    # Create a simple pattern that might match years
    pattern = re.compile(r'\b(\d{4})\b')
    yearpat = re.compile(r'(\d{4})')
    
    min_date = datetime(min_year, 1, 1)
    max_date = datetime(max_year, 12, 31)
    
    result = plausible_year_filter(
        htmlstring,
        pattern=pattern,
        yearpat=yearpat,
        earliest=min_date,
        latest=max_date
    )
    
    # All returned years should be within boundaries
    for item in result:
        year_match = yearpat.search(item)
        if year_match:
            year = int(year_match[1])
            assert min_year <= year <= max_year, f"Year {year} outside boundaries [{min_year}, {max_year}]"


@given(
    date_str=st.text(min_size=0, max_size=50)
)
def test_is_valid_date_malformed_input(date_str):
    """Test is_valid_date with potentially malformed input"""
    min_date = datetime(2000, 1, 1)
    max_date = datetime(2030, 12, 31)
    
    result = is_valid_date(date_str, "%Y-%m-%d", min_date, max_date)
    
    # If it returns True, the date should be parseable
    if result:
        try:
            parsed = datetime.strptime(date_str, "%Y-%m-%d")
            assert min_date <= parsed <= max_date
        except ValueError:
            assert False, f"is_valid_date returned True for unparseable date: {date_str}"


@given(
    html_template=st.sampled_from([
        '<html><meta name="date" content="{}"/></html>',
        '<html><meta property="article:published" content="{}"/></html>',
        '<html><time datetime="{}">Published</time></html>',
    ]),
    date_content=st.text(min_size=0, max_size=30)
)
@settings(max_examples=100)
def test_find_date_with_invalid_content(html_template, date_content):
    """Test find_date with various invalid date contents"""
    html = html_template.format(date_content)
    
    result = find_date(
        html,
        min_date=datetime(2000, 1, 1),
        max_date=datetime(2030, 12, 31)
    )
    
    # If a date is returned, it should be valid
    if result is not None:
        try:
            parsed = datetime.strptime(result, "%Y-%m-%d")
            assert datetime(2000, 1, 1) <= parsed <= datetime(2030, 12, 31)
        except ValueError:
            assert False, f"find_date returned invalid date format: {result}"


@given(
    occurrences=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.integers(min_value=1, max_value=100),
        min_size=0,
        max_size=10
    )
)
def test_select_candidate_empty_input(occurrences):
    """Test select_candidate with various Counter inputs"""
    from htmldate.core import select_candidate
    
    counter = Counter(occurrences)
    catch = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
    yearpat = re.compile(r'(\d{4})')
    
    options = Extractor(
        False,  # extensive_search
        datetime(2030, 12, 31),  # max_date
        datetime(2000, 1, 1),  # min_date
        True,  # original_date
        "%Y-%m-%d"  # outputformat
    )
    
    # Should handle empty or invalid inputs gracefully
    result = select_candidate(counter, catch, yearpat, options)
    
    # Result should be None or a valid Match object
    if result is not None:
        assert hasattr(result, 'group') or hasattr(result, 'groups')


@given(
    year1=st.integers(min_value=0, max_value=99),
    year2=st.integers(min_value=0, max_value=99)
)
def test_normalize_match_year_edge_cases(year1, year2):
    """Test year normalization at century boundaries"""
    for year in [year1, year2]:
        year_str = str(year).zfill(2)
        fake_match = FakeMatch(("15", "06", year_str))
        
        result = normalize_match(fake_match)
        result_year = int(result.split('-')[0])
        
        # Verify the century assignment logic
        if year_str == "00":
            assert result_year == 2000
        elif year_str == "99":
            assert result_year == 1999
        else:
            if year_str[0] == '9':
                assert result_year == 1900 + year
            else:
                assert result_year == 2000 + year


if __name__ == "__main__":
    # Run edge case tests
    test_normalize_match_robustness()
    test_normalize_match_invalid_dates()
    test_plausible_year_filter_boundaries()
    test_is_valid_date_malformed_input()
    test_find_date_with_invalid_content()
    test_select_candidate_empty_input()
    test_normalize_match_year_edge_cases()
    print("All edge case tests defined successfully!")