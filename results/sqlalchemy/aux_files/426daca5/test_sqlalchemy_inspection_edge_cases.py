"""Edge case property-based tests for sqlalchemy.inspection module"""

from hypothesis import given, strategies as st, assume, settings, Phase
import sqlalchemy.inspection as si
from sqlalchemy import exc


@settings(max_examples=1000, phases=[Phase.generate])
@given(st.data())
def test_registry_modification_during_inspection(data):
    """Test modifying registry while inspecting"""
    # This tests a potential race condition or reentrancy issue
    
    class ModifyingInspector:
        def __init__(self):
            self.call_count = 0
            
        def __call__(self, obj):
            self.call_count += 1
            if self.call_count == 1:
                # On first call, try to modify the registry
                # This could potentially cause issues
                DummyType = type("Dummy", (), {})
                si._registrars[DummyType] = True
                # Clean up immediately
                del si._registrars[DummyType]
            return f"Inspected_{self.call_count}"
    
    TestType = type(f"ModifyTest_{id(data)}", (), {})
    inspector = ModifyingInspector()
    si._registrars[TestType] = inspector
    
    try:
        obj = TestType()
        result = si.inspect(obj)
        assert result == "Inspected_1"
        
        # Inspect again to see if state is maintained
        result2 = si.inspect(obj)
        assert result2 == "Inspected_2"
    finally:
        del si._registrars[TestType]


@settings(max_examples=1000)
@given(st.data())
def test_metaclass_inspection(data):
    """Test inspection with metaclasses"""
    # Create a metaclass
    class Meta(type):
        pass
    
    # Create a class with this metaclass
    TestClass = Meta(f"MetaTest_{id(data)}", (), {})
    
    # Register the metaclass
    si._registrars[Meta] = lambda x: f"Meta_{x.__class__.__name__}"
    
    try:
        # Create instance and inspect
        obj = TestClass()
        # The object's type is TestClass, and TestClass's type is Meta
        # But inspection looks at obj's type chain, not metaclass
        result = si.inspect(obj, raiseerr=False)
        # Should return None because we registered Meta (the metaclass)
        # not TestClass (the class)
        assert result is None
        
        # Now register TestClass itself
        si._registrars[TestClass] = lambda x: "TestClass"
        result = si.inspect(obj)
        assert result == "TestClass"
    finally:
        if Meta in si._registrars:
            del si._registrars[Meta]
        if TestClass in si._registrars:
            del si._registrars[TestClass]


@settings(max_examples=500)
@given(st.integers(min_value=-1000, max_value=1000))
def test_inspection_return_values(value):
    """Test that inspect correctly handles various return values"""
    # Test different return value types
    return_values = [
        value,  # Integer
        str(value),  # String
        [value],  # List
        {"key": value},  # Dict
        (value,),  # Tuple
        {value},  # Set
        None if value < 0 else value,  # Conditional None
    ]
    
    for i, ret_val in enumerate(return_values):
        TestType = type(f"ReturnTest_{i}_{value}", (), {})
        si._registrars[TestType] = lambda x, rv=ret_val: rv
        
        try:
            obj = TestType()
            if ret_val is None:
                # Should raise with raiseerr=True
                try:
                    si.inspect(obj, raiseerr=True)
                    assert False, "Should raise NoInspectionAvailable for None return"
                except exc.NoInspectionAvailable:
                    pass
                
                # Should return None with raiseerr=False
                result = si.inspect(obj, raiseerr=False)
                assert result is None
            else:
                result = si.inspect(obj)
                assert result == ret_val
        finally:
            del si._registrars[TestType]


@settings(max_examples=500)
@given(st.data())
def test_special_method_objects(data):
    """Test inspection of objects with special methods"""
    class SpecialObject:
        def __init__(self):
            self.value = data.draw(st.integers())
            
        def __eq__(self, other):
            # Potentially problematic equality
            if not isinstance(other, SpecialObject):
                return False
            return self.value == other.value
            
        def __hash__(self):
            return hash(self.value)
            
        def __repr__(self):
            return f"SpecialObject({self.value})"
    
    # Register the type
    si._registrars[SpecialObject] = lambda x: x
    
    try:
        obj1 = SpecialObject()
        obj2 = SpecialObject()
        
        result1 = si.inspect(obj1)
        result2 = si.inspect(obj2)
        
        # Should return the same objects
        assert result1 is obj1
        assert result2 is obj2
        
        # They should not be confused despite potential __eq__ issues
        if obj1 is not obj2:
            assert result1 is not result2
    finally:
        del si._registrars[SpecialObject]


@settings(max_examples=500)
@given(st.data())
def test_abstract_base_classes(data):
    """Test with abstract base classes"""
    from abc import ABC, abstractmethod
    
    class AbstractBase(ABC):
        @abstractmethod
        def method(self):
            pass
    
    class ConcreteImpl(AbstractBase):
        def method(self):
            return "implemented"
    
    # Register the abstract base
    si._registrars[AbstractBase] = lambda x: "AbstractBase"
    
    try:
        # Can't instantiate abstract class, so test with concrete
        obj = ConcreteImpl()
        result = si.inspect(obj)
        # Should find AbstractBase in MRO
        assert result == "AbstractBase"
    finally:
        del si._registrars[AbstractBase]


@settings(max_examples=500, deadline=1000)
@given(st.data())
def test_recursive_inspector(data):
    """Test inspector that calls inspect recursively"""
    class RecursiveInspector:
        def __init__(self):
            self.depth = 0
            self.max_depth = data.draw(st.integers(min_value=1, max_value=3))
            
        def __call__(self, obj):
            self.depth += 1
            if self.depth < self.max_depth:
                # Recursively inspect the same object
                # This shouldn't cause infinite recursion because
                # we're tracking depth
                result = si.inspect(obj)
                self.depth -= 1
                return f"Recursive_{result}"
            else:
                self.depth -= 1
                return f"Base_{self.depth}"
    
    TestType = type(f"RecursiveTest_{id(data)}", (), {})
    si._registrars[TestType] = RecursiveInspector()
    
    try:
        obj = TestType()
        result = si.inspect(obj)
        # Should have recursive structure
        assert "Base" in result or "Recursive" in result
    finally:
        del si._registrars[TestType]


@settings(max_examples=500)
@given(st.data())
def test_empty_mro_handling(data):
    """Test edge cases with MRO iteration"""
    # Normal Python classes always have at least object in MRO
    # But let's test the inspection logic thoroughly
    
    # Create a normal class
    TestClass = type("TestMRO", (), {})
    obj = TestClass()
    
    # Ensure object is in MRO
    assert object in TestClass.__mro__
    
    # Don't register anything
    # This tests the "else" clause after the for loop
    result = si.inspect(obj, raiseerr=False)
    assert result is None
    
    # Now register object itself - this is unusual but valid
    si._registrars[object] = lambda x: "object"
    
    try:
        # Now everything should be inspectable
        result = si.inspect(obj)
        assert result == "object"
        
        # Even built-in types
        result = si.inspect(42)
        assert result == "object"
        
        result = si.inspect("string")
        assert result == "object"
    finally:
        # Critical cleanup - don't leave object registered!
        del si._registrars[object]


if __name__ == "__main__":
    print("Running edge case tests...")
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])