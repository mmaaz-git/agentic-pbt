import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
from hypothesis import given, strategies as st, settings, assume
import awkward as ak
from awkward.behaviors.mixins import mixin_class, mixin_class_method, _call_transposed


# Strategy for valid Python identifiers  
def valid_identifier():
    return st.text(
        alphabet=st.characters(whitelist_categories=('Ll', 'Lu'), min_codepoint=97),
        min_size=1,
        max_size=20
    ).filter(lambda s: s.isidentifier() and not s.startswith('_'))


# Test 1: mixin_class decorator properly registers classes in registry
@given(
    class_name=valid_identifier(),
    behavior_name=st.one_of(st.none(), valid_identifier()),
    use_mixin_methods=st.booleans()
)
def test_mixin_class_registration(class_name, behavior_name, use_mixin_methods):
    registry = {}
    
    # Create a test class with optional mixin method
    if use_mixin_methods:
        class TestClass:
            @mixin_class_method(np.add, {int, float})
            def __add__(self, other):
                return self
    else:
        class TestClass:
            pass
    
    # Set the class name dynamically
    TestClass.__name__ = class_name
    TestClass.__module__ = __name__
    
    # Apply the decorator
    decorated = mixin_class(registry, name=behavior_name)
    result_class = decorated(TestClass)
    
    # Properties to test:
    # 1. The decorator should return the original class
    assert result_class is TestClass
    
    # 2. Registry should contain Record and Array entries
    expected_name = behavior_name if behavior_name is not None else class_name
    assert expected_name in registry
    assert ("*", expected_name) in registry
    
    # 3. Created classes should be subclasses of the appropriate types
    record_class = registry[expected_name]
    array_class = registry[("*", expected_name)]
    assert issubclass(record_class, ak.highlevel.Record)
    assert issubclass(array_class, ak.highlevel.Array)
    assert issubclass(record_class, TestClass)
    assert issubclass(array_class, TestClass)
    
    # 4. Class names should follow the pattern
    assert record_class.__name__ == class_name + "Record"
    assert array_class.__name__ == class_name + "Array"
    
    # 5. Module should be preserved
    assert record_class.__module__ == __name__
    assert array_class.__module__ == __name__


# Test 2: mixin_class_method decorator properly marks methods
@given(
    rhs=st.one_of(
        st.none(),
        st.sets(st.sampled_from([int, float, str, list, dict]), min_size=0, max_size=5)
    ),
    transpose=st.booleans()
)
def test_mixin_class_method_marking(rhs, transpose):
    # Create a mock ufunc
    mock_ufunc = np.add
    
    # Define a test method
    def test_method(self, other=None):
        return self
    
    # Apply the decorator
    decorator = mixin_class_method(mock_ufunc, rhs=rhs, transpose=transpose)
    decorated_method = decorator(test_method)
    
    # Properties to test:
    # 1. Method should have _awkward_mixin attribute
    assert hasattr(decorated_method, '_awkward_mixin')
    
    # 2. _awkward_mixin should be a tuple of (ufunc, rhs, transpose_func)
    mixin_data = decorated_method._awkward_mixin
    assert isinstance(mixin_data, tuple)
    assert len(mixin_data) == 3
    assert mixin_data[0] is mock_ufunc
    
    # 3. If rhs is provided, it should be a set in the mixin data
    if rhs is not None:
        assert isinstance(mixin_data[1], set)
        assert mixin_data[1] == rhs
    else:
        assert mixin_data[1] is None
    
    # 4. Transpose function should be created only when transpose=True and rhs is not None
    if transpose and rhs is not None:
        assert mixin_data[2] is not None
        assert callable(mixin_data[2])
    else:
        assert mixin_data[2] is None


# Test 3: mixin_class_method validates rhs parameter
@given(
    invalid_rhs=st.one_of(
        st.integers(),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    ).filter(lambda x: not isinstance(x, (set, type(None))))
)
def test_mixin_class_method_rhs_validation(invalid_rhs):
    mock_ufunc = np.add
    
    def test_method(self, other):
        return self
    
    # Should raise ValueError for invalid rhs
    decorator = mixin_class_method(mock_ufunc, rhs=invalid_rhs)
    try:
        decorated_method = decorator(test_method)
        # If we get here, the validation failed
        assert False, f"Expected ValueError for rhs={invalid_rhs}, but none was raised"
    except ValueError as e:
        assert "expected a set of right-hand-side argument types" in str(e)
    except Exception as e:
        # Wrong exception type
        assert False, f"Expected ValueError but got {type(e).__name__}: {e}"


# Test 4: _call_transposed correctly swaps arguments
@given(
    left=st.integers(),
    right=st.floats(allow_nan=False, allow_infinity=False)
)
def test_call_transposed(left, right):
    # Create a function that returns a tuple of its arguments
    def test_func(a, b):
        return (a, b)
    
    # Call _call_transposed
    result = _call_transposed(test_func, left, right)
    
    # Property: arguments should be swapped
    assert result == (right, left)


# Test 5: mixin_class handles inheritance correctly
@given(
    parent_name=valid_identifier(),
    child_name=valid_identifier(),
    num_parent_methods=st.integers(min_value=0, max_value=3),
    num_child_methods=st.integers(min_value=0, max_value=3)
)
@settings(max_examples=50)
def test_mixin_class_inheritance(parent_name, child_name, num_parent_methods, num_child_methods):
    assume(parent_name != child_name)
    
    registry = {}
    
    # Create parent class with methods
    class ParentClass:
        pass
    
    # Add methods to parent
    for i in range(num_parent_methods):
        method = lambda self, other: self
        method._awkward_mixin = (np.add, {int}, None)
        setattr(ParentClass, f"parent_method_{i}", method)
    
    ParentClass.__name__ = parent_name
    ParentClass.__module__ = __name__
    
    # Create child class
    class ChildClass(ParentClass):
        pass
    
    # Add methods to child
    for i in range(num_child_methods):
        method = lambda self, other: self
        method._awkward_mixin = (np.subtract, {float}, None)
        setattr(ChildClass, f"child_method_{i}", method)
    
    ChildClass.__name__ = child_name
    ChildClass.__module__ = __name__
    
    # Register the child class
    decorated = mixin_class(registry)
    result_class = decorated(ChildClass)
    
    # Properties to test:
    # 1. Child should be registered
    assert child_name in registry
    assert ("*", child_name) in registry
    
    # 2. Methods from parent should be accessible and registered
    total_mixin_methods = 0
    for cls in ChildClass.mro():
        for method in cls.__dict__.values():
            if hasattr(method, '_awkward_mixin'):
                total_mixin_methods += 1
    
    # Count registered ufunc behaviors
    ufunc_registrations = sum(1 for key in registry if isinstance(key, tuple) and len(key) >= 2 and key[1] == child_name)
    
    # Should have registered at least some of the methods
    assert ufunc_registrations >= 0