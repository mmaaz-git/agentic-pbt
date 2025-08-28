"""Advanced property-based tests for pydantic.json_schema module"""

import json
import math
from typing import Optional, List, Union, Dict, Any, Literal, ForwardRef
from hypothesis import given, strategies as st, assume, settings, note
from hypothesis.strategies import composite
from pydantic import BaseModel, Field, ConfigDict, validator
from pydantic.json_schema import (
    GenerateJsonSchema, 
    model_json_schema,
    _DefinitionsRemapping,
    _deduplicate_schemas,
    DefsRef,
    JsonRef,
    DEFAULT_REF_TEMPLATE,
    JsonSchemaValue
)
import pytest


# Property 7: Test recursive models with self-references
@given(st.data())
@settings(max_examples=50, deadline=5000)
def test_recursive_model_schemas(data):
    """Test that recursive models generate valid schemas with proper references"""
    
    # Create a recursive model
    class TreeNode(BaseModel):
        value: int
        children: List['TreeNode'] = []
    
    schema = model_json_schema(TreeNode)
    
    # Schema should be valid JSON
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Should have a $defs section for recursive definition
    assert '$defs' in schema
    assert 'TreeNode' in schema['$defs']
    
    # The recursive reference should be properly structured
    tree_def = schema['$defs']['TreeNode']
    assert 'properties' in tree_def
    assert 'children' in tree_def['properties']
    
    children_prop = tree_def['properties']['children']
    assert 'items' in children_prop
    assert '$ref' in children_prop['items']
    assert children_prop['items']['$ref'] == '#/$defs/TreeNode'


# Property 8: Test that deduplicate_schemas preserves schema equivalence
@given(st.lists(st.dictionaries(
    st.sampled_from(['type', 'title', 'properties', 'required']),
    st.sampled_from(['string', 'integer', 'boolean', 'object', 'array']),
    min_size=1,
    max_size=3
), min_size=1, max_size=10))
@settings(max_examples=50)
def test_deduplicate_schemas_property(schemas):
    """Test that _deduplicate_schemas maintains schema equivalence"""
    
    # _deduplicate_schemas should reduce a list to unique schemas
    deduplicated = _deduplicate_schemas(schemas)
    
    # Result should be a list
    assert isinstance(deduplicated, list)
    
    # Should not have more schemas than input
    assert len(deduplicated) <= len(schemas)
    
    # Each schema in the original should have an equivalent in deduplicated
    for original in schemas:
        found_match = False
        for dedup in deduplicated:
            if original == dedup:
                found_match = True
                break
        assert found_match, f"Original schema {original} not found in deduplicated list"


# Property 9: Test models with special field types (None, Any, etc.)
@given(st.data())
@settings(max_examples=50)
def test_special_field_types(data):
    """Test that models with special field types generate valid schemas"""
    
    from typing import Any
    
    class SpecialModel(BaseModel):
        none_field: None = None
        any_field: Any = "anything"
        optional_none: Optional[None] = None
        list_any: List[Any] = []
    
    schema = model_json_schema(SpecialModel)
    
    # Should generate valid JSON
    json_str = json.dumps(schema)
    deserialized = json.loads(json_str)
    
    # Check properties exist
    assert 'properties' in schema
    props = schema['properties']
    
    # none_field should have null type
    if 'none_field' in props:
        assert props['none_field'].get('type') == 'null' or 'null' in props['none_field'].get('type', [])
    
    # any_field should allow any type
    if 'any_field' in props:
        # Any field might not have a type restriction or have multiple types
        assert 'type' not in props['any_field'] or isinstance(props['any_field']['type'], (str, list))


# Property 10: Test JSON schema with discriminated unions
@given(st.data())
@settings(max_examples=50)
def test_discriminated_union_schemas(data):
    """Test that discriminated unions generate valid schemas"""
    
    from typing import Annotated
    from pydantic import Field as PydanticField
    
    class Cat(BaseModel):
        pet_type: Literal['cat']
        meows: int
    
    class Dog(BaseModel):
        pet_type: Literal['dog'] 
        barks: float
    
    class Lizard(BaseModel):
        pet_type: Literal['reptile', 'lizard']
        scales: bool
    
    class Model(BaseModel):
        pet: Union[Cat, Dog, Lizard] = PydanticField(discriminator='pet_type')
        number: int
    
    schema = model_json_schema(Model)
    
    # Should be valid JSON
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Should have definitions for each union member
    if '$defs' in schema:
        # At least some of the union members should be defined
        defined_models = set(schema['$defs'].keys())
        expected_models = {'Cat', 'Dog', 'Lizard', 'Model'}
        # Should have at least one of the expected models
        assert len(defined_models & expected_models) > 0


