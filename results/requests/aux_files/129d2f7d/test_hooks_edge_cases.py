import pytest
from hypothesis import given, strategies as st, assume, settings, example
from requests.hooks import default_hooks, dispatch_hook, HOOKS
import copy


# Test for exception handling in hooks
@given(
    hook_data=st.one_of(
        st.integers(),
        st.text(),
        st.lists(st.integers())
    )
)
def test_dispatch_hook_exception_handling(hook_data):
    """Test what happens when a hook raises an exception"""
    def raising_hook(data, **kwargs):
        raise ValueError("Hook error")
    
    hooks = {"test": raising_hook}
    
    # The current implementation doesn't catch exceptions
    # So this should propagate the exception
    with pytest.raises(ValueError, match="Hook error"):
        dispatch_hook("test", hooks, hook_data)


# Test with complex nested data structures
@given(
    nested_data=st.recursive(
        st.one_of(st.integers(), st.text(), st.none()),
        lambda children: st.one_of(
            st.lists(children, max_size=3),
            st.dictionaries(st.text(max_size=5), children, max_size=3)
        ),
        max_leaves=20
    )
)
def test_dispatch_hook_nested_structures(nested_data):
    """Test dispatch_hook with deeply nested data structures"""
    def identity_hook(data, **kwargs):
        return data
    
    hooks = {"test": identity_hook}
    result = dispatch_hook("test", hooks, nested_data)
    assert result == nested_data


# Test with special Python objects
@given(
    hook_data=st.one_of(
        st.sets(st.integers()),
        st.frozensets(st.integers()),
        st.tuples(st.integers(), st.text()),
        st.binary()
    )
)
def test_dispatch_hook_special_types(hook_data):
    """Test dispatch_hook with various Python types"""
    call_count = []
    
    def counting_hook(data, **kwargs):
        call_count.append(1)
        return data
    
    hooks = {"test": counting_hook}
    result = dispatch_hook("test", hooks, hook_data)
    
    assert result == hook_data
    assert len(call_count) == 1


# Test what happens with circular references
def test_dispatch_hook_circular_reference():
    """Test dispatch_hook with circular reference in data"""
    # Create a circular reference
    circular_list = [1, 2, 3]
    circular_list.append(circular_list)
    
    def identity_hook(data, **kwargs):
        return data
    
    hooks = {"test": identity_hook}
    result = dispatch_hook("test", hooks, circular_list)
    
    # Result should be the same circular structure
    assert result is circular_list


# Test with extremely long hook chains
@given(
    num_hooks=st.integers(min_value=100, max_value=1000),
    initial_value=st.integers(min_value=-1000, max_value=1000)
)
@settings(max_examples=10)  # Reduce examples for performance
def test_dispatch_hook_many_hooks(num_hooks, initial_value):
    """Test with a very long chain of hooks"""
    def increment_hook(data, **kwargs):
        return data + 1
    
    hooks = {"test": [increment_hook] * num_hooks}
    result = dispatch_hook("test", hooks, initial_value)
    
    assert result == initial_value + num_hooks


# Test hook mutation of the hooks dictionary itself
def test_dispatch_hook_mutating_hooks_dict():
    """Test what happens if a hook mutates the hooks dictionary"""
    hooks_dict = {}
    
    def evil_hook(data, **kwargs):
        # Try to modify the hooks dict during execution
        hooks_dict["test"] = []
        return data + 1
    
    hooks_dict["test"] = [evil_hook]
    result = dispatch_hook("test", hooks_dict, 0)
    
    # The hook should have been called before mutation
    assert result == 1
    # And the hooks dict should be mutated
    assert hooks_dict["test"] == []


# Test with hooks that return different types
@given(
    initial_data=st.integers()
)
def test_dispatch_hook_type_changes(initial_data):
    """Test hooks that change the data type"""
    def to_string(data, **kwargs):
        return str(data)
    
    def to_list(data, **kwargs):
        return [data]
    
    def to_dict(data, **kwargs):
        return {"value": data}
    
    hooks = {"test": [to_string, to_list, to_dict]}
    result = dispatch_hook("test", hooks, initial_data)
    
    # Should be: int -> str -> [str] -> {"value": [str]}
    assert result == {"value": [str(initial_data)]}


# Test with empty string key
@given(
    hook_data=st.integers()
)
def test_dispatch_hook_empty_key(hook_data):
    """Test dispatch_hook with empty string as key"""
    def modify_hook(data, **kwargs):
        return data * 2
    
    hooks = {"": modify_hook}
    result = dispatch_hook("", hooks, hook_data)
    assert result == hook_data * 2


# Test with None as hook in list
def test_dispatch_hook_none_in_list():
    """Test what happens with None in the hooks list"""
    def valid_hook(data, **kwargs):
        return data + 1
    
    # This should fail because None is not callable
    hooks = {"test": [valid_hook, None, valid_hook]}
    
    with pytest.raises(TypeError):
        dispatch_hook("test", hooks, 0)


# Test dispatch_hook with hooks being a non-dict
@given(
    hook_data=st.integers()
)
def test_dispatch_hook_invalid_hooks_type(hook_data):
    """Test dispatch_hook when hooks is not a dict or None"""
    # dispatch_hook expects hooks to be a dict or None
    # Let's test with other types
    
    # With a list (should work, returns original data)
    result = dispatch_hook("test", [], hook_data)
    assert result == hook_data
    
    # With a string (should work, returns original data)
    result = dispatch_hook("test", "not a dict", hook_data)
    assert result == hook_data
    
    # With an integer (should work, returns original data)
    result = dispatch_hook("test", 42, hook_data)
    assert result == hook_data


# Test with Unicode and special characters in keys
@given(
    key=st.text(min_size=1),
    hook_data=st.integers()
)
def test_dispatch_hook_unicode_keys(key, hook_data):
    """Test dispatch_hook with various Unicode keys"""
    def double_hook(data, **kwargs):
        return data * 2
    
    hooks = {key: double_hook}
    result = dispatch_hook(key, hooks, hook_data)
    assert result == hook_data * 2


# Test hook that returns a different object each time
class Counter:
    def __init__(self):
        self.count = 0
    
    def __call__(self, data, **kwargs):
        self.count += 1
        return self.count

def test_dispatch_hook_stateful_hook():
    """Test with a stateful hook"""
    counter = Counter()
    hooks = {"test": [counter, counter, counter]}
    
    result = dispatch_hook("test", hooks, "ignored")
    # Each call returns 1, 2, 3 respectively
    # The last one (3) should be the final result
    assert result == 3
    assert counter.count == 3