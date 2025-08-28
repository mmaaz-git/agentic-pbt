"""Comprehensive property-based tests for pydantic JSON schema generation logic"""

import json
import sys
from typing import Optional, List, Union, Dict, Any, Literal, get_args
from hypothesis import given, strategies as st, assume, settings, note
from pydantic import BaseModel, Field, ConfigDict
from pydantic.json_schema import (
    GenerateJsonSchema,
    model_json_schema,
    JsonSchemaMode
)
import pytest


# Property 34: Test that changing modes actually changes the schema for computed fields
@given(st.data())
@settings(max_examples=50)
def test_mode_affects_computed_fields(data):
    """Test that validation vs serialization mode properly handles computed fields"""
    
    from pydantic import computed_field
    
    class ModelWithComputed(BaseModel):
        base_value: int
        
        @computed_field
        @property
        def doubled(self) -> int:
            return self.base_value * 2
    
    val_schema = model_json_schema(ModelWithComputed, mode='validation')
    ser_schema = model_json_schema(ModelWithComputed, mode='serialization')
    
    # Both should be valid JSON
    json.dumps(val_schema)
    json.dumps(ser_schema)
    
    val_props = val_schema.get('properties', {})
    ser_props = ser_schema.get('properties', {})
    
    # Validation schema should not include computed field
    assert 'doubled' not in val_props
    assert 'base_value' in val_props
    
    # Serialization schema should include computed field
    assert 'doubled' in ser_props
    assert 'base_value' in ser_props


# Property 35: Test with Literal types containing special values
@given(st.data())
@settings(max_examples=50)
def test_literal_special_values(data):
    """Test Literal types with special values like empty strings, None, etc."""
    
    class LiteralModel(BaseModel):
        empty_string_literal: Literal[""]
        none_literal: Literal[None]
        bool_literal: Literal[True, False]
        mixed_literal: Literal["a", 1, None, True]
        unicode_literal: Literal["🦄", "中文"]
    
    schema = model_json_schema(LiteralModel)
    
    # Should be valid JSON
    json_str = json.dumps(schema, ensure_ascii=False)
    json.loads(json_str)
    
    props = schema.get('properties', {})
    
    # Check empty string literal
    if 'empty_string_literal' in props:
        # Should have enum with empty string
        assert 'enum' in props['empty_string_literal'] or 'const' in props['empty_string_literal']
        if 'enum' in props['empty_string_literal']:
            assert "" in props['empty_string_literal']['enum']
        elif 'const' in props['empty_string_literal']:
            assert props['empty_string_literal']['const'] == ""
    
    # Check None literal
    if 'none_literal' in props:
        # Should indicate null type
        assert props['none_literal'].get('type') == 'null' or \
               props['none_literal'].get('const') is None or \
               props['none_literal'].get('enum') == [None]
    
    # Check mixed literal
    if 'mixed_literal' in props:
        if 'enum' in props['mixed_literal']:
            enum_values = props['mixed_literal']['enum']
            assert "a" in enum_values
            assert 1 in enum_values
            assert None in enum_values
            assert True in enum_values


# Property 36: Test field ordering preservation
@given(st.data())
@settings(max_examples=50)
def test_field_order_preservation(data):
    """Test that field order is preserved in the schema"""
    
    class OrderedModel(BaseModel):
        zebra: str
        apple: int
        banana: float
        xylophone: bool
        middle: Optional[str] = None
        aardvark: List[int] = []
    
    schema = model_json_schema(OrderedModel)
    
    if 'properties' in schema:
        # Get the keys in order
        prop_keys = list(schema['properties'].keys())
        
        # The order should match the order defined in the model
        expected_order = ['zebra', 'apple', 'banana', 'xylophone', 'middle', 'aardvark']
        assert prop_keys == expected_order
    
    # Required fields should also maintain order
    if 'required' in schema:
        required = schema['required']
        # Filter expected order to only required fields
        expected_required = [f for f in expected_order if f in ['zebra', 'apple', 'banana', 'xylophone']]
        # Order of required fields should match
        assert all(required.index(f1) < required.index(f2) 
                  for i, f1 in enumerate(expected_required[:-1]) 
                  for f2 in expected_required[i+1:]
                  if f1 in required and f2 in required)


# Property 37: Test with models using __root__
@given(st.data())
@settings(max_examples=50)
def test_root_model_schema(data):
    """Test schema generation for models with __root__"""
    
    from pydantic import RootModel
    
    class StringRootModel(RootModel[str]):
        pass
    
    class ListRootModel(RootModel[List[int]]):
        pass
    
    class DictRootModel(RootModel[Dict[str, Any]]):
        pass
    
    # Test string root model
    string_schema = model_json_schema(StringRootModel)
    json.dumps(string_schema)
    assert string_schema.get('type') == 'string'
    
    # Test list root model
    list_schema = model_json_schema(ListRootModel)
    json.dumps(list_schema)
    assert list_schema.get('type') == 'array'
    if 'items' in list_schema:
        assert list_schema['items'].get('type') == 'integer'
    
    # Test dict root model
    dict_schema = model_json_schema(DictRootModel)
    json.dumps(dict_schema)
    assert dict_schema.get('type') == 'object'


