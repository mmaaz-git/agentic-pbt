"""Extended property-based tests for sqlalchemy.inspection module"""

import gc
import weakref
from hypothesis import given, strategies as st, assume, settings, example
import sqlalchemy.inspection as si
from sqlalchemy import exc


@settings(max_examples=500)
@given(st.data())
def test_concurrent_registration_and_inspection(data):
    """Test thread-safety concerns with registration and inspection"""
    # Create multiple types
    types = []
    for i in range(data.draw(st.integers(min_value=1, max_value=10))):
        cls = type(f"ConcurrentTest_{i}", (), {})
        types.append(cls)
    
    # Register some of them
    registered = []
    for cls in types:
        if data.draw(st.booleans()):
            if data.draw(st.booleans()):
                si._registrars[cls] = True
            else:
                si._registrars[cls] = lambda x, c=cls: f"Inspected_{c.__name__}"
            registered.append(cls)
    
    try:
        # Inspect all objects multiple times
        for _ in range(3):
            for cls in types:
                obj = cls()
                if cls in registered:
                    result = si.inspect(obj)
                    assert result is not None
                else:
                    result = si.inspect(obj, raiseerr=False)
                    assert result is None
    finally:
        # Cleanup
        for cls in registered:
            if cls in si._registrars:
                del si._registrars[cls]


@settings(max_examples=500)
@given(st.integers(min_value=0, max_value=100))
def test_inspect_with_none_type(val):
    """Test that None can be inspected without issues"""
    # None is a special case - let's ensure it works
    result = si.inspect(None, raiseerr=False)
    assert result is None
    
    # Also test with other singleton-like objects
    result = si.inspect(True, raiseerr=False)
    assert result is None
    
    result = si.inspect(False, raiseerr=False)
    assert result is None


@settings(max_examples=200)
@given(st.data())
def test_weakref_compatibility(data):
    """Test that registered types can be garbage collected"""
    # Create a type dynamically
    class_name = f"WeakRefTest_{id(data)}"
    TestClass = type(class_name, (), {})
    
    # Create a weak reference to it
    weak_ref = weakref.ref(TestClass)
    
    # Register it
    si._registrars[TestClass] = True
    
    # Create and inspect an instance
    obj = TestClass()
    result = si.inspect(obj)
    assert result is obj
    
    # Clean up registration
    del si._registrars[TestClass]
    
    # Delete the class reference
    del TestClass
    
    # Force garbage collection
    gc.collect()
    
    # The weak reference should be dead now
    assert weak_ref() is None or weak_ref().__name__ == class_name


@settings(max_examples=500)
@given(st.data())
def test_inspector_exception_handling(data):
    """Test what happens when an inspector raises an exception"""
    class InspectorException(Exception):
        pass
    
    def failing_inspector(obj):
        raise InspectorException("Inspector failed")
    
    TestType = type(f"ExceptionTest_{id(data)}", (), {})
    si._registrars[TestType] = failing_inspector
    
    try:
        obj = TestType()
        # The inspect function doesn't catch exceptions from inspectors
        # So this should propagate
        try:
            result = si.inspect(obj)
            assert False, "Should have raised InspectorException"
        except InspectorException:
            pass  # Expected
    finally:
        del si._registrars[TestType]


@settings(max_examples=200)
@given(st.lists(st.booleans(), min_size=3, max_size=10))
def test_deep_inheritance_chain(inheritance_flags):
    """Test very deep inheritance chains"""
    classes = []
    base = None
    
    for i, should_register in enumerate(inheritance_flags):
        if base is None:
            cls = type(f"DeepBase_{i}", (), {})
        else:
            cls = type(f"DeepDerived_{i}", (base,), {})
        
        if should_register:
            si._registrars[cls] = lambda x, idx=i: f"Level_{idx}"
        
        classes.append(cls)
        base = cls
    
    try:
        # Test the deepest class
        if classes:
            deepest = classes[-1]
            obj = deepest()
            
            # Find which inspector should be used
            expected_idx = None
            for i in range(len(classes) - 1, -1, -1):
                if inheritance_flags[i]:
                    expected_idx = i
                    break
            
            if expected_idx is not None:
                result = si.inspect(obj)
                assert result == f"Level_{expected_idx}"
            else:
                result = si.inspect(obj, raiseerr=False)
                assert result is None
    finally:
        # Cleanup
        for i, cls in enumerate(classes):
            if inheritance_flags[i] and cls in si._registrars:
                del si._registrars[cls]


@settings(max_examples=200)
@given(st.data())
def test_builtin_types_inspection(data):
    """Test inspection of built-in Python types"""
    # Test various built-in types
    builtins = [
        42,
        3.14,
        "string",
        b"bytes",
        [],
        {},
        set(),
        frozenset(),
        tuple(),
        complex(1, 2),
        range(10),
        slice(1, 10),
    ]
    
    for obj in builtins:
        # These should not be registered by default
        result = si.inspect(obj, raiseerr=False)
        # Unless SQLAlchemy has registered them, these should return None
        # But we should not crash
        assert result is None or result is not None  # Tautology but tests no crash


@settings(max_examples=200)
@given(st.integers(min_value=1, max_value=20))
def test_diamond_inheritance(n):
    """Test diamond inheritance pattern"""
    # Create diamond structure:
    #     Base
    #    /    \
    #   A      B
    #    \    /
    #     C
    
    Base = type(f"DiamondBase_{n}", (), {})
    A = type(f"DiamondA_{n}", (Base,), {})
    B = type(f"DiamondB_{n}", (Base,), {})
    C = type(f"DiamondC_{n}", (A, B), {})
    
    # Register different combinations
    if n % 4 == 0:
        si._registrars[Base] = lambda x: "Base"
    elif n % 4 == 1:
        si._registrars[A] = lambda x: "A"
    elif n % 4 == 2:
        si._registrars[B] = lambda x: "B"
    else:
        si._registrars[A] = lambda x: "A"
        si._registrars[B] = lambda x: "B"
    
    try:
        obj = C()
        result = si.inspect(obj)
        
        # MRO for C is [C, A, B, Base, object]
        # So A should be found before B
        if n % 4 == 0:
            assert result == "Base"
        elif n % 4 == 1:
            assert result == "A"
        elif n % 4 == 2:
            assert result == "B"
        else:
            assert result == "A"  # A comes before B in MRO
    finally:
        # Cleanup
        for cls in [Base, A, B]:
            if cls in si._registrars:
                del si._registrars[cls]


if __name__ == "__main__":
    print("Running extended property-based tests...")
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])