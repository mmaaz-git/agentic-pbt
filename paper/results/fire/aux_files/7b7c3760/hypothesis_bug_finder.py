#!/usr/bin/env python3
"""Property-based test that discovers the Info() bug systematically."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import fire.inspectutils as inspectutils


# Strategy to generate objects with various __str__ behaviors
@st.composite  
def objects_with_str_behaviors(draw):
    behavior = draw(st.integers(0, 3))
    
    if behavior == 0:
        # Normal object
        class NormalObj:
            def __str__(self):
                return "normal"
        return NormalObj()
    
    elif behavior == 1:
        # Object that raises in __str__
        exception_type = draw(st.sampled_from([ValueError, TypeError, RuntimeError, AttributeError]))
        message = draw(st.text(min_size=1, max_size=50))
        
        class BadStrObj:
            def __str__(self):
                raise exception_type(message)
        return BadStrObj()
    
    elif behavior == 2:
        # Object with __str__ that returns non-string
        return_value = draw(st.one_of(st.integers(), st.floats(), st.none(), st.lists(st.integers())))
        
        class NonStringStr:
            def __str__(self):
                return return_value
        return NonStringStr()
    
    else:
        # Object with no __str__ (uses default)
        class NoStr:
            pass
        return NoStr()


@given(objects_with_str_behaviors())
@settings(max_examples=100)
def test_info_handles_all_objects(obj):
    """Info() should handle any object without crashing."""
    # This property states that Info should never crash, regardless of input
    try:
        info = inspectutils.Info(obj)
        # If successful, verify basic properties
        assert isinstance(info, dict)
        assert 'type_name' in info
        assert 'string_form' in info
    except Exception as e:
        # Any exception here is a bug!
        print(f"\nBUG FOUND: Info() crashed with {type(obj).__name__}")
        print(f"  Exception: {type(e).__name__}: {e}")
        raise


if __name__ == "__main__":
    print("Running property-based test to find Info() bugs...")
    try:
        test_info_handles_all_objects()
        print("Test completed - checking 100 examples")
    except Exception as e:
        print(f"\nTest failed! Bug confirmed.")
        print("\nTo reproduce:")
        print("```python")
        print("class BadStr:")
        print("    def __str__(self):")
        print("        raise ValueError('Cannot convert to string!')")
        print("")
        print("bad_obj = BadStr()")
        print("info = fire.inspectutils.Info(bad_obj)  # This will crash")
        print("```")