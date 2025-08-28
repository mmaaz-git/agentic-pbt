#!/usr/bin/env /root/hypothesis-llm/envs/htmldate_env/bin/python
"""Property-based tests for htmldate.core module"""

import re
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from datetime import datetime
from hypothesis import given, strategies as st, settings, assume
import math

# Import target modules
from htmldate.core import normalize_match, compare_reference, find_date
from htmldate.validators import is_valid_date, is_valid_format, compare_values
from htmldate.utils import Extractor


# Property 1: normalize_match should handle match groups correctly
class FakeMatch:
    """Mock Match object for testing normalize_match"""
    def __init__(self, groups):
        self._groups = groups
    
    def groups(self):
        return self._groups


@given(
    day=st.integers(min_value=1, max_value=31),
    month=st.integers(min_value=1, max_value=12),
    year=st.one_of(
        st.integers(min_value=0, max_value=99),  # 2-digit years
        st.integers(min_value=1900, max_value=2099)  # 4-digit years
    )
)
def test_normalize_match_produces_valid_format(day, month, year):
    """Test that normalize_match produces dates in YYYY-MM-DD format"""
    year_str = str(year).zfill(2) if year < 100 else str(year)
    fake_match = FakeMatch((str(day), str(month), year_str))
    
    result = normalize_match(fake_match)
    
    # Check format: YYYY-MM-DD
    assert re.match(r'^\d{4}-\d{2}-\d{2}$', result)
    
    # Parse result to check components
    parts = result.split('-')
    assert len(parts) == 3
    assert len(parts[0]) == 4  # year
    assert len(parts[1]) == 2  # month
    assert len(parts[2]) == 2  # day


@given(
    day=st.integers(min_value=1, max_value=31),
    month=st.integers(min_value=1, max_value=12),
    year=st.integers(min_value=0, max_value=99)
)
def test_normalize_match_year_expansion_consistency(day, month, year):
    """Test that 2-digit year expansion is consistent with documented rules"""
    year_str = str(year).zfill(2)
    fake_match = FakeMatch((str(day), str(month), year_str))
    
    result = normalize_match(fake_match)
    result_year = int(result.split('-')[0])
    
    # Check documented expansion rule: 90s -> 1990s, 00s -> 2000s
    if year_str[0] == '9':
        assert result_year == 1900 + year
    else:
        assert result_year == 2000 + year


# Property 2: is_valid_date should correctly validate boundaries
@given(
    year=st.integers(min_value=1900, max_value=2100),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),  # Use 28 to avoid invalid dates
    min_year=st.integers(min_value=1900, max_value=2050),
    max_year=st.integers(min_value=1950, max_value=2100)
)
def test_is_valid_date_boundary_checking(year, month, day, min_year, max_year):
    """Test that is_valid_date correctly enforces date boundaries"""
    assume(min_year <= max_year)
    
    date_str = f"{year:04d}-{month:02d}-{day:02d}"
    min_date = datetime(min_year, 1, 1)
    max_date = datetime(max_year, 12, 31)
    
    result = is_valid_date(date_str, "%Y-%m-%d", min_date, max_date)
    
    # The function should return True only if the date is within boundaries
    date_obj = datetime(year, month, day)
    expected = min_date <= date_obj <= max_date
    
    assert result == expected


# Property 3: is_valid_format should accept valid formats and reject invalid ones
@given(
    format_str=st.text(min_size=1, max_size=20)
)
def test_is_valid_format_consistency(format_str):
    """Test that is_valid_format correctly validates format strings"""
    result = is_valid_format(format_str)
    
    # If it returns True, the format should work with strftime
    if result:
        assert '%' in format_str
        try:
            datetime(2017, 9, 1).strftime(format_str)
            valid = True
        except (ValueError, TypeError):
            valid = False
        assert valid
    else:
        # If it returns False, either no % or strftime should fail
        if '%' in format_str:
            try:
                datetime(2017, 9, 1).strftime(format_str)
                # If this succeeds, is_valid_format was wrong
                assert False, f"is_valid_format incorrectly rejected valid format: {format_str}"
            except (ValueError, TypeError):
                pass  # Expected


# Property 4: compare_values should maintain ordering invariant
@given(
    ref1=st.integers(min_value=0, max_value=2000000000),
    date_str=st.sampled_from([
        "2020-01-01", "2021-06-15", "2019-12-31", "2022-03-20"
    ]),
    original=st.booleans()
)
def test_compare_values_ordering(ref1, date_str, original):
    """Test that compare_values maintains correct ordering based on original flag"""
    options = Extractor(
        False,  # extensive_search
        datetime(2030, 12, 31),  # max_date
        datetime(2000, 1, 1),  # min_date
        original,  # original_date
        "%Y-%m-%d"  # outputformat
    )
    
    result = compare_values(ref1, date_str, options)
    
    # Convert date_str to timestamp for comparison
    timestamp = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())
    
    if ref1 == 0:
        assert result == timestamp
    elif original:
        # For original dates, we want the minimum (earliest)
        assert result == min(ref1, timestamp)
    else:
        # For non-original dates, we want the maximum (latest)
        assert result == max(ref1, timestamp)


# Property 5: find_date should respect output format
@given(
    html=st.just('<html><meta name="date" content="2021-06-15"/></html>'),
    output_format=st.sampled_from(["%Y-%m-%d", "%Y/%m/%d", "%d.%m.%Y", "%Y"])
)
def test_find_date_output_format(html, output_format):
    """Test that find_date returns dates in the requested format"""
    result = find_date(
        html,
        outputformat=output_format,
        min_date=datetime(2000, 1, 1),
        max_date=datetime(2030, 12, 31)
    )
    
    if result is not None:
        # Try parsing with the specified format
        try:
            if output_format == "%Y":
                # Special case for year-only format
                datetime.strptime(result, output_format).replace(month=1, day=1)
            else:
                datetime.strptime(result, output_format)
            format_valid = True
        except ValueError:
            format_valid = False
        
        assert format_valid, f"Result '{result}' doesn't match format '{output_format}'"


# Property 6: find_date should return dates within specified boundaries
@given(
    min_year=st.integers(min_value=2000, max_value=2020),
    max_year=st.integers(min_value=2021, max_value=2030)
)
def test_find_date_boundary_respect(min_year, max_year):
    """Test that find_date only returns dates within specified boundaries"""
    assume(min_year < max_year)
    
    # HTML with multiple dates
    html = f'''
    <html>
        <meta name="date" content="1999-01-01"/>
        <meta property="article:published" content="{min_year + 1}-06-15"/>
        <meta name="publication_date" content="2035-12-31"/>
    </html>
    '''
    
    result = find_date(
        html,
        min_date=datetime(min_year, 1, 1),
        max_date=datetime(max_year, 12, 31)
    )
    
    if result is not None:
        date_obj = datetime.strptime(result, "%Y-%m-%d")
        assert datetime(min_year, 1, 1) <= date_obj <= datetime(max_year, 12, 31)


if __name__ == "__main__":
    # Run all tests
    test_normalize_match_produces_valid_format()
    test_normalize_match_year_expansion_consistency()
    test_is_valid_date_boundary_checking()
    test_is_valid_format_consistency()
    test_compare_values_ordering()
    test_find_date_output_format()
    test_find_date_boundary_respect()
    print("All property tests defined successfully!")