# Property 38: Test schema generation with inheritance
@given(st.data())
@settings(max_examples=50)
def test_inheritance_schema(data):
    """Test that inherited fields are properly included in schema"""
    
    class BaseModel1(BaseModel):
        base_field: str
        shared_field: int = 1
    
    class ChildModel(BaseModel1):
        child_field: float
        shared_field: int = 2  # Override default
    
    class GrandchildModel(ChildModel):
        grandchild_field: bool
    
    # Test child model schema
    child_schema = model_json_schema(ChildModel)
    json.dumps(child_schema)
    
    child_props = child_schema.get('properties', {})
    # Should have both base and child fields
    assert 'base_field' in child_props
    assert 'child_field' in child_props
    assert 'shared_field' in child_props
    
    # Check default value is overridden
    if 'default' in child_props['shared_field']:
        assert child_props['shared_field']['default'] == 2
    
    # Test grandchild model schema
    grandchild_schema = model_json_schema(GrandchildModel)
    json.dumps(grandchild_schema)
    
    grandchild_props = grandchild_schema.get('properties', {})
    # Should have all fields
    assert 'base_field' in grandchild_props
    assert 'child_field' in grandchild_props
    assert 'grandchild_field' in grandchild_props


# Property 39: Test with very large models (many fields)
@given(
    num_fields=st.integers(min_value=50, max_value=100)
)
@settings(max_examples=10, deadline=10000)
def test_large_model_schema(num_fields):
    """Test schema generation with models having many fields"""
    
    # Create a model with many fields dynamically
    fields = {}
    annotations = {}
    
    for i in range(num_fields):
        field_name = f"field_{i:04d}"
        field_type = [str, int, float, bool][i % 4]
        annotations[field_name] = field_type
        if i % 3 == 0:
            # Some fields have defaults
            fields[field_name] = Field(default=f"default_{i}")
    
    LargeModel = type('LargeModel', (BaseModel,), {
        '__annotations__': annotations,
        **fields
    })
    
    schema = model_json_schema(LargeModel)
    
    # Should be valid JSON
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Should have all fields
    props = schema.get('properties', {})
    assert len(props) == num_fields
    
    # Check a sample of fields
    for i in [0, num_fields // 2, num_fields - 1]:
        field_name = f"field_{i:04d}"
        assert field_name in props


# Property 40: Test with models using generic types
@given(st.data())
@settings(max_examples=50)
def test_generic_model_schema(data):
    """Test schema generation for generic models"""
    
    from typing import TypeVar, Generic
    
    T = TypeVar('T')
    
    class GenericContainer(BaseModel, Generic[T]):
        value: T
        metadata: str
    
    # Create concrete instances
    StringContainer = GenericContainer[str]
    IntContainer = GenericContainer[int]
    ListContainer = GenericContainer[List[str]]
    
    # Test string container
    str_schema = model_json_schema(StringContainer)
    json.dumps(str_schema)
    str_props = str_schema.get('properties', {})
    if 'value' in str_props:
        assert str_props['value'].get('type') == 'string'
    
    # Test int container
    int_schema = model_json_schema(IntContainer)
    json.dumps(int_schema)
    int_props = int_schema.get('properties', {})
    if 'value' in int_props:
        assert int_props['value'].get('type') == 'integer'
    
    # Test list container
    list_schema = model_json_schema(ListContainer)
    json.dumps(list_schema)
    list_props = list_schema.get('properties', {})
    if 'value' in list_props:
        assert list_props['value'].get('type') == 'array'
        if 'items' in list_props['value']:
            assert list_props['value']['items'].get('type') == 'string'


# Property 41: Test that identical models produce identical schemas
@given(st.data())
@settings(max_examples=50)
def test_schema_determinism(data):
    """Test that generating schema multiple times produces identical results"""
    
    class TestModel(BaseModel):
        field1: str
        field2: int
        field3: Optional[float] = None
        field4: List[str] = []
    
    # Generate schema multiple times
    schemas = [model_json_schema(TestModel) for _ in range(5)]
    
    # All should be identical
    first_json = json.dumps(schemas[0], sort_keys=True)
    for schema in schemas[1:]:
        assert json.dumps(schema, sort_keys=True) == first_json


# Property 42: Test with models having complex default factories
@given(st.data())
@settings(max_examples=50)
def test_default_factory_schema(data):
    """Test schema generation with default_factory fields"""
    
    from pydantic import Field
    
    def default_list():
        return [1, 2, 3]
    
    def default_dict():
        return {"key": "value"}
    
    class FactoryModel(BaseModel):
        list_field: List[int] = Field(default_factory=list)
        dict_field: Dict[str, str] = Field(default_factory=dict)
        custom_list: List[int] = Field(default_factory=default_list)
        custom_dict: Dict[str, str] = Field(default_factory=default_dict)
    
    schema = model_json_schema(FactoryModel)
    
    # Should be valid JSON
    json.dumps(schema)
    
    props = schema.get('properties', {})
    
    # Fields with default_factory should have type but might not have default value
    for field_name in ['list_field', 'dict_field', 'custom_list', 'custom_dict']:
        assert field_name in props
        # Should have type information
        assert 'type' in props[field_name]
    
    # List fields should be arrays
    assert props['list_field']['type'] == 'array'
    assert props['custom_list']['type'] == 'array'
    
    # Dict fields should be objects
    assert props['dict_field']['type'] == 'object'
    assert props['custom_dict']['type'] == 'object'


if __name__ == "__main__":
    print("Running comprehensive schema generation tests...")
    pytest.main([__file__, "-v", "--tb=short"])