"""Test the protocol definitions themselves."""

from hypothesis import given, strategies as st
from troposphere.type_defs.protocols import JSONreprProtocol, ToDictProtocol
from troposphere.type_defs.compat import Protocol
from typing import Dict, Any
import inspect


def test_protocol_inheritance():
    """Test that the protocols properly inherit from Protocol."""
    assert issubclass(JSONreprProtocol, Protocol)
    assert issubclass(ToDictProtocol, Protocol)


def test_protocol_methods_defined():
    """Test that protocols define the expected methods."""
    # Check JSONreprProtocol
    json_methods = [name for name, _ in inspect.getmembers(JSONreprProtocol, inspect.isfunction) 
                    if not name.startswith('_')]
    assert 'JSONrepr' in json_methods
    
    # Check ToDictProtocol  
    dict_methods = [name for name, _ in inspect.getmembers(ToDictProtocol, inspect.isfunction)
                    if not name.startswith('_')]
    assert 'to_dict' in dict_methods


def test_protocol_implementation_check():
    """Test that we can check if a class implements the protocols."""
    
    class CorrectToDict:
        def to_dict(self) -> Dict[str, Any]:
            return {}
    
    class CorrectJSONrepr:
        def JSONrepr(self, *args, **kwargs) -> Dict[str, Any]:
            return {}
    
    class WrongMethod:
        def wrong_method(self):
            return {}
    
    # Check that classes with correct methods are recognized
    obj1 = CorrectToDict()
    obj2 = CorrectJSONrepr()
    obj3 = WrongMethod()
    
    assert hasattr(obj1, 'to_dict')
    assert callable(getattr(obj1, 'to_dict'))
    
    assert hasattr(obj2, 'JSONrepr')
    assert callable(getattr(obj2, 'JSONrepr'))
    
    assert not hasattr(obj3, 'to_dict')
    assert not hasattr(obj3, 'JSONrepr')


def test_protocol_signatures():
    """Test the method signatures of the protocols."""
    # Get the signatures
    jsonrepr_sig = inspect.signature(JSONreprProtocol.JSONrepr)
    to_dict_sig = inspect.signature(ToDictProtocol.to_dict)
    
    # JSONrepr accepts *args and **kwargs
    params = list(jsonrepr_sig.parameters.keys())
    assert 'self' in params
    # Should have VAR_POSITIONAL and VAR_KEYWORD parameters
    var_positional = any(p.kind == inspect.Parameter.VAR_POSITIONAL 
                        for p in jsonrepr_sig.parameters.values())
    var_keyword = any(p.kind == inspect.Parameter.VAR_KEYWORD 
                     for p in jsonrepr_sig.parameters.values())
    assert var_positional
    assert var_keyword
    
    # to_dict only takes self
    params = list(to_dict_sig.parameters.keys())
    assert params == ['self']
    
    # Both should return Dict[str, Any]
    assert 'Dict[str, Any]' in str(jsonrepr_sig.return_annotation)
    assert 'Dict[str, Any]' in str(to_dict_sig.return_annotation)


def test_protocol_methods_raise_not_implemented():
    """Test that protocol methods raise NotImplementedError."""
    # We can't instantiate protocols directly, but we can test the methods
    
    class TestJSONrepr(JSONreprProtocol):
        pass
    
    class TestToDict(ToDictProtocol):
        pass
    
    # These should inherit the NotImplementedError behavior
    obj1 = TestJSONrepr()
    obj2 = TestToDict()
    
    try:
        obj1.JSONrepr()
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass
    
    try:
        obj2.to_dict()
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass


class PolymorphicImplementation:
    """A class that implements both protocols."""
    def to_dict(self) -> Dict[str, Any]:
        return {'source': 'to_dict'}
    
    def JSONrepr(self, *args, **kwargs) -> Dict[str, Any]:
        return {'source': 'JSONrepr'}


def test_dual_protocol_implementation():
    """Test that a class can implement both protocols."""
    obj = PolymorphicImplementation()
    
    # Should have both methods
    assert hasattr(obj, 'to_dict')
    assert hasattr(obj, 'JSONrepr')
    
    # Both should be callable
    assert callable(obj.to_dict)
    assert callable(obj.JSONrepr)
    
    # Should return different values
    assert obj.to_dict() == {'source': 'to_dict'}
    assert obj.JSONrepr() == {'source': 'JSONrepr'}
    
    # JSONrepr should accept arguments
    assert obj.JSONrepr(1, 2, x=3) == {'source': 'JSONrepr'}


@given(st.dictionaries(st.text(), st.integers()))
def test_protocol_return_type_variance(data):
    """Test that implementations can return any dict-like structure."""
    
    class FlexibleToDict:
        def __init__(self, data):
            self.data = data
        
        def to_dict(self) -> Dict[str, Any]:
            return self.data
    
    class FlexibleJSONrepr:
        def __init__(self, data):
            self.data = data
        
        def JSONrepr(self, *args, **kwargs) -> Dict[str, Any]:
            return self.data
    
    obj1 = FlexibleToDict(data)
    obj2 = FlexibleJSONrepr(data)
    
    assert obj1.to_dict() == data
    assert obj2.JSONrepr() == data


def test_subclass_protocol_override():
    """Test that subclasses can override protocol methods."""
    
    class Base:
        def to_dict(self) -> Dict[str, Any]:
            return {'class': 'Base'}
    
    class Derived(Base):
        def to_dict(self) -> Dict[str, Any]:
            base = super().to_dict()
            base['class'] = 'Derived'
            return base
    
    base = Base()
    derived = Derived()
    
    assert base.to_dict() == {'class': 'Base'}
    assert derived.to_dict() == {'class': 'Derived'}