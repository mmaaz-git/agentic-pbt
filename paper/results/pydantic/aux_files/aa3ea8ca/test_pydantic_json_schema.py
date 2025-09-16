"""Property-based tests for pydantic.json_schema module"""

import json
import re
from typing import Optional, List, Union, Dict, Any, Literal
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
from pydantic import BaseModel, Field, ConfigDict
from pydantic.json_schema import (
    GenerateJsonSchema, 
    model_json_schema,
    _DefinitionsRemapping,
    DefsRef,
    JsonRef
)
import pytest


# Strategy for generating valid field types
@composite
def simple_field_types(draw):
    """Generate simple field types for Pydantic models"""
    return draw(st.sampled_from([
        str,
        int,
        float,
        bool,
        type(None),
        Optional[str],
        Optional[int],
        List[str],
        List[int],
        Dict[str, str],
        Dict[str, int],
    ]))


@composite
def valid_field_names(draw):
    """Generate valid Python identifier field names"""
    # Start with a letter or underscore, then alphanumeric or underscore
    first = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyz_"))
    rest = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=0, max_size=10))
    name = first + rest
    # Avoid Python keywords
    assume(name not in ["class", "def", "return", "if", "else", "for", "while", "import", "from", "pass", "break", "continue"])
    return name


@composite 
def simple_model_schemas(draw):
    """Generate simple Pydantic model classes dynamically"""
    n_fields = draw(st.integers(min_value=1, max_value=5))
    fields = {}
    
    for _ in range(n_fields):
        field_name = draw(valid_field_names())
        assume(field_name not in fields)  # Avoid duplicate field names
        field_type = draw(simple_field_types())
        fields[field_name] = (field_type, ...)  # Required field
    
    model_name = draw(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=1, max_size=1)) + \
                 draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=0, max_size=10))
    
    # Create model dynamically
    model = type(model_name, (BaseModel,), {"__annotations__": {k: v[0] for k, v in fields.items()}})
    return model


# Property 1: Generated JSON schemas are valid JSON that can be round-tripped
@given(model_cls=simple_model_schemas(), mode=st.sampled_from(['validation', 'serialization']))
@settings(max_examples=100)
def test_schema_is_valid_json(model_cls, mode):
    """Test that generated schemas are valid JSON that can be serialized and deserialized"""
    schema = model_json_schema(model_cls, mode=mode)
    
    # Schema should be a dictionary
    assert isinstance(schema, dict)
    
    # Should be JSON serializable
    json_str = json.dumps(schema)
    assert isinstance(json_str, str)
    
    # Should be able to deserialize back
    deserialized = json.loads(json_str)
    assert deserialized == schema


# Property 2: All $ref values in schema resolve to valid definitions
@given(model_cls=simple_model_schemas())
@settings(max_examples=100)
def test_all_refs_resolve(model_cls):
    """Test that all $ref values in the schema resolve to valid definitions"""
    
    # Create a model with nested references
    class NestedModel(BaseModel):
        field: model_cls
        optional_field: Optional[model_cls] = None
        list_field: List[model_cls] = []
    
    schema = model_json_schema(NestedModel)
    
    def extract_refs(obj, refs=None):
        """Recursively extract all $ref values from schema"""
        if refs is None:
            refs = set()
        
        if isinstance(obj, dict):
            if '$ref' in obj:
                refs.add(obj['$ref'])
            for value in obj.values():
                extract_refs(value, refs)
        elif isinstance(obj, list):
            for item in obj:
                extract_refs(item, refs)
        
        return refs
    
    # Extract all refs
    all_refs = extract_refs(schema)
    
    # Get definitions
    defs = schema.get('$defs', {})
    
    # Check each ref resolves
    for ref in all_refs:
        # Refs should follow the pattern #/$defs/ModelName
        assert ref.startswith('#/$defs/'), f"Invalid ref format: {ref}"
        model_name = ref.replace('#/$defs/', '')
        
        # The referenced model should exist in definitions
        assert model_name in defs, f"Ref {ref} does not resolve to a definition"
        
        # The definition should be a valid schema object
        assert isinstance(defs[model_name], dict)
        assert 'type' in defs[model_name] or '$ref' in defs[model_name]


# Property 3: Schema generation with different ref_templates produces equivalent schemas
@given(
    model_cls=simple_model_schemas(),
    template_suffix=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=1, max_size=10)
)
@settings(max_examples=100)
def test_ref_template_consistency(model_cls, template_suffix):
    """Test that different ref_templates produce structurally equivalent schemas"""
    
    # Generate schemas with different ref templates
    default_schema = model_json_schema(model_cls)
    custom_template = f"#/definitions/{template_suffix}_{{model}}"
    custom_schema = model_json_schema(model_cls, ref_template=custom_template)
    
    # Both should have the same structure (same keys at top level)
    assert set(default_schema.keys()) == set(custom_schema.keys())
    
    # If there are properties, they should have the same names
    if 'properties' in default_schema:
        assert set(default_schema['properties'].keys()) == set(custom_schema['properties'].keys())
    
    # Required fields should be the same
    if 'required' in default_schema:
        assert set(default_schema.get('required', [])) == set(custom_schema.get('required', []))


# Property 4: DefinitionsRemapping preserves schema structure
@given(st.data())
@settings(max_examples=50)
def test_definitions_remapping_preserves_structure(data):
    """Test that _DefinitionsRemapping.remap_json_schema preserves schema structure"""
    
    # Create models with potential name collisions
    class Model1(BaseModel):
        field1: str
    
    class Model2(BaseModel):
        field2: int
        
    class Container(BaseModel):
        m1: Model1
        m2: Model2
        m1_list: List[Model1] = []
    
    schema = model_json_schema(Container)
    
    # Create a simple remapping
    original_refs = {}
    remapped_refs = {}
    
    # Build remapping dictionaries
    if '$defs' in schema:
        for def_name in schema['$defs']:
            original_def = DefsRef(def_name)
            # Add a suffix to create remapped version
            remapped_def = DefsRef(f"{def_name}_remapped")
            original_refs[original_def] = remapped_def
            
            original_json = JsonRef(f"#/$defs/{def_name}")
            remapped_json = JsonRef(f"#/$defs/{def_name}_remapped")
            remapped_refs[original_json] = remapped_json
    
    if not original_refs:
        # No definitions to remap, skip this test case
        return
    
    remapping = _DefinitionsRemapping(
        defs_remapping=original_refs,
        json_remapping=remapped_refs
    )
    
    # Apply remapping
    remapped_schema = remapping.remap_json_schema(schema)
    
    # The remapped schema should still be valid JSON
    json_str = json.dumps(remapped_schema)
    json.loads(json_str)
    
    # Structure should be preserved
    assert type(remapped_schema) == type(schema)
    
    # If original had $defs, remapped should too
    if '$defs' in schema:
        assert '$defs' in remapped_schema or len(schema['$defs']) == 0


# Property 5: GenerateJsonSchema handles field aliases correctly
@given(
    field_name=valid_field_names(),
    alias=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-", min_size=1, max_size=20),
    by_alias=st.booleans()
)
@settings(max_examples=100)
def test_field_alias_handling(field_name, alias, by_alias):
    """Test that field aliases are handled correctly based on by_alias parameter"""
    
    # Create model with aliased field
    class AliasModel(BaseModel):
        model_config = ConfigDict(populate_by_name=True)
        
        # Need to use __annotations__ to set the field dynamically
        pass
    
    # Set the field with alias dynamically
    AliasModel.__annotations__ = {field_name: str}
    setattr(AliasModel, field_name, Field(alias=alias))
    
    # Generate schema
    schema = model_json_schema(AliasModel, by_alias=by_alias)
    
    # Check that the correct name is used in properties
    properties = schema.get('properties', {})
    
    if by_alias:
        # Should use alias
        assert alias in properties or len(properties) == 0
        if alias in properties:
            assert field_name not in properties or field_name == alias
    else:
        # Should use field name
        assert field_name in properties or len(properties) == 0
        if field_name in properties:
            assert alias not in properties or field_name == alias


# Property 6: Validation and serialization modes produce compatible schemas
@given(model_cls=simple_model_schemas())
@settings(max_examples=100)
def test_validation_serialization_mode_compatibility(model_cls):
    """Test that validation and serialization modes produce compatible schemas"""
    
    validation_schema = model_json_schema(model_cls, mode='validation')
    serialization_schema = model_json_schema(model_cls, mode='serialization')
    
    # Both should be valid dictionaries
    assert isinstance(validation_schema, dict)
    assert isinstance(serialization_schema, dict)
    
    # Both should have the same base structure keys (though values may differ)
    base_keys = {'type', 'title'}
    for key in base_keys:
        if key in validation_schema:
            assert key in serialization_schema
    
    # If one has properties, both should (for simple models)
    if 'properties' in validation_schema:
        assert 'properties' in serialization_schema
        
        # Property names might differ (computed fields, etc.) but should overlap
        val_props = set(validation_schema['properties'].keys())
        ser_props = set(serialization_schema['properties'].keys())
        
        # For simple models without computed fields, they should be the same
        # But we allow serialization to have additional fields (computed fields)
        # Validation properties should be a subset of or equal to serialization properties
        # OR they should be completely equal for simple models
        assert val_props <= ser_props or val_props == ser_props


if __name__ == "__main__":
    # Run a quick test to make sure things work
    print("Running property-based tests for pydantic.json_schema...")
    pytest.main([__file__, "-v", "--tb=short"])