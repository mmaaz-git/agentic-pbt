"""Edge case property-based tests for pydantic.json_schema module"""

import json
import math
import sys
from typing import Optional, List, Union, Dict, Any, Literal, Tuple, Set
from decimal import Decimal
from datetime import datetime, date, time, timedelta
from uuid import UUID
from enum import Enum, IntEnum
from hypothesis import given, strategies as st, assume, settings, note, example
from hypothesis.strategies import composite
from pydantic import BaseModel, Field, ConfigDict, field_validator, ValidationError
from pydantic.json_schema import (
    GenerateJsonSchema, 
    model_json_schema,
    JsonSchemaValue
)
import pytest


# Property 16: Test with numeric edge cases (inf, nan, very large/small numbers)
@given(st.data())
@settings(max_examples=50)
def test_numeric_edge_cases(data):
    """Test schema generation with numeric edge cases"""
    
    class NumericModel(BaseModel):
        float_field: float
        optional_float: Optional[float] = None
        float_with_inf: float = float('inf')
        float_with_neg_inf: float = float('-inf')
        float_with_nan: float = float('nan')
        decimal_field: Decimal = Decimal('999999999999999999999999999999.99999999999999999999999999')
    
    schema = model_json_schema(NumericModel)
    
    # Should generate valid JSON
    json_str = json.dumps(schema, allow_nan=True)  # Allow NaN/Inf for this test
    json.loads(json_str)
    
    # Check that numeric fields have correct types
    assert 'properties' in schema
    props = schema['properties']
    
    assert 'float_field' in props
    assert props['float_field']['type'] == 'number'
    
    # Default values with inf/nan might be handled specially
    if 'default' in props['float_with_inf']:
        # Check if it's properly serialized
        default_val = props['float_with_inf']['default']
        # Should be either the string "Infinity" or null or omitted
        assert default_val in [None, 'Infinity', float('inf')] or math.isinf(default_val)


# Property 17: Test with complex nested generics
@given(st.data())
@settings(max_examples=50)
def test_complex_nested_generics(data):
    """Test schema generation with complex nested generic types"""
    
    class ComplexModel(BaseModel):
        nested_dict: Dict[str, Dict[str, List[int]]]
        tuple_field: Tuple[str, int, bool]
        set_field: Set[str]
        optional_nested: Optional[Dict[str, Optional[List[Optional[str]]]]] = None
    
    schema = model_json_schema(ComplexModel)
    
    # Should generate valid JSON
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Check that complex types are properly represented
    assert 'properties' in schema
    props = schema['properties']
    
    # nested_dict should be an object type
    if 'nested_dict' in props:
        assert 'type' in props['nested_dict']
        # Could be 'object' or have additionalProperties
        assert props['nested_dict']['type'] == 'object' or 'additionalProperties' in props['nested_dict']
    
    # tuple_field should be an array with specific items
    if 'tuple_field' in props:
        assert props['tuple_field']['type'] == 'array'
        # Should have prefixItems or items defining the tuple structure
        assert 'prefixItems' in props['tuple_field'] or 'items' in props['tuple_field']
    
    # set_field should be an array with unique items
    if 'set_field' in props:
        assert props['set_field']['type'] == 'array'
        assert props['set_field'].get('uniqueItems') == True


# Property 18: Test with datetime and temporal types
@given(st.data())
@settings(max_examples=50)
def test_datetime_types(data):
    """Test schema generation with datetime types"""
    
    class DateTimeModel(BaseModel):
        dt_field: datetime
        date_field: date
        time_field: time
        timedelta_field: timedelta
        optional_dt: Optional[datetime] = None
    
    schema = model_json_schema(DateTimeModel)
    
    # Should generate valid JSON
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Check that datetime fields have correct format
    assert 'properties' in schema
    props = schema['properties']
    
    # datetime field should have string type with format
    if 'dt_field' in props:
        assert props['dt_field']['type'] == 'string'
        assert 'format' in props['dt_field']
        assert props['dt_field']['format'] in ['date-time', 'datetime']
    
    # date field should have string type with date format
    if 'date_field' in props:
        assert props['date_field']['type'] == 'string'
        assert props['date_field'].get('format') == 'date'
    
    # time field should have string type with time format
    if 'time_field' in props:
        assert props['time_field']['type'] == 'string'
        assert props['time_field'].get('format') == 'time'


