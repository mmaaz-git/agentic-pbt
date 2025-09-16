"""Hypothesis test for Index equality bug"""

import tempfile
import sys
from hypothesis import given, strategies as st, settings

# Add the diskcache environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

from diskcache.persistent import Index

# Strategy for non-mapping types
non_mappings = st.one_of(
    st.integers(),
    st.floats(),
    st.text(),
    st.booleans(),
    st.none(),
    st.lists(st.integers()),
    st.tuples(st.integers()),
)

@given(
    st.dictionaries(st.text(min_size=1), st.integers(), max_size=5),
    non_mappings
)
@settings(max_examples=100)
def test_index_equality_with_non_mappings(items, non_mapping):
    """Index should return False when compared to non-mapping types, not raise TypeError"""
    with tempfile.TemporaryDirectory() as tmpdir:
        index = Index(tmpdir, items)
        
        # Test __eq__
        try:
            result_eq = (index == non_mapping)
            assert result_eq == False, f"Index == {type(non_mapping).__name__} should be False"
        except TypeError as e:
            print(f"BUG: Index.__eq__ raises TypeError with {type(non_mapping).__name__}: {e}")
            raise
        
        # Test __ne__
        try:
            result_ne = (index != non_mapping)
            assert result_ne == True, f"Index != {type(non_mapping).__name__} should be True"
        except TypeError as e:
            print(f"BUG: Index.__ne__ raises TypeError with {type(non_mapping).__name__}: {e}")
            raise

if __name__ == "__main__":
    print("Testing Index equality with non-mapping types...")
    try:
        test_index_equality_with_non_mappings()
        print("Test passed (no bug found)")
    except AssertionError as e:
        print(f"Test failed: {e}")
    except TypeError as e:
        print(f"BUG CONFIRMED: {e}")