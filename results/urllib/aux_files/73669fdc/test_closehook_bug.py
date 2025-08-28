import urllib.response
import io
from hypothesis import given, strategies as st


@given(
    num_hooks=st.integers(min_value=2, max_value=10),
    hook_raises=st.lists(st.booleans(), min_size=2, max_size=10)
)
def test_chained_closehooks_with_exceptions(num_hooks, hook_raises):
    """Test that chained closehooks with exceptions can cause issues."""
    # Ensure we have the right number of hook_raises values
    hook_raises = (hook_raises * num_hooks)[:num_hooks]
    
    call_order = []
    errors_raised = []
    
    def make_hook(n):
        def hook():
            call_order.append(n)
            if hook_raises[n]:
                error = RuntimeError(f"Hook {n} failed")
                errors_raised.append(error)
                raise error
        return hook
    
    fp = io.BytesIO(b"test")
    obj = fp
    
    # Chain multiple closehooks
    for i in range(num_hooks):
        obj = urllib.response.addclosehook(obj, make_hook(i))
    
    # Close and see what happens
    try:
        obj.close()
    except RuntimeError:
        pass
    
    # Check that all hooks were called in reverse order
    expected_order = list(range(num_hooks-1, -1, -1))
    
    # Due to exception handling, not all hooks might be called
    # But the ones that are called should be in reverse order
    for i in range(len(call_order)-1):
        assert call_order[i] > call_order[i+1], f"Hooks called out of order: {call_order}"
    
    # The file should be closed regardless
    assert fp.closed


@given(
    data=st.binary(),
    exception_type=st.sampled_from([KeyboardInterrupt, SystemExit, MemoryError])
)
def test_critical_exceptions_in_hook(data, exception_type):
    """Test that critical exceptions in hooks are properly propagated."""
    fp = io.BytesIO(data)
    
    def critical_hook():
        raise exception_type("Critical error")
    
    closehook = urllib.response.addclosehook(fp, critical_hook)
    
    try:
        closehook.close()
        assert False, f"Should have raised {exception_type.__name__}"
    except exception_type:
        pass
    
    # Even with critical exceptions, file should be closed
    assert fp.closed


@given(st.integers(min_value=1, max_value=100))
def test_closehook_recursion_limit(depth):
    """Test deep nesting of closehooks."""
    fp = io.BytesIO(b"test")
    obj = fp
    
    call_count = []
    
    def hook():
        call_count.append(1)
    
    # Create deeply nested closehooks
    for _ in range(depth):
        obj = urllib.response.addclosehook(obj, hook)
    
    obj.close()
    
    # All hooks should be called
    assert len(call_count) == depth
    assert fp.closed


@given(st.binary())
def test_hook_modifying_closehook_state(data):
    """Test hook that tries to modify closehook internal state."""
    fp = io.BytesIO(data)
    
    def malicious_hook(closehook_ref):
        # Try to prevent cleanup by modifying state
        closehook_ref[0].closehook = lambda: None
        closehook_ref[0].hookargs = ()
    
    closehook = urllib.response.addclosehook(fp, lambda: None)
    closehook_ref = [closehook]
    
    # Replace with malicious hook
    closehook.closehook = lambda: malicious_hook(closehook_ref)
    
    closehook.close()
    
    # Should still be closed
    assert closehook.closed
    assert fp.closed


if __name__ == "__main__":
    import pytest
    import sys
    
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))