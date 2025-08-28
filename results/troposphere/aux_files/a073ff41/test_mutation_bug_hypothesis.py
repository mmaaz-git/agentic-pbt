#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages/')

from hypothesis import given, strategies as st, settings
import troposphere.forecast as forecast

# Test the mutation bug with Hypothesis

@st.composite
def attribute_lists(draw):
    """Generate lists of AttributesItems"""
    num_attrs = draw(st.integers(min_value=1, max_value=5))
    return [
        forecast.AttributesItems(
            AttributeName=f"attr_{i}",
            AttributeType=draw(st.sampled_from(["string", "integer", "float", "timestamp"]))
        )
        for i in range(num_attrs)
    ]

@given(attribute_lists())
@settings(max_examples=50)
def test_schema_mutation_property(attrs):
    """Property: Schema should not be affected by mutations to the original list"""
    # Create a copy of the original list for comparison
    original_length = len(attrs)
    
    # Create Schema with the list
    schema = forecast.Schema(Attributes=attrs)
    
    # Get the initial state
    dict_before = schema.to_dict()
    attrs_before = dict_before["Attributes"]
    
    # Mutate the original list
    attrs.append(
        forecast.AttributesItems(AttributeName="mutated", AttributeType="string")
    )
    
    # Get the state after mutation
    dict_after = schema.to_dict()
    attrs_after = dict_after["Attributes"]
    
    # The Schema should not be affected by the mutation
    # Expected: len(attrs_after) == original_length
    # Actual: len(attrs_after) == original_length + 1 (BUG!)
    assert len(attrs_after) == original_length, f"Schema was mutated! Before: {len(attrs_before)}, After: {len(attrs_after)}"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])