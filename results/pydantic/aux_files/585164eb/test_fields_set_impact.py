"""Test if invalid fields_set causes actual issues"""

from pydantic import RootModel, BaseModel
from typing import Dict, Any
import json


class TestRootModel(RootModel[Dict[str, int]]):
    pass


def test_serialization_with_invalid_fields_set():
    """Test if invalid fields_set affects serialization"""
    
    print("=== Testing serialization with invalid fields_set ===")
    
    # Create model with invalid fields in fields_set
    model = TestRootModel.model_construct({'a': 1}, _fields_set={'root', 'invalid', 'fake'})
    print(f"Initial fields_set: {model.__pydantic_fields_set__}")
    
    # Test model_dump with exclude_unset
    dumped_exclude_unset = model.model_dump(exclude_unset=True)
    print(f"model_dump(exclude_unset=True): {dumped_exclude_unset}")
    # Should only dump 'root' since it's the only real field
    
    # Test model_dump with include
    try:
        dumped_include = model.model_dump(include={'invalid'})
        print(f"model_dump(include={{'invalid'}}): {dumped_include}")
    except Exception as e:
        print(f"model_dump(include={{'invalid'}}) error: {e}")
    
    # Test model_dump with exclude  
    dumped_exclude = model.model_dump(exclude={'invalid'})
    print(f"model_dump(exclude={{'invalid'}}): {dumped_exclude}")
    
    # Test model_dump_json with exclude_unset
    json_exclude_unset = model.model_dump_json(exclude_unset=True)
    print(f"model_dump_json(exclude_unset=True): {json_exclude_unset}")
    
    # Test if fields_set affects equality
    model2 = TestRootModel.model_construct({'a': 1}, _fields_set={'root'})
    print(f"\nmodel1 fields_set: {model.__pydantic_fields_set__}")
    print(f"model2 fields_set: {model2.__pydantic_fields_set__}")
    print(f"model1 == model2: {model == model2}")  # Should be True based on root content
    
    # Test if it affects validation
    print("\n=== Testing validation ===")
    model3 = TestRootModel.model_construct({'b': 2}, _fields_set={'invalid'})
    print(f"model3 fields_set (no 'root'): {model3.__pydantic_fields_set__}")
    
    # What happens with exclude_unset when 'root' is not in fields_set?
    dumped3 = model3.model_dump(exclude_unset=True)
    print(f"model_dump(exclude_unset=True) when 'root' not in fields_set: {dumped3}")
    
    # This could be problematic! If 'root' is not in fields_set but invalid fields are,
    # exclude_unset might behave unexpectedly


def test_field_set_filtering():
    """Test if Pydantic filters fields_set internally"""
    
    print("\n=== Testing fields_set filtering ===")
    
    model = TestRootModel.model_construct({'c': 3}, _fields_set={'root', 'invalid'})
    
    # Check if model_fields_set property does any filtering
    print(f"Raw __pydantic_fields_set__: {model.__pydantic_fields_set__}")
    
    # Check if any Pydantic operations filter out invalid fields
    from pydantic import ValidationError
    
    # Try to trigger operations that might use fields_set
    model_copy = model.model_copy()
    print(f"model_copy() fields_set: {model_copy.__pydantic_fields_set__}")
    
    # Check with update
    model_copy2 = model.model_copy(update={'d': 4})
    print(f"model_copy(update=...) fields_set: {model_copy2.__pydantic_fields_set__}")


def test_fields_set_edge_case():
    """Test edge case: no 'root' in fields_set but has invalid fields"""
    
    print("\n=== Testing edge case: only invalid fields in fields_set ===")
    
    # Create model where 'root' is NOT in fields_set, but invalid fields are
    model = TestRootModel.model_construct({'x': 99}, _fields_set={'invalid', 'fake'})
    print(f"Model with only invalid fields in fields_set: {model.__pydantic_fields_set__}")
    print(f"model.root: {model.root}")
    
    # This is definitely wrong - the model has a root value but fields_set says it's unset
    # and instead has non-existent fields marked as set
    
    # Test exclude_unset behavior
    excluded = model.model_dump(exclude_unset=True)
    print(f"model_dump(exclude_unset=True): {excluded}")
    
    # Expected: {} since 'root' is not in fields_set
    # This means data is lost!
    
    json_str = model.model_dump_json(exclude_unset=True)
    print(f"model_dump_json(exclude_unset=True): {json_str}")
    
    # If this returns {}, it's a data loss bug
    return model


if __name__ == "__main__":
    test_serialization_with_invalid_fields_set()
    test_field_set_filtering()
    problematic_model = test_fields_set_edge_case()
    
    print("\n=== POTENTIAL BUG FOUND ===")
    print("model_construct allows setting _fields_set with invalid field names")
    print("This can cause data loss when using exclude_unset=True")
    print("If 'root' is not in fields_set but the model has data, exclude_unset ignores it!")