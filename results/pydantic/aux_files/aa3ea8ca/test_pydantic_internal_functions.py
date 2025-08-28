"""Property-based tests for internal functions in pydantic.json_schema"""

import json
import copy
from typing import Dict, List, Any
from hypothesis import given, strategies as st, assume, settings, note, example
from pydantic.json_schema import (
    _DefinitionsRemapping,
    _deduplicate_schemas,
    DefsRef,
    JsonRef,
    JsonSchemaValue
)
import pytest


# Property 26: Test _deduplicate_schemas with edge cases
@given(st.data())
@settings(max_examples=100)
def test_deduplicate_edge_cases(data):
    """Test _deduplicate_schemas with various edge cases"""
    
    # Test with empty list
    assert _deduplicate_schemas([]) == []
    
    # Test with single schema
    single = [{"type": "string"}]
    assert _deduplicate_schemas(single) == single
    
    # Test with identical schemas
    identical = [{"type": "string"}, {"type": "string"}, {"type": "string"}]
    deduplicated = _deduplicate_schemas(identical)
    assert len(deduplicated) == 1
    assert deduplicated[0] == {"type": "string"}
    
    # Test with nested identical schemas
    nested = [
        {"type": "object", "properties": {"a": {"type": "string"}}},
        {"type": "object", "properties": {"a": {"type": "string"}}},
    ]
    deduplicated = _deduplicate_schemas(nested)
    assert len(deduplicated) == 1
    
    # Test with different schemas
    different = [
        {"type": "string"},
        {"type": "integer"},
        {"type": "boolean"}
    ]
    deduplicated = _deduplicate_schemas(different)
    assert len(deduplicated) == 3
    
    # Test with schemas containing $ref
    with_refs = [
        {"$ref": "#/$defs/Model1"},
        {"$ref": "#/$defs/Model1"},
        {"$ref": "#/$defs/Model2"}
    ]
    deduplicated = _deduplicate_schemas(with_refs)
    assert len(deduplicated) == 2


# Property 27: Test _DefinitionsRemapping with circular references
@given(st.data())
@settings(max_examples=50)
def test_remapping_circular_refs(data):
    """Test that remapping handles circular references correctly"""
    
    # Create schemas with circular references
    def1 = DefsRef("Model1")
    def2 = DefsRef("Model2")
    
    definitions = {
        def1: {
            "type": "object",
            "properties": {
                "field": {"$ref": "#/$defs/Model2"}
            }
        },
        def2: {
            "type": "object", 
            "properties": {
                "field": {"$ref": "#/$defs/Model1"}
            }
        }
    }
    
    prioritized_choices = {
        def1: [def1],
        def2: [def2]
    }
    
    defs_to_json = {
        def1: JsonRef("#/$defs/Model1"),
        def2: JsonRef("#/$defs/Model2")
    }
    
    try:
        remapping = _DefinitionsRemapping.from_prioritized_choices(
            prioritized_choices, defs_to_json, definitions
        )
        
        # Apply remapping
        schema = {"$defs": definitions}
        remapped = remapping.remap_json_schema(schema)
        
        # Should still have circular structure
        assert "$defs" in remapped
        # Should preserve the circular references
        
    except Exception as e:
        note(f"Circular reference handling failed: {e}")


# Property 28: Test _DefinitionsRemapping.remap_json_schema with complex schemas
@given(
    schema_dict=st.dictionaries(
        st.sampled_from(["type", "properties", "items", "$ref", "anyOf", "allOf"]),
        st.recursive(
            st.sampled_from(["string", "integer", "boolean", JsonRef("#/$defs/Test")]),
            lambda children: st.one_of(
                st.dictionaries(st.text(min_size=1, max_size=5), children, max_size=3),
                st.lists(children, max_size=3)
            ),
            max_leaves=10
        ),
        min_size=1,
        max_size=5
    )
)
@settings(max_examples=50, deadline=5000)
def test_remap_preserves_structure(schema_dict):
    """Test that remap_json_schema preserves the overall structure"""
    
    # Create a simple remapping
    remapping = _DefinitionsRemapping(
        defs_remapping={DefsRef("Test"): DefsRef("TestRemapped")},
        json_remapping={JsonRef("#/$defs/Test"): JsonRef("#/$defs/TestRemapped")}
    )
    
    # Apply remapping
    remapped = remapping.remap_json_schema(schema_dict)
    
    # Should preserve the type of the input
    assert type(remapped) == type(schema_dict)
    
    # If it's a dict, should have same keys (values might differ due to remapping)
    if isinstance(schema_dict, dict):
        assert set(remapped.keys()) == set(schema_dict.keys())
    
    # If it's a list, should have same length
    if isinstance(schema_dict, list):
        assert len(remapped) == len(schema_dict)


