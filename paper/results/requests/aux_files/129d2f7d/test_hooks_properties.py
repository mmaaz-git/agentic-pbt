import pytest
from hypothesis import given, strategies as st, assume, settings
from requests.hooks import default_hooks, dispatch_hook, HOOKS
import copy


# Test 1: default_hooks() invariant
def test_default_hooks_invariant():
    """default_hooks() should always return a dict with HOOKS keys and empty lists"""
    result = default_hooks()
    
    # Check it's a dictionary
    assert isinstance(result, dict)
    
    # Check all expected keys are present
    assert set(result.keys()) == set(HOOKS)
    
    # Check all values are empty lists
    for key, value in result.items():
        assert isinstance(value, list)
        assert len(value) == 0
    
    # Check that multiple calls create independent dictionaries
    result2 = default_hooks()
    assert result is not result2  # Different objects
    assert result == result2  # But equal content


# Test 2: dispatch_hook() identity property with no hooks
@given(
    key=st.text(),
    hook_data=st.one_of(
        st.none(),
        st.integers(),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )
)
def test_dispatch_hook_identity_no_hooks(key, hook_data):
    """With no hooks for a key, dispatch_hook should return original data unchanged"""
    # Test with None hooks
    result = dispatch_hook(key, None, hook_data)
    assert result is hook_data  # Should be the same object
    
    # Test with empty dict
    result = dispatch_hook(key, {}, hook_data)
    assert result is hook_data
    
    # Test with dict containing different key
    result = dispatch_hook(key, {"other_key": []}, hook_data)
    assert result is hook_data


# Test 3: dispatch_hook() single callable conversion
@given(
    hook_data=st.one_of(
        st.integers(),
        st.text(),
        st.lists(st.integers())
    )
)
def test_dispatch_hook_single_callable(hook_data):
    """A single callable should be converted to a list and work correctly"""
    modifications = []
    
    def single_hook(data, **kwargs):
        modifications.append(data)
        return f"modified_{data}"
    
    hooks = {"test": single_hook}
    result = dispatch_hook("test", hooks, hook_data)
    
    # Check hook was called
    assert len(modifications) == 1
    assert modifications[0] == hook_data
    
    # Check result was modified
    assert result == f"modified_{hook_data}"


# Test 4: dispatch_hook() sequential application
@given(
    initial_data=st.integers()
)
def test_dispatch_hook_sequential_application(initial_data):
    """Multiple hooks should be applied in sequence, each modifying the data"""
    def add_one(data, **kwargs):
        return data + 1
    
    def multiply_two(data, **kwargs):
        return data * 2
    
    def subtract_three(data, **kwargs):
        return data - 3
    
    hooks = {"math": [add_one, multiply_two, subtract_three]}
    result = dispatch_hook("math", hooks, initial_data)
    
    # Verify the operations were applied in order:
    # initial_data -> +1 -> *2 -> -3
    expected = ((initial_data + 1) * 2) - 3
    assert result == expected


# Test 5: dispatch_hook() None handling
@given(
    hook_data=st.one_of(
        st.integers(),
        st.text(),
        st.lists(st.integers())
    )
)
def test_dispatch_hook_none_handling(hook_data):
    """If a hook returns None, the original data should be preserved"""
    call_count = []
    
    def returns_none(data, **kwargs):
        call_count.append(1)
        return None
    
    def modifies_data(data, **kwargs):
        call_count.append(2)
        return f"modified_{data}"
    
    # Test single hook returning None
    hooks = {"test": returns_none}
    result = dispatch_hook("test", hooks, hook_data)
    assert result == hook_data  # Data unchanged
    assert len(call_count) == 1  # Hook was called
    
    # Test multiple hooks where first returns None
    call_count.clear()
    hooks = {"test": [returns_none, modifies_data]}
    result = dispatch_hook("test", hooks, hook_data)
    assert result == f"modified_{hook_data}"  # Second hook modifies
    assert call_count == [1, 2]  # Both hooks called
    
    # Test multiple hooks where second returns None
    call_count.clear()
    hooks = {"test": [modifies_data, returns_none]}
    result = dispatch_hook("test", hooks, hook_data)
    assert result == f"modified_{hook_data}"  # First modification preserved
    assert call_count == [2, 1]  # Both hooks called


# Test 6: dispatch_hook() kwargs passing
@given(
    hook_data=st.integers(),
    extra_value=st.integers()
)
def test_dispatch_hook_kwargs_passing(hook_data, extra_value):
    """dispatch_hook should pass kwargs to hook functions"""
    received_kwargs = []
    
    def hook_with_kwargs(data, **kwargs):
        received_kwargs.append(kwargs)
        return data + kwargs.get('extra', 0)
    
    hooks = {"test": hook_with_kwargs}
    result = dispatch_hook("test", hooks, hook_data, extra=extra_value)
    
    # Check kwargs were passed
    assert len(received_kwargs) == 1
    assert received_kwargs[0] == {'extra': extra_value}
    
    # Check result
    assert result == hook_data + extra_value


# Test 7: dispatch_hook() with list of hooks
@given(
    num_hooks=st.integers(min_value=0, max_value=10),
    initial_data=st.integers()
)
def test_dispatch_hook_list_of_hooks(num_hooks, initial_data):
    """dispatch_hook should handle a list of hooks correctly"""
    call_order = []
    
    def make_hook(i):
        def hook(data, **kwargs):
            call_order.append(i)
            return data + i
        return hook
    
    hook_list = [make_hook(i) for i in range(num_hooks)]
    hooks = {"test": hook_list}
    
    result = dispatch_hook("test", hooks, initial_data)
    
    # Check all hooks were called in order
    assert call_order == list(range(num_hooks))
    
    # Check final result
    expected = initial_data + sum(range(num_hooks))
    assert result == expected


# Test 8: dispatch_hook() with mutable data
@given(
    list_data=st.lists(st.integers(), min_size=1)
)
def test_dispatch_hook_mutable_data(list_data):
    """dispatch_hook should handle mutable data correctly"""
    original_data = list_data.copy()
    
    def mutating_hook(data, **kwargs):
        # Mutate the data
        data.append(999)
        return data  # Return the same object
    
    def checking_hook(data, **kwargs):
        # This hook sees the mutated data
        assert 999 in data
        return data
    
    hooks = {"test": [mutating_hook, checking_hook]}
    result = dispatch_hook("test", hooks, list_data)
    
    # Result should be the mutated list
    assert result is list_data  # Same object
    assert 999 in result  # Was mutated
    
    # Original list was also mutated (since it's the same object)
    assert 999 in list_data