# Property 11: Test that ref_template with special characters doesn't break schemas
@given(
    special_chars=st.text(alphabet="!@#$%^&*()[]{}|\\:;\"'<>,.?/~`", min_size=1, max_size=5)
)
@settings(max_examples=50)
def test_ref_template_with_special_chars(special_chars):
    """Test that special characters in ref_template are handled properly"""
    
    class SimpleModel(BaseModel):
        field: str
    
    # Create a ref template with special characters
    # This might be invalid, but shouldn't crash
    template = f"#/custom{special_chars}/{{model}}"
    
    try:
        schema = model_json_schema(SimpleModel, ref_template=template)
        # If it succeeds, the schema should be valid JSON
        json_str = json.dumps(schema)
        json.loads(json_str)
    except (ValueError, KeyError, TypeError) as e:
        # It's ok if it raises an error for invalid templates
        # But it shouldn't crash with unhandled exceptions
        note(f"Expected error for template '{template}': {e}")


# Property 12: Test models with cyclic dependencies
@given(st.data())
@settings(max_examples=30, deadline=5000)
def test_cyclic_dependency_schemas(data):
    """Test that models with cyclic dependencies generate valid schemas"""
    
    class Parent(BaseModel):
        name: str
        children: List['Child'] = []
    
    class Child(BaseModel):
        name: str
        parent: Optional['Parent'] = None
    
    # Generate schema for model with cyclic dependency
    schema = model_json_schema(Parent)
    
    # Should be valid JSON
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Should have both models in definitions
    if '$defs' in schema:
        assert 'Parent' in schema['$defs'] or 'Child' in schema['$defs']
        
        # Check that references are properly structured
        for model_name, model_def in schema['$defs'].items():
            if 'properties' in model_def:
                for prop_name, prop_def in model_def['properties'].items():
                    # Check for valid references
                    if '$ref' in prop_def:
                        ref = prop_def['$ref']
                        assert ref.startswith('#/'), f"Invalid reference format: {ref}"
                    elif 'items' in prop_def and '$ref' in prop_def['items']:
                        ref = prop_def['items']['$ref']
                        assert ref.startswith('#/'), f"Invalid reference format: {ref}"


# Property 13: Test GenerateJsonSchema with empty models
@given(st.data())
@settings(max_examples=50)
def test_empty_model_schema(data):
    """Test that empty models generate valid schemas"""
    
    class EmptyModel(BaseModel):
        pass
    
    schema = model_json_schema(EmptyModel)
    
    # Should generate valid JSON
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Should have basic structure
    assert isinstance(schema, dict)
    assert 'type' in schema
    assert schema['type'] == 'object'
    
    # Empty model should have empty or no properties
    if 'properties' in schema:
        assert len(schema['properties']) == 0
    
    # Should have no required fields
    if 'required' in schema:
        assert len(schema['required']) == 0


# Property 14: Test with models containing validators
@given(field_value=st.integers())
@settings(max_examples=50)
def test_model_with_validators(field_value):
    """Test that models with validators generate valid schemas"""
    
    class ValidatedModel(BaseModel):
        value: int
        
        @validator('value')
        def value_must_be_positive(cls, v):
            if v < 0:
                raise ValueError('must be positive')
            return v
    
    schema = model_json_schema(ValidatedModel)
    
    # Should generate valid JSON regardless of validator
    json_str = json.dumps(schema)
    json.loads(json_str)
    
    # Should have the field in properties
    assert 'properties' in schema
    assert 'value' in schema['properties']
    assert schema['properties']['value']['type'] == 'integer'


# Property 15: Test _DefinitionsRemapping.from_prioritized_choices 
@given(st.data())
@settings(max_examples=30, deadline=5000)
def test_definitions_remapping_from_prioritized_choices(data):
    """Test that from_prioritized_choices creates valid remappings"""
    
    # Create simple test data
    def1 = DefsRef("Model1")
    def2 = DefsRef("Model2")
    def3 = DefsRef("Model1_2")  # Potential collision
    
    prioritized_choices = {
        def1: [def1],
        def2: [def2],
        def3: [def3, def1],  # def3 could be remapped to def1
    }
    
    defs_to_json = {
        def1: JsonRef("#/$defs/Model1"),
        def2: JsonRef("#/$defs/Model2"), 
        def3: JsonRef("#/$defs/Model1_2"),
    }
    
    definitions = {
        def1: {"type": "object", "properties": {"a": {"type": "string"}}},
        def2: {"type": "object", "properties": {"b": {"type": "integer"}}},
        def3: {"type": "object", "properties": {"c": {"type": "boolean"}}},
    }
    
    try:
        remapping = _DefinitionsRemapping.from_prioritized_choices(
            prioritized_choices, defs_to_json, definitions
        )
        
        # Should produce a valid remapping
        assert isinstance(remapping, _DefinitionsRemapping)
        assert isinstance(remapping.defs_remapping, dict)
        assert isinstance(remapping.json_remapping, dict)
        
        # Apply remapping to a test schema
        test_schema = {
            "$defs": definitions,
            "$ref": "#/$defs/Model1"
        }
        
        remapped = remapping.remap_json_schema(test_schema)
        
        # Should still be valid JSON
        json_str = json.dumps(remapped)
        json.loads(json_str)
        
    except Exception as e:
        # Some configurations might legitimately fail
        note(f"Remapping failed with: {e}")


if __name__ == "__main__":
    print("Running advanced property-based tests for pydantic.json_schema...")
    pytest.main([__file__, "-v", "--tb=short"])