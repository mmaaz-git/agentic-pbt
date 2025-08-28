"""Property-based tests for pydantic.annotated_handlers"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from typing import Any
import pydantic_core.core_schema as core_schema
from pydantic.annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler


# Test 1: GetJsonSchemaHandler.mode attribute contract
def test_json_handler_mode_attribute_contract():
    """
    The GetJsonSchemaHandler docstring states:
    'Attributes:
        mode: Json schema mode, can be `validation` or `serialization`.'
    
    This implies the attribute should be accessible, but it raises AttributeError.
    """
    handler = GetJsonSchemaHandler()
    # According to docstring, mode should be an accessible attribute
    # but accessing it raises AttributeError
    with pytest.raises(AttributeError):
        _ = handler.mode


@given(mode=st.sampled_from(['validation', 'serialization']))
def test_json_handler_mode_persistence(mode):
    """Test that mode attribute persists after being set"""
    handler = GetJsonSchemaHandler()
    handler.mode = mode
    assert handler.mode == mode


@given(
    mode1=st.sampled_from(['validation', 'serialization']),
    mode2=st.sampled_from(['validation', 'serialization'])
)
def test_json_handler_mode_reassignment(mode1, mode2):
    """Test that mode can be reassigned multiple times"""
    handler = GetJsonSchemaHandler()
    handler.mode = mode1
    assert handler.mode == mode1
    handler.mode = mode2
    assert handler.mode == mode2


# Test 2: NotImplementedError consistency
@given(source_type=st.one_of(
    st.none(),
    st.integers(),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_core_handler_call_raises_not_implemented(source_type):
    """Test that GetCoreSchemaHandler.__call__ always raises NotImplementedError"""
    handler = GetCoreSchemaHandler()
    with pytest.raises(NotImplementedError):
        handler(source_type)


@given(source_type=st.one_of(
    st.none(),
    st.integers(),
    st.text(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_core_handler_generate_schema_raises_not_implemented(source_type):
    """Test that GetCoreSchemaHandler.generate_schema always raises NotImplementedError"""
    handler = GetCoreSchemaHandler()
    with pytest.raises(NotImplementedError):
        handler.generate_schema(source_type)


def test_core_handler_resolve_ref_schema_raises_not_implemented():
    """Test that GetCoreSchemaHandler.resolve_ref_schema raises NotImplementedError"""
    handler = GetCoreSchemaHandler()
    schema = core_schema.str_schema()
    with pytest.raises(NotImplementedError):
        handler.resolve_ref_schema(schema)


def test_core_handler_field_name_raises_not_implemented():
    """Test that GetCoreSchemaHandler.field_name property raises NotImplementedError"""
    handler = GetCoreSchemaHandler()
    with pytest.raises(NotImplementedError):
        _ = handler.field_name


def test_json_handler_call_raises_not_implemented():
    """Test that GetJsonSchemaHandler.__call__ raises NotImplementedError"""
    handler = GetJsonSchemaHandler()
    schema = core_schema.str_schema()
    with pytest.raises(NotImplementedError):
        handler(schema)


@given(json_schema=st.dictionaries(
    st.text(min_size=1),
    st.one_of(st.text(), st.integers(), st.booleans())
))
def test_json_handler_resolve_ref_raises_not_implemented(json_schema):
    """Test that GetJsonSchemaHandler.resolve_ref_schema raises NotImplementedError"""
    handler = GetJsonSchemaHandler()
    with pytest.raises(NotImplementedError):
        handler.resolve_ref_schema(json_schema)


# Test 3: Multiple instance independence
@given(
    mode1=st.sampled_from(['validation', 'serialization']),
    mode2=st.sampled_from(['validation', 'serialization'])
)
def test_json_handler_instances_are_independent(mode1, mode2):
    """Test that different instances maintain independent state"""
    handler1 = GetJsonSchemaHandler()
    handler2 = GetJsonSchemaHandler()
    
    handler1.mode = mode1
    handler2.mode = mode2
    
    assert handler1.mode == mode1
    assert handler2.mode == mode2


# Test 4: Edge case with invalid mode values
@given(mode=st.text())
def test_json_handler_accepts_any_mode_value(mode):
    """
    The docstring says mode can be 'validation' or 'serialization',
    but the implementation doesn't validate this constraint.
    """
    handler = GetJsonSchemaHandler()
    handler.mode = mode
    assert handler.mode == mode


# Test 5: Instance creation never fails
@given(st.data())
def test_handler_instantiation_never_fails(data):
    """Test that handler instantiation always succeeds"""
    core_handler = GetCoreSchemaHandler()
    json_handler = GetJsonSchemaHandler()
    
    assert isinstance(core_handler, GetCoreSchemaHandler)
    assert isinstance(json_handler, GetJsonSchemaHandler)


# Test 6: Attribute error before mode is set
def test_json_handler_mode_uninitialized_access_pattern():
    """
    Test that accessing mode before setting it raises AttributeError.
    This tests the specific bug where the annotated attribute is not initialized.
    """
    handler = GetJsonSchemaHandler()
    
    # First access should raise AttributeError
    with pytest.raises(AttributeError, match="'GetJsonSchemaHandler' object has no attribute 'mode'"):
        _ = handler.mode
    
    # After setting, it should work
    handler.mode = 'validation'
    assert handler.mode == 'validation'
    
    # Create another instance - it should also raise AttributeError initially
    handler2 = GetJsonSchemaHandler()
    with pytest.raises(AttributeError):
        _ = handler2.mode