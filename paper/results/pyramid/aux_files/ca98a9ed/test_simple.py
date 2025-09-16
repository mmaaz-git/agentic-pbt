#!/usr/bin/env python3
"""Simple test runner for pyramid.events properties"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
from pyramid.events import BeforeRender
import traceback

print("Starting property-based testing of pyramid.events")
print("=" * 60)

# Test 1: BeforeRender dictionary behavior with edge cases
@given(
    system_dict=st.dictionaries(
        st.text(min_size=1), 
        st.one_of(st.text(), st.integers(), st.floats(allow_nan=False))
    ),
    rendering_val=st.one_of(st.none(), st.dictionaries(st.text(), st.text()))
)
@settings(max_examples=100)
def test_before_render_dict_behavior(system_dict, rendering_val):
    """BeforeRender should behave like a dictionary as documented"""
    event = BeforeRender(system_dict, rendering_val)
    
    # Should be a dict subclass
    assert isinstance(event, dict)
    
    # Should initialize with system dict values
    for key, value in system_dict.items():
        assert event[key] == value
    
    # Should preserve rendering_val
    assert event.rendering_val == rendering_val

# Test 2: Check BeforeRender with empty dict
@given(rendering_val=st.one_of(st.none(), st.dictionaries(st.text(), st.text())))
@settings(max_examples=50)
def test_before_render_empty_dict(rendering_val):
    """BeforeRender should handle empty system dict"""
    event = BeforeRender({}, rendering_val)
    assert len(event) == 0
    assert event.rendering_val == rendering_val
    
    # Should still support dict operations on empty dict
    event['new_key'] = 'new_value'
    assert event['new_key'] == 'new_value'

# Test 3: BeforeRender overwrite behavior
@given(
    key=st.text(min_size=1),
    old_value=st.text(),
    new_value=st.text()
)
@settings(max_examples=50)
def test_before_render_overwrite(key, old_value, new_value):
    """BeforeRender should allow overwriting existing keys"""
    if old_value == new_value:
        return  # Skip when values are the same
    
    system_dict = {key: old_value}
    event = BeforeRender(system_dict)
    assert event[key] == old_value
    
    # Overwrite should work
    event[key] = new_value
    assert event[key] == new_value

# Test 4: BeforeRender with special keys
@given(rendering_val=st.dictionaries(st.text(), st.text()))
@settings(max_examples=50)
def test_before_render_special_keys(rendering_val):
    """Test BeforeRender with keys that might conflict with dict internals"""
    special_keys = ['__class__', '__dict__', '__init__', 'rendering_val']
    system_dict = {key: f"value_{key}" for key in special_keys}
    
    try:
        event = BeforeRender(system_dict, rendering_val)
        
        # Check if special keys are handled correctly
        for key in special_keys:
            if key != 'rendering_val':  # rendering_val is an attribute, not a dict key
                assert event[key] == f"value_{key}"
    except Exception as e:
        print(f"Failed with special keys: {e}")
        raise

# Run the tests
tests = [
    test_before_render_dict_behavior,
    test_before_render_empty_dict,
    test_before_render_overwrite,
    test_before_render_special_keys
]

for test_func in tests:
    print(f"\nRunning: {test_func.__name__}")
    try:
        test_func()
        print(f"✓ {test_func.__name__} passed")
    except Exception as e:
        print(f"✗ {test_func.__name__} failed")
        print(f"  Error: {e}")
        traceback.print_exc()

print("\n" + "=" * 60)
print("Testing complete!")