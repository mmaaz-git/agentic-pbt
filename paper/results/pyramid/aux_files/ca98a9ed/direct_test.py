#!/usr/bin/env python3
"""Direct test of pyramid.events without pytest"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.events import BeforeRender, NewRequest, NewResponse, subscriber
from hypothesis import given, strategies as st
import traceback

def run_test(test_name, test_func):
    """Helper to run a single test"""
    print(f"\nTesting: {test_name}")
    try:
        test_func()
        print(f"✓ PASSED: {test_name}")
        return True
    except AssertionError as e:
        print(f"✗ FAILED: {test_name}")
        print(f"  AssertionError: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ ERROR: {test_name}")
        print(f"  Exception: {e}")
        traceback.print_exc()
        return False

print("=" * 70)
print("Property-Based Testing of pyramid.events")
print("=" * 70)

results = []

# Test 1: BeforeRender with 'rendering_val' key conflict
def test_rendering_val_conflict():
    """Test what happens when system dict contains 'rendering_val' key"""
    system_dict = {'rendering_val': 'dict_value'}
    rendering_val_param = 'param_value'
    
    event = BeforeRender(system_dict, rendering_val_param)
    
    # The attribute should be the parameter
    assert event.rendering_val == 'param_value', \
        f"Expected rendering_val attribute to be 'param_value', got {event.rendering_val}"
    
    # The dict should contain the key
    assert event['rendering_val'] == 'dict_value', \
        f"Expected dict['rendering_val'] to be 'dict_value', got {event['rendering_val']}"

results.append(run_test("BeforeRender 'rendering_val' key conflict", test_rendering_val_conflict))

# Test 2: BeforeRender attribute vs dict key access
def test_attribute_vs_dict_access():
    """Test difference between attribute and dict key access"""
    system_dict = {'test_key': 'test_value'}
    event = BeforeRender(system_dict, rendering_val='rv_value')
    
    # Dict access should work for dict keys
    assert event['test_key'] == 'test_value'
    
    # Attribute access for rendering_val
    assert event.rendering_val == 'rv_value'
    
    # What if we set rendering_val as a dict key?
    event['rendering_val'] = 'new_dict_value'
    
    # Attribute should remain unchanged
    assert event.rendering_val == 'rv_value', \
        f"Attribute changed unexpectedly: {event.rendering_val}"
    
    # Dict key should be the new value
    assert event['rendering_val'] == 'new_dict_value'

results.append(run_test("BeforeRender attribute vs dict access", test_attribute_vs_dict_access))

# Test 3: subscriber with empty predicates
def test_subscriber_empty():
    """Test subscriber decorator with no arguments"""
    decorator = subscriber()
    assert decorator.ifaces == ()
    assert decorator.predicates == {}
    assert decorator.depth == 0
    assert decorator.category == 'pyramid'

results.append(run_test("subscriber with empty arguments", test_subscriber_empty))

# Test 4: BeforeRender mutation affects original dict
def test_before_render_mutation():
    """Test if BeforeRender mutates or copies the system dict"""
    original = {'key1': 'value1'}
    event = BeforeRender(original)
    
    # Modify through event
    event['key2'] = 'value2'
    
    # Check if original is affected
    if 'key2' in original:
        print("  Note: BeforeRender modifies the original dict")
    else:
        print("  Note: BeforeRender doesn't modify the original dict")
    
    # This is not necessarily a bug, just interesting behavior to note

results.append(run_test("BeforeRender mutation behavior", test_before_render_mutation))

# Test 5: NewResponse with None values
def test_new_response_none():
    """Test NewResponse with None request or response"""
    # With None request
    event1 = NewResponse(None, {'response': 'data'})
    assert event1.request is None
    assert event1.response == {'response': 'data'}
    
    # With None response
    event2 = NewResponse({'request': 'data'}, None)
    assert event2.request == {'request': 'data'}
    assert event2.response is None
    
    # Both None
    event3 = NewResponse(None, None)
    assert event3.request is None
    assert event3.response is None

results.append(run_test("NewResponse with None values", test_new_response_none))

# Test 6: BeforeRender subclass behavior
def test_before_render_isinstance():
    """Test BeforeRender's relationship with dict"""
    event = BeforeRender({'key': 'value'})
    
    assert isinstance(event, dict)
    assert isinstance(event, BeforeRender)
    assert issubclass(BeforeRender, dict)

results.append(run_test("BeforeRender inheritance", test_before_render_isinstance))

# Test 7: BeforeRender with large dictionary using Hypothesis
@given(
    system_dict=st.dictionaries(
        st.text(min_size=1, max_size=100),
        st.text(),
        min_size=100,
        max_size=100
    )
)
def test_large_dict_property(system_dict):
    event = BeforeRender(system_dict)
    assert len(event) == len(system_dict)
    for key in system_dict:
        assert event[key] == system_dict[key]

# Run the Hypothesis test manually
print("\nTesting: BeforeRender with large dictionaries (Hypothesis)")
try:
    test_large_dict_property()
    print("✓ PASSED: BeforeRender with large dictionaries")
    results.append(True)
except Exception as e:
    print(f"✗ FAILED: BeforeRender with large dictionaries")
    print(f"  Error: {e}")
    traceback.print_exc()
    results.append(False)

# Summary
print("\n" + "=" * 70)
passed = sum(results)
total = len(results)
print(f"Test Results: {passed}/{total} passed")

if passed == total:
    print("✓ All tests passed!")
else:
    print(f"✗ {total - passed} test(s) failed")

print("=" * 70)