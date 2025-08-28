from hypothesis import given, strategies as st
from requests.hooks import dispatch_hook

# Test with the proposed fix: handle non-dict gracefully
def dispatch_hook_fixed(key, hooks, hook_data, **kwargs):
    """Fixed version that handles non-dict hooks gracefully"""
    hooks = hooks or {}
    
    # Fix: Check if hooks has get method (is dict-like)
    if not hasattr(hooks, 'get'):
        return hook_data
        
    hooks = hooks.get(key)
    if hooks:
        if hasattr(hooks, "__call__"):
            hooks = [hooks]
        for hook in hooks:
            _hook_data = hook(hook_data, **kwargs)
            if _hook_data is not None:
                hook_data = _hook_data
    return hook_data

# Property test to verify the fix maintains correct behavior
@given(
    hooks_type=st.sampled_from([None, {}, {"test": []}, {"test": lambda x, **k: x + 1}, "string", 123, [1,2,3]]),
    data=st.integers()
)
def test_fixed_version(hooks_type, data):
    """Test that fixed version handles all cases correctly"""
    try:
        # Original behavior for valid inputs
        if isinstance(hooks_type, (dict, type(None))):
            original = dispatch_hook("test", hooks_type, data)
            fixed = dispatch_hook_fixed("test", hooks_type, data)
            assert original == fixed, f"Behavior changed for valid input {hooks_type}"
        else:
            # Original crashes, fixed should return data unchanged
            fixed = dispatch_hook_fixed("test", hooks_type, data)
            assert fixed == data, f"Fixed version should return data unchanged for {type(hooks_type)}"
    except Exception as e:
        print(f"Unexpected error with {hooks_type}: {e}")
        raise

# Run the test
test_fixed_version()
print("All tests passed! Fix maintains backward compatibility while handling edge cases.")