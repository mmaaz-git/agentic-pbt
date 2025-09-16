import functools
from typing import Union, Generic, TypeVar, List, Dict

from hypothesis import given, strategies as st, assume


def test_generic_types():
    """Test behavior with generic types."""
    T = TypeVar('T')
    
    class Container(Generic[T]):
        def __init__(self, value: T):
            self.value = value
    
    @functools.singledispatch
    def process(obj):
        return "default"
    
    # Try to register for generic type
    @process.register(Container)
    def _(obj):
        return f"container with {obj.value}"
    
    # Test with different type parameters
    int_container = Container(42)
    str_container = Container("hello")
    
    result1 = process(int_container)
    result2 = process(str_container)
    
    # Both should use the Container handler regardless of type parameter
    assert result1 == "container with 42"
    assert result2 == "container with hello"


def test_diamond_inheritance():
    """Test behavior with diamond inheritance pattern."""
    
    class A:
        pass
    
    class B(A):
        pass
    
    class C(A):
        pass
    
    class D(B, C):  # Diamond inheritance
        pass
    
    @functools.singledispatch
    def func(obj):
        return "default"
    
    @func.register(A)
    def _(obj):
        return "A"
    
    @func.register(B)
    def _(obj):
        return "B"
    
    @func.register(C)
    def _(obj):
        return "C"
    
    # Test D which inherits from both B and C
    d_instance = D()
    result = func(d_instance)
    
    # Should follow MRO - B comes before C in class D(B, C)
    assert result == "B"
    
    # Verify MRO
    assert D.__mro__[1] == B
    assert D.__mro__[2] == C


def test_metaclass_instances():
    """Test dispatch on metaclass instances."""
    
    class Meta(type):
        pass
    
    class ClassWithMeta(metaclass=Meta):
        pass
    
    @functools.singledispatch
    def process(obj):
        return "default"
    
    # Register for the metaclass itself
    @process.register(Meta)
    def _(obj):
        return "metaclass"
    
    # Register for instances of classes with that metaclass
    @process.register(ClassWithMeta)
    def _(obj):
        return "instance"
    
    # Test with the class itself (which is an instance of Meta)
    result1 = process(ClassWithMeta)
    
    # Test with an instance of the class
    instance = ClassWithMeta()
    result2 = process(instance)
    
    assert result1 == "metaclass"
    assert result2 == "instance"


def test_bool_int_relationship():
    """Test that bool (subclass of int) is handled correctly."""
    
    @functools.singledispatch
    def func(x):
        return "default"
    
    @func.register(int)
    def _(x):
        return f"int: {x}"
    
    # bool is a subclass of int
    assert issubclass(bool, int)
    
    # Test with bool values
    assert func(True) == "int: True"
    assert func(False) == "int: False"
    
    # Now register specific bool handler
    @func.register(bool)
    def _(x):
        return f"bool: {x}"
    
    # Should now use bool handler
    assert func(True) == "bool: True"
    assert func(False) == "bool: False"
    
    # int should still use int handler
    assert func(42) == "int: 42"


def test_class_decorator_syntax():
    """Test the class decorator syntax for registration."""
    
    @functools.singledispatch
    def process(obj):
        return "default"
    
    # Use decorator syntax directly on class
    @process.register
    class Handler:
        def __init__(self, value):
            self.value = value
    
    # This should have registered Handler class
    instance = Handler(42)
    
    # When using class decorator, the class itself becomes the handler
    # and process(instance) should return the instance
    result = process(instance)
    
    # The decorator returns the class unchanged
    assert result is instance


def test_functools_singledispatchmethod():
    """Test singledispatchmethod for methods."""
    
    class Processor:
        @functools.singledispatchmethod
        def process(self, arg):
            return f"default: {arg}"
        
        @process.register
        def _(self, arg: int):
            return f"int: {arg}"
        
        @process.register
        def _(self, arg: str):
            return f"str: {arg}"
    
    p = Processor()
    
    assert p.process(42) == "int: 42"
    assert p.process("hello") == "str: hello"
    assert p.process(3.14) == "default: 3.14"


@given(st.booleans())
def test_bool_dispatch_with_explicit_registration(bool_val):
    """Property test for bool dispatch behavior."""
    
    @functools.singledispatch
    def func(x):
        return "default"
    
    @func.register(bool)
    def bool_handler(x):
        return "bool"
    
    @func.register(int)
    def int_handler(x):
        return "int"
    
    # Property: bool values should use bool handler when bool is registered first
    assert func(bool_val) == "bool"
    assert func(1) == "int"
    assert func(0) == "int"
    
    # But True == 1 and False == 0
    assert True == 1
    assert False == 0
    
    # However dispatch should be based on type, not value
    assert type(bool_val) == bool
    assert type(1) == int


def test_multiple_inheritance_mro():
    """Test complex MRO scenarios."""
    
    class A: pass
    class B: pass
    class C(A): pass
    class D(B): pass
    class E(C, D): pass  # Multiple inheritance
    
    @functools.singledispatch
    def func(obj):
        return "default"
    
    @func.register(A)
    def _(obj):
        return "A"
    
    @func.register(B)
    def _(obj):
        return "B"
    
    # E inherits from C (which inherits from A) and D (which inherits from B)
    # MRO: E -> C -> A -> D -> B -> object
    e = E()
    result = func(e)
    
    # Should use A handler (via C) because C comes before D in MRO
    assert result == "A"
    
    # Verify our MRO understanding
    mro = E.__mro__
    a_index = mro.index(A)
    b_index = mro.index(B)
    assert a_index < b_index


def test_registration_with_abstract_property():
    """Test with abstract base classes and properties."""
    from abc import ABC, abstractmethod
    
    class AbstractBase(ABC):
        @abstractmethod
        def method(self):
            pass
    
    class Concrete(AbstractBase):
        def method(self):
            return "concrete"
    
    @functools.singledispatch
    def process(obj):
        return "default"
    
    @process.register(AbstractBase)
    def _(obj):
        return "abstract"
    
    # Can't instantiate AbstractBase directly
    # But Concrete instances should use the AbstractBase handler
    c = Concrete()
    assert process(c) == "abstract"


def test_weakref_behavior():
    """Test if singledispatch handles weak references correctly."""
    import weakref
    
    @functools.singledispatch
    def func(obj):
        return "default"
    
    @func.register(int)
    def _(obj):
        return "int"
    
    # Create an object that can be weakly referenced
    class Dummy:
        pass
    
    obj = Dummy()
    weak = weakref.ref(obj)
    
    # Weak reference itself should get default
    assert func(weak) == "default"
    
    # Dereferenced should also get default (it's a Dummy instance)
    assert func(weak()) == "default"