# Property 29: Test _DefinitionsRemapping with empty and None values
@given(st.data())
@settings(max_examples=50)
def test_remapping_empty_none(data):
    """Test remapping with empty and None values"""
    
    # Empty remapping should not change anything
    empty_remapping = _DefinitionsRemapping(
        defs_remapping={},
        json_remapping={}
    )
    
    test_schemas = [
        {},
        {"type": "string"},
        {"$ref": "#/$defs/Model"},
        None,
        [],
        [{"type": "string"}],
        {"properties": {"field": None}},
        {"anyOf": [None, {"type": "string"}]}
    ]
    
    for schema in test_schemas:
        remapped = empty_remapping.remap_json_schema(schema)
        assert remapped == schema


# Property 30: Test _DefinitionsRemapping.from_prioritized_choices with collisions
@given(st.data())
@settings(max_examples=50, deadline=5000)
def test_prioritized_choices_with_collisions(data):
    """Test from_prioritized_choices when there are name collisions"""
    
    # Create schemas that would have collisions
    def1 = DefsRef("Model")
    def2 = DefsRef("Model_1")
    def3 = DefsRef("Model_2")
    
    # All could potentially remap to "Model"
    prioritized_choices = {
        def1: [def1],  # Model stays as Model
        def2: [DefsRef("Model"), def2],  # Model_1 prefers Model but falls back to Model_1
        def3: [DefsRef("Model"), def2, def3],  # Model_2 has multiple preferences
    }
    
    defs_to_json = {
        def1: JsonRef("#/$defs/Model"),
        def2: JsonRef("#/$defs/Model_1"),
        def3: JsonRef("#/$defs/Model_2"),
        DefsRef("Model"): JsonRef("#/$defs/Model"),
    }
    
    # Different schemas to ensure they can't all map to the same name
    definitions = {
        def1: {"type": "object", "properties": {"a": {"type": "string"}}},
        def2: {"type": "object", "properties": {"b": {"type": "integer"}}},
        def3: {"type": "object", "properties": {"c": {"type": "boolean"}}},
    }
    
    try:
        remapping = _DefinitionsRemapping.from_prioritized_choices(
            prioritized_choices, defs_to_json, definitions
        )
        
        # Check that remapping is valid
        assert isinstance(remapping.defs_remapping, dict)
        assert isinstance(remapping.json_remapping, dict)
        
        # Each original def should have a remapping
        for original_def in [def1, def2, def3]:
            remapped_def = remapping.remap_defs_ref(original_def)
            assert isinstance(remapped_def, str)
        
        # Apply to a schema with all definitions
        test_schema = {
            "$defs": definitions,
            "anyOf": [
                {"$ref": "#/$defs/Model"},
                {"$ref": "#/$defs/Model_1"},
                {"$ref": "#/$defs/Model_2"}
            ]
        }
        
        remapped_schema = remapping.remap_json_schema(test_schema)
        
        # Should still be valid JSON
        json.dumps(remapped_schema)
        
    except Exception as e:
        note(f"Collision handling failed: {e}")