# Property 19: Test with Enum types
@given(st.data())
@settings(max_examples=50)
def test_enum_types(data):
    """Test schema generation with Enum types"""
    
    class Color(Enum):
        RED = 'red'
        GREEN = 'green'
        BLUE = 'blue'
    
    class Priority(IntEnum):
        LOW = 1
        MEDIUM = 2
        HIGH = 3
    
    class EnumModel(BaseModel):
        color: Color
        priority: Priority
        optional_color: Optional[Color] = None
        color_list: List[Color] = []
    
    schema = model_json_schema(EnumModel)
    
    # Should generate valid JSON
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Check that enum fields have correct enum values
    assert 'properties' in schema
    props = schema['properties']
    
    # color field should have enum values
    if 'color' in props:
        # Should either have 'enum' directly or reference a definition
        assert 'enum' in props['color'] or '$ref' in props['color'] or 'allOf' in props['color']
        
    # Check definitions for enum types
    if '$defs' in schema:
        for def_name, def_schema in schema['$defs'].items():
            if 'enum' in def_schema:
                # Enum values should be the actual enum values
                assert isinstance(def_schema['enum'], list)
                assert len(def_schema['enum']) > 0


# Property 20: Test with UUID and other special types
@given(st.data())
@settings(max_examples=50)
def test_uuid_types(data):
    """Test schema generation with UUID types"""
    
    class UUIDModel(BaseModel):
        id: UUID
        optional_id: Optional[UUID] = None
        id_list: List[UUID] = []
    
    schema = model_json_schema(UUIDModel)
    
    # Should generate valid JSON
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Check that UUID fields have correct format
    assert 'properties' in schema
    props = schema['properties']
    
    # UUID field should have string type with format
    if 'id' in props:
        assert props['id']['type'] == 'string'
        assert 'format' in props['id']
        assert props['id']['format'] == 'uuid'


# Property 21: Test with models containing class methods and properties
@given(st.data())
@settings(max_examples=50)
def test_model_with_methods(data):
    """Test that models with methods and properties generate valid schemas"""
    
    class MethodModel(BaseModel):
        value: int
        
        @property
        def computed_value(self) -> int:
            return self.value * 2
        
        def instance_method(self) -> str:
            return f"Value is {self.value}"
        
        @classmethod
        def class_method(cls) -> str:
            return "Class method"
        
        @staticmethod
        def static_method() -> str:
            return "Static method"
    
    schema = model_json_schema(MethodModel)
    
    # Should generate valid JSON
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Should only include actual fields, not methods
    assert 'properties' in schema
    props = schema['properties']
    
    # Should have the value field
    assert 'value' in props
    
    # Should not include methods in properties
    assert 'instance_method' not in props
    assert 'class_method' not in props
    assert 'static_method' not in props
    
    # Property might be included depending on configuration
    # but if it is, it should be properly formatted


# Property 22: Test with extremely long field names and values
@given(
    long_field_name=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=100, max_size=200),
    long_string_default=st.text(min_size=1000, max_size=2000)
)
@settings(max_examples=20, deadline=5000)
def test_long_names_and_values(long_field_name, long_string_default):
    """Test schema generation with very long field names and default values"""
    
    # Ensure field name is a valid Python identifier
    field_name = "field_" + "".join(c for c in long_field_name if c.isalnum() or c == "_")[:100]
    
    # Create model class dynamically
    attrs = {
        '__annotations__': {field_name: str},
        field_name: Field(default=long_string_default, description="A very long field")
    }
    
    LongModel = type('LongModel', (BaseModel,), attrs)
    
    schema = model_json_schema(LongModel)
    
    # Should generate valid JSON even with long names/values
    json_str = json.dumps(schema)
    deserialized = json.loads(json_str)
    
    # Should have the long field
    assert 'properties' in schema
    assert field_name in schema['properties']
    
    # Default value should be preserved
    if 'default' in schema['properties'][field_name]:
        assert schema['properties'][field_name]['default'] == long_string_default


# Property 23: Test with models using ConfigDict settings
@given(
    extra_setting=st.sampled_from(['forbid', 'allow', 'ignore']),
    frozen=st.booleans(),
    validate_default=st.booleans()
)
@settings(max_examples=50)
def test_config_dict_settings(extra_setting, frozen, validate_default):
    """Test that ConfigDict settings don't break schema generation"""
    
    class ConfiguredModel(BaseModel):
        model_config = ConfigDict(
            extra=extra_setting,
            frozen=frozen,
            validate_default=validate_default,
            str_strip_whitespace=True,
            use_enum_values=True
        )
        
        field1: str
        field2: int = 42
    
    schema = model_json_schema(ConfiguredModel)
    
    # Should generate valid JSON regardless of config
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Should have basic structure
    assert 'properties' in schema
    assert 'field1' in schema['properties']
    assert 'field2' in schema['properties']
    
    # Extra setting might affect additionalProperties
    if extra_setting == 'forbid':
        # When forbid, additionalProperties should be false
        assert schema.get('additionalProperties') == False
    elif extra_setting == 'allow':
        # When allow, additionalProperties might be true or omitted
        assert schema.get('additionalProperties', True) == True


# Property 24: Test with Union types containing None
@given(st.data())
@settings(max_examples=50)
def test_union_with_none(data):
    """Test Union types that include None"""
    
    class UnionModel(BaseModel):
        union_field: Union[str, int, None]
        optional_union: Optional[Union[str, int]] = None
        union_list: List[Union[str, None]] = []
    
    schema = model_json_schema(UnionModel)
    
    # Should generate valid JSON
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Check union field representation
    assert 'properties' in schema
    props = schema['properties']
    
    if 'union_field' in props:
        # Should have anyOf or oneOf with multiple types including null
        assert 'anyOf' in props['union_field'] or 'oneOf' in props['union_field'] or 'type' in props['union_field']
        
        if 'anyOf' in props['union_field']:
            types = props['union_field']['anyOf']
            # Should include null type
            assert any(t.get('type') == 'null' for t in types)
            # Should include string and integer
            assert any(t.get('type') == 'string' for t in types)
            assert any(t.get('type') == 'integer' for t in types)


# Property 25: Test schema generation with field constraints
@given(
    min_val=st.integers(min_value=-1000, max_value=0),
    max_val=st.integers(min_value=1, max_value=1000)
)
@settings(max_examples=50)
def test_field_constraints(min_val, max_val):
    """Test that field constraints are properly reflected in schema"""
    
    class ConstrainedModel(BaseModel):
        bounded_int: int = Field(ge=min_val, le=max_val)
        positive_float: float = Field(gt=0)
        short_string: str = Field(max_length=10)
        regex_string: str = Field(pattern=r'^[A-Z][a-z]+$')
        sized_list: List[int] = Field(min_length=1, max_length=5)
    
    schema = model_json_schema(ConstrainedModel)
    
    # Should generate valid JSON
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Check that constraints are in schema
    assert 'properties' in schema
    props = schema['properties']
    
    # bounded_int should have min/max
    if 'bounded_int' in props:
        assert props['bounded_int'].get('minimum') == min_val
        assert props['bounded_int'].get('maximum') == max_val
    
    # positive_float should have exclusiveMinimum
    if 'positive_float' in props:
        assert props['positive_float'].get('exclusiveMinimum') == 0
    
    # short_string should have maxLength
    if 'short_string' in props:
        assert props['short_string'].get('maxLength') == 10
    
    # regex_string should have pattern
    if 'regex_string' in props:
        assert 'pattern' in props['regex_string']
    
    # sized_list should have minItems and maxItems
    if 'sized_list' in props:
        assert props['sized_list'].get('minItems') == 1
        assert props['sized_list'].get('maxItems') == 5


if __name__ == "__main__":
    print("Running edge case property-based tests for pydantic.json_schema...")
    pytest.main([__file__, "-v", "--tb=short"])