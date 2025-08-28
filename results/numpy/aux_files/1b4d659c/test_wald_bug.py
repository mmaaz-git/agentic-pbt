import numpy as np
import numpy.random
from hypothesis import given, strategies as st, settings

@given(
    st.floats(min_value=1e8, max_value=1e15),
    st.floats(min_value=0.1, max_value=10.0)
)
@settings(max_examples=50)
def test_wald_negative_values(mean, scale):
    """Wald distribution should never produce negative values"""
    samples = numpy.random.wald(mean, scale, size=1000)
    negative_count = sum(s < 0 for s in samples)
    
    if negative_count > 0:
        print(f"\nFound negative values!")
        print(f"  mean={mean}, scale={scale}")
        print(f"  {negative_count}/1000 negative values")
        print(f"  Min value: {samples.min()}")
        print(f"  Example negatives: {samples[samples < 0][:5]}")
        
    assert all(s >= 0 for s in samples), f"Found {negative_count} negative values with mean={mean}, scale={scale}"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])