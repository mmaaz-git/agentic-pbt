"""Property-based tests for pandas.tseries functions."""

import pandas.tseries.frequencies as freq
from hypothesis import given, strategies as st, assume, settings
import pytest


# Define valid frequency strings based on pandas documentation
# These are the codes that _maybe_coerce_freq can handle
VALID_FREQ_CODES = [
    "Y", "Y-JAN", "Y-FEB", "Y-MAR", "Y-APR", "Y-MAY", "Y-JUN",
    "Y-JUL", "Y-AUG", "Y-SEP", "Y-OCT", "Y-NOV", "Y-DEC",
    "Q", "Q-JAN", "Q-FEB", "Q-MAR", "Q-APR", "Q-MAY", "Q-JUN",
    "Q-JUL", "Q-AUG", "Q-SEP", "Q-OCT", "Q-NOV", "Q-DEC",
    "BQ", "BQ-JAN", "BQ-FEB", "BQ-MAR", "BQ-APR", "BQ-MAY", "BQ-JUN",
    "BQ-JUL", "BQ-AUG", "BQ-SEP", "BQ-OCT", "BQ-NOV", "BQ-DEC",
    "M", "BM",
    "W", "W-SUN", "W-MON", "W-TUE", "W-WED", "W-THU", "W-FRI", "W-SAT",
    "D", "B", "C",
    "h", "min", "s", "ms", "us", "ns"
]

freq_strategy = st.sampled_from(VALID_FREQ_CODES)


@given(source=freq_strategy, target=freq_strategy)
@settings(max_examples=1000)
def test_subperiod_superperiod_mutual_exclusion(source, target):
    """
    Property: is_subperiod and is_superperiod should be mutually exclusive
    for the same pair of frequencies (except when source == target).
    """
    is_sub = freq.is_subperiod(source, target)
    is_super = freq.is_superperiod(source, target)
    
    if source == target:
        # When frequencies are the same, both should be False
        assert not is_sub and not is_super
    else:
        # Both cannot be True at the same time
        assert not (is_sub and is_super)


@given(source=freq_strategy, target=freq_strategy)
@settings(max_examples=1000)
def test_subperiod_superperiod_symmetry(source, target):
    """
    Property: if A is a subperiod of B, then B should be a superperiod of A.
    """
    is_sub = freq.is_subperiod(source, target)
    is_super_inverse = freq.is_superperiod(target, source)
    
    # If source is a subperiod of target, target should be a superperiod of source
    assert is_sub == is_super_inverse


@given(a=freq_strategy, b=freq_strategy, c=freq_strategy)
@settings(max_examples=500)
def test_subperiod_transitivity(a, b, c):
    """
    Property: Transitivity - if A is subperiod of B and B is subperiod of C, 
    then A should be subperiod of C.
    """
    if freq.is_subperiod(a, b) and freq.is_subperiod(b, c):
        assert freq.is_subperiod(a, c)


@given(a=freq_strategy, b=freq_strategy, c=freq_strategy)
@settings(max_examples=500)
def test_superperiod_transitivity(a, b, c):
    """
    Property: Transitivity - if A is superperiod of B and B is superperiod of C,
    then A should be superperiod of C.
    """
    if freq.is_superperiod(a, b) and freq.is_superperiod(b, c):
        assert freq.is_superperiod(a, c)


# Test _quarter_months_conform mathematical properties
month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", 
               "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
month_strategy = st.sampled_from(month_names)


@given(month1=month_strategy, month2=month_strategy)
def test_quarter_months_conform_symmetry(month1, month2):
    """
    Property: _quarter_months_conform should be symmetric.
    """
    result1 = freq._quarter_months_conform(month1, month2)
    result2 = freq._quarter_months_conform(month2, month1)
    assert result1 == result2


@given(month=month_strategy)
def test_quarter_months_conform_reflexive(month):
    """
    Property: A month should always conform with itself.
    """
    assert freq._quarter_months_conform(month, month)


@given(month1=month_strategy, month2=month_strategy, month3=month_strategy)
def test_quarter_months_conform_transitivity(month1, month2, month3):
    """
    Property: If month1 conforms with month2, and month2 conforms with month3,
    then month1 should conform with month3.
    """
    if freq._quarter_months_conform(month1, month2) and freq._quarter_months_conform(month2, month3):
        assert freq._quarter_months_conform(month1, month3)


# Test period type checking functions
@given(rule=st.text(min_size=0, max_size=20))
def test_period_type_mutual_exclusion(rule):
    """
    Property: A rule cannot be multiple period types at once
    (annual, quarterly, monthly, weekly).
    """
    try:
        is_annual = freq._is_annual(rule)
        is_quarterly = freq._is_quarterly(rule) 
        is_monthly = freq._is_monthly(rule)
        is_weekly = freq._is_weekly(rule)
        
        # Count how many period types this rule matches
        type_count = sum([is_annual, is_quarterly, is_monthly, is_weekly])
        
        # A rule should match at most one period type
        assert type_count <= 1
    except (AttributeError, KeyError, ValueError):
        # Some invalid rules might cause exceptions, which is fine
        pass


# Test known hierarchical relationships
@given(source=st.sampled_from(["ns", "us", "ms", "s", "min", "h"]))
def test_known_time_hierarchy(source):
    """
    Property: Known time unit hierarchy should be preserved.
    ns -> us -> ms -> s -> min -> h
    """
    hierarchy = ["ns", "us", "ms", "s", "min", "h"]
    source_idx = hierarchy.index(source)
    
    for i, target in enumerate(hierarchy):
        target_idx = i
        if source_idx < target_idx:
            # source is finer than target, should be subperiod
            assert freq.is_subperiod(source, target)
            assert freq.is_superperiod(target, source)
        elif source_idx > target_idx:
            # source is coarser than target, should be superperiod
            assert freq.is_superperiod(source, target)
            assert freq.is_subperiod(target, source)
        else:
            # same period
            assert not freq.is_subperiod(source, target)
            assert not freq.is_superperiod(source, target)


# Test specific edge cases and boundaries
def test_none_handling():
    """Test that None is handled correctly."""
    assert not freq.is_subperiod(None, "D")
    assert not freq.is_subperiod("D", None)
    assert not freq.is_superperiod(None, "D")
    assert not freq.is_superperiod("D", None)
    assert not freq.is_subperiod(None, None)
    assert not freq.is_superperiod(None, None)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])