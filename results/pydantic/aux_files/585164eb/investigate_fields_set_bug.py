"""Investigate potential bug with model_construct and _fields_set"""

from pydantic import RootModel
from typing import Dict


class TestRootModel(RootModel[Dict[str, int]]):
    pass


def test_fields_set_behavior():
    """Test if model_construct incorrectly preserves invalid fields in _fields_set"""
    
    print("=== Testing model_construct with _fields_set ===")
    
    # Test 1: Normal construction - should only have 'root'
    normal = TestRootModel({'a': 1})
    print(f"Normal construction fields_set: {normal.__pydantic_fields_set__}")
    assert normal.__pydantic_fields_set__ == {'root'}
    
    # Test 2: model_construct with only 'root' in fields_set
    constructed1 = TestRootModel.model_construct({'b': 2}, _fields_set={'root'})
    print(f"model_construct with {{'root'}} fields_set: {constructed1.__pydantic_fields_set__}")
    assert constructed1.__pydantic_fields_set__ == {'root'}
    
    # Test 3: model_construct with empty fields_set
    constructed2 = TestRootModel.model_construct({'c': 3}, _fields_set=set())
    print(f"model_construct with empty fields_set: {constructed2.__pydantic_fields_set__}")
    assert constructed2.__pydantic_fields_set__ == set()
    
    # Test 4: model_construct with invalid fields (THIS IS THE BUG)
    constructed3 = TestRootModel.model_construct({'d': 4}, _fields_set={'root', 'invalid', 'other'})
    print(f"model_construct with {{'root', 'invalid', 'other'}} fields_set: {constructed3.__pydantic_fields_set__}")
    
    # Expected: Should only contain 'root' since that's the only field in RootModel
    # Actual: Contains all provided fields including invalid ones
    print(f"RootModel fields: {list(constructed3.__pydantic_fields__.keys())}")
    print(f"Contains invalid fields? {'invalid' in constructed3.__pydantic_fields_set__}")
    
    # This is problematic because:
    # 1. RootModel only has one field: 'root'
    # 2. __pydantic_fields_set__ should only track actual fields
    # 3. Invalid field names shouldn't be preserved
    
    # Test that the invalid fields cause issues with other operations
    print("\n=== Testing impact of invalid fields_set ===")
    
    # Copy operation
    import copy
    copied = copy.copy(constructed3)
    print(f"Copied model fields_set: {copied.__pydantic_fields_set__}")
    
    # Deepcopy operation
    deepcopied = copy.deepcopy(constructed3)
    print(f"Deepcopied model fields_set: {deepcopied.__pydantic_fields_set__}")
    
    # Pickle operation
    import pickle
    pickled = pickle.dumps(constructed3)
    unpickled = pickle.loads(pickled)
    print(f"Unpickled model fields_set: {unpickled.__pydantic_fields_set__}")
    
    # All operations preserve the invalid fields
    return constructed3


def test_basemodel_comparison():
    """Compare with regular BaseModel behavior"""
    from pydantic import BaseModel
    
    print("\n=== Comparing with BaseModel behavior ===")
    
    class RegularModel(BaseModel):
        root: Dict[str, int]
    
    # BaseModel with model_construct
    regular = RegularModel.model_construct(root={'e': 5}, _fields_set={'root', 'invalid'})
    print(f"BaseModel fields_set with invalid field: {regular.__pydantic_fields_set__}")
    
    # BaseModel also preserves invalid fields!
    # This might be intentional behavior for model_construct (bypass validation)
    # But it could lead to issues if code assumes fields_set only contains valid fields


if __name__ == "__main__":
    model = test_fields_set_behavior()
    test_basemodel_comparison()
    
    print("\n=== Summary ===")
    print("model_construct allows invalid field names in _fields_set")
    print("This affects both RootModel and BaseModel")
    print("The invalid fields are preserved through copy/pickle operations")
    print("This could be a bug if other code assumes fields_set only contains valid fields")