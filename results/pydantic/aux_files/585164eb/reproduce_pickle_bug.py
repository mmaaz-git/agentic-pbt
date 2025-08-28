"""Standalone reproduction of pickle issue with RootModel"""

import pickle
from pydantic import RootModel
from typing import List, Dict, Any


def test_local_class_pickle():
    """Test if locally defined RootModel classes can be pickled"""
    
    # Define a RootModel class inside a function (as tests do)
    class LocalModel(RootModel[Dict[str, int]]):
        pass
    
    # Create instance
    model = LocalModel({'a': 1, 'b': 2})
    print(f"Original model: {model.root}")
    
    # Try to pickle
    try:
        pickled = pickle.dumps(model)
        print("✓ Successfully pickled local class")
        restored = pickle.loads(pickled)
        print(f"✓ Restored model: {restored.root}")
        return True
    except AttributeError as e:
        print(f"✗ Failed to pickle local class: {e}")
        return False


def test_global_class_pickle():
    """Test if module-level RootModel classes can be pickled"""
    
    # Create instance of global class  
    model = GlobalModel({'x': 10, 'y': 20})
    print(f"\nOriginal model: {model.root}")
    
    # Try to pickle
    try:
        pickled = pickle.dumps(model)
        print("✓ Successfully pickled global class")
        restored = pickle.loads(pickled)
        print(f"✓ Restored model: {restored.root}")
        return True
    except Exception as e:
        print(f"✗ Failed to pickle global class: {e}")
        return False


# Define a global RootModel class
class GlobalModel(RootModel[Dict[str, int]]):
    pass


if __name__ == "__main__":
    print("=== Testing pickle with RootModel ===")
    
    # Test local class (expected to fail - Python limitation)
    local_result = test_local_class_pickle()
    
    # Test global class (should work if RootModel supports pickle)
    global_result = test_global_class_pickle()
    
    print("\n=== Summary ===")
    print(f"Local class pickle: {'PASS' if local_result else 'FAIL (expected - Python limitation)'}")
    print(f"Global class pickle: {'PASS' if global_result else 'FAIL (BUG!)'}")
    
    # Additional test: verify __getstate__ and __setstate__ work
    print("\n=== Testing __getstate__ and __setstate__ ===")
    model = GlobalModel({'test': 123})
    state = model.__getstate__()
    print(f"State dict keys: {state.keys()}")
    
    # Create new instance and restore state
    new_model = GlobalModel.__new__(GlobalModel)
    new_model.__setstate__(state)
    print(f"Restored via __setstate__: {new_model.root}")
    print(f"Equality check: {new_model.root == model.root}")