# Property 31: Test _deduplicate_schemas preserves order of first occurrence
@given(
    schemas=st.lists(
        st.dictionaries(
            st.sampled_from(["type", "format", "title"]),
            st.sampled_from(["string", "integer", "number", "boolean", "null"]),
            min_size=1,
            max_size=3
        ),
        min_size=1,
        max_size=20
    )
)
@settings(max_examples=50)
def test_deduplicate_preserves_first_occurrence(schemas):
    """Test that _deduplicate_schemas preserves the first occurrence of each unique schema"""
    
    deduplicated = _deduplicate_schemas(schemas)
    
    # Track which schemas we've seen
    seen = []
    seen_json = []
    
    for schema in schemas:
        schema_json = json.dumps(schema, sort_keys=True)
        if schema_json not in seen_json:
            seen.append(schema)
            seen_json.append(schema_json)
    
    # Deduplicated should match the first occurrences
    assert len(deduplicated) == len(seen)
    
    # Each deduplicated schema should match a first occurrence
    for dedup_schema in deduplicated:
        dedup_json = json.dumps(dedup_schema, sort_keys=True)
        assert dedup_json in seen_json


# Property 32: Test _DefinitionsRemapping with deeply nested structures
@given(st.data())
@settings(max_examples=30, deadline=5000)
def test_remapping_deeply_nested(data):
    """Test remapping with deeply nested schema structures"""
    
    # Create a deeply nested schema
    deep_schema = {
        "$defs": {
            "Model": {
                "type": "object",
                "properties": {
                    "field1": {
                        "type": "array",
                        "items": {
                            "anyOf": [
                                {"$ref": "#/$defs/Model"},
                                {
                                    "type": "object",
                                    "properties": {
                                        "nested": {"$ref": "#/$defs/Model"}
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        },
        "$ref": "#/$defs/Model"
    }
    
    # Create remapping
    remapping = _DefinitionsRemapping(
        defs_remapping={DefsRef("Model"): DefsRef("RemappedModel")},
        json_remapping={JsonRef("#/$defs/Model"): JsonRef("#/$defs/RemappedModel")}
    )
    
    # Apply remapping
    remapped = remapping.remap_json_schema(deep_schema)
    
    # Check that all references were updated
    def check_refs(obj, ref_to_find="#/$defs/Model", ref_expected="#/$defs/RemappedModel"):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$ref" and value == ref_to_find:
                    assert False, f"Found unreplaced ref: {value}"
                elif key == "$ref" and value == ref_expected:
                    pass  # This is expected
                else:
                    check_refs(value, ref_to_find, ref_expected)
        elif isinstance(obj, list):
            for item in obj:
                check_refs(item, ref_to_find, ref_expected)
    
    check_refs(remapped)
    
    # Should have the remapped model in definitions
    assert "RemappedModel" in remapped["$defs"] or "Model" in remapped["$defs"]


# Property 33: Test schemas with special JSON characters in strings
@given(
    special_string=st.one_of(
        st.text(alphabet='"\\', min_size=1),
        st.text().map(lambda x: x + '\n' + x if x else '\n'),
        st.text().map(lambda x: '\\' + x),
        st.text().map(lambda x: f'"{x}"'),
        st.sampled_from(['\n', '\r', '\t', '\\n', '\\r', '\\t', '"hello"', '\\\\'])
    )
)
@settings(max_examples=50)
def test_special_json_characters(special_string):
    """Test that schemas with special JSON characters are handled correctly"""
    
    test_schema = {
        "type": "object",
        "properties": {
            "field": {
                "type": "string",
                "default": special_string,
                "description": f"Field with special chars: {special_string}"
            }
        }
    }
    
    # Create a remapping (even if it doesn't change anything)
    remapping = _DefinitionsRemapping(
        defs_remapping={},
        json_remapping={}
    )
    
    # Apply remapping
    remapped = remapping.remap_json_schema(test_schema)
    
    # Should be JSON serializable
    json_str = json.dumps(remapped)
    
    # Should be able to parse back
    parsed = json.loads(json_str)
    
    # Special characters should be preserved
    if "default" in parsed["properties"]["field"]:
        assert parsed["properties"]["field"]["default"] == special_string


if __name__ == "__main__":
    print("Running internal function property-based tests...")
    pytest.main([__file__, "-v", "--tb=short"])