"""Minimal test confirming the infinity/NaN JSON round-trip bug"""

import math
from hypothesis import given, strategies as st
from pydantic import BaseModel
import pytest


@given(
    special_float=st.sampled_from([float('inf'), float('-inf'), float('nan')])
)
def test_special_float_json_roundtrip_fails(special_float):
    """
    This test demonstrates that Pydantic fails to preserve special float values
    (inf, -inf, nan) through JSON serialization round-trip.
    
    The model_dump_json() method serializes these values as null,
    which cannot be deserialized back to the original float values.
    """
    
    class FloatModel(BaseModel):
        value: float
    
    # Create model with special float value
    original = FloatModel(value=special_float)
    
    # Serialize to JSON
    json_str = original.model_dump_json()
    
    # This should work but doesn't - special floats become null
    assert json_str == '{"value":null}'
    
    # Attempting to deserialize fails
    with pytest.raises(Exception) as exc_info:
        FloatModel.model_validate_json(json_str)
    
    # The error is about null not being a valid float
    assert "Input should be a valid number" in str(exc_info.value)


def test_dict_roundtrip_works():
    """For comparison, dict round-trip preserves special floats correctly"""
    
    class FloatModel(BaseModel):
        value: float
    
    for special in [float('inf'), float('-inf'), float('nan')]:
        original = FloatModel(value=special)
        dumped = original.model_dump()
        restored = FloatModel.model_validate(dumped)
        
        if math.isnan(special):
            assert math.isnan(restored.value)
        else:
            assert restored.value == special


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))