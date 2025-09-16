import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/django-simple-history_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
from hypothesis import settings
import simple_history.utils as utils


# Test get_change_reason_from_object
@given(st.text())
def test_get_change_reason_with_attribute(reason):
    """
    Property: If an object has _change_reason attribute, 
    get_change_reason_from_object should return that exact value
    """
    class MockObject:
        def __init__(self, reason):
            self._change_reason = reason
    
    obj = MockObject(reason)
    result = utils.get_change_reason_from_object(obj)
    assert result == reason


@given(st.one_of(st.integers(), st.text(), st.lists(st.integers())))
def test_get_change_reason_without_attribute(value):
    """
    Property: If an object doesn't have _change_reason attribute,
    get_change_reason_from_object should return None
    """
    class MockObject:
        def __init__(self, val):
            self.some_other_attr = val
    
    obj = MockObject(value)
    result = utils.get_change_reason_from_object(obj)
    assert result is None


@given(st.one_of(st.none(), st.integers(), st.floats(), st.text()))
def test_get_change_reason_with_none_attribute(value):
    """
    Property: Even if _change_reason is None or any falsy value,
    it should return that exact value, not default to None
    """
    class MockObject:
        def __init__(self, reason):
            self._change_reason = reason
    
    obj = MockObject(value)
    result = utils.get_change_reason_from_object(obj)
    assert result == value


# Test edge cases with primitive types
@given(st.one_of(st.integers(), st.floats(), st.text(), st.lists(st.integers())))
def test_get_change_reason_on_primitives(value):
    """
    Property: get_change_reason_from_object should handle any object type
    gracefully and return None if no _change_reason attribute exists
    """
    result = utils.get_change_reason_from_object(value)
    assert result is None


# Test that the function doesn't modify the object
@given(st.text())
def test_get_change_reason_no_side_effects(reason):
    """
    Property: get_change_reason_from_object should not modify the object
    """
    class MockObject:
        def __init__(self, reason):
            self._change_reason = reason
            self.original_reason = reason
    
    obj = MockObject(reason)
    original_id = id(obj._change_reason)
    result = utils.get_change_reason_from_object(obj)
    
    assert obj._change_reason == obj.original_reason
    assert id(obj._change_reason) == original_id


# Test attribute name precision
@given(st.text())
def test_change_reason_attribute_name_precision(value):
    """
    Property: The function should only look for _change_reason attribute,
    not similar names like change_reason or _change_reasons
    """
    class MockObject:
        def __init__(self, val):
            self.change_reason = val  # without underscore
            self._change_reasons = val  # plural
            self._changeReason = val  # camelCase
    
    obj = MockObject(value)
    result = utils.get_change_reason_from_object(obj)
    assert result is None  # Should return None since _change_reason doesn't exist


# Test with special attribute values
@given(st.dictionaries(st.text(), st.integers()))
def test_change_reason_complex_types(value):
    """
    Property: _change_reason can be any type of value, including complex types
    """
    class MockObject:
        def __init__(self, reason):
            self._change_reason = reason
    
    obj = MockObject(value)
    result = utils.get_change_reason_from_object(obj)
    assert result == value
    assert result is value  # Should be the same object reference


# Test hasattr behavior consistency
@given(st.text(), st.text())
def test_change_reason_hasattr_consistency(reason, other_value):
    """
    Property: The function's behavior should be consistent with Python's hasattr
    """
    class MockObject:
        def __init__(self, reason):
            if reason is not None:
                self._change_reason = reason
    
    obj = MockObject(reason)
    result = utils.get_change_reason_from_object(obj)
    
    if hasattr(obj, '_change_reason'):
        assert result == reason
    else:
        assert result is None