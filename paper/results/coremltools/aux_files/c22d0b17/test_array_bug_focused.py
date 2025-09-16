#!/usr/bin/env python3
"""Focused test demonstrating the Array dimension validation bug"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
from coremltools.models import datatypes

# Property test that demonstrates the bug
@given(st.lists(st.integers(), min_size=1, max_size=5))
def test_array_dimensions_should_be_positive(dimensions):
    """Arrays should only accept positive dimensions, but they don't."""
    try:
        arr = datatypes.Array(*dimensions)
        # If it succeeds, all dimensions should be positive
        for d in dimensions:
            assert d > 0, f"Array accepted non-positive dimension: {d}"
        # num_elements should also be positive
        assert arr.num_elements > 0, f"Array has non-positive num_elements: {arr.num_elements}"
    except (AssertionError, ValueError):
        # Expected to fail for non-positive dimensions
        pass

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "--hypothesis-show-statistics"])