"""
Focused test to investigate the potential mutation bug in cloudpickle
"""
import pickle
import sys

# Add the virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

import srsly.cloudpickle as cloudpickle


def test_nested_closure_mutation():
    """Test if nested closures with mutations are preserved correctly"""
    
    def outer():
        data = [1, 2, 3]
        
        def middle():
            data.append(99)
            
            def inner():
                return sum(data)
            
            return inner
        
        return middle
    
    # Create the function chain
    func = outer()
    inner_func = func()
    
    # Get initial result
    initial_result = inner_func()
    print(f"Initial result: {initial_result}")
    print(f"Expected: sum([1, 2, 3, 99]) = {1 + 2 + 3 + 99}")
    
    # Round-trip the middle function
    serialized = cloudpickle.dumps(func)
    restored_func = pickle.loads(serialized)
    
    # Call the restored function to get the inner function
    restored_inner = restored_func()
    
    # Check the result
    restored_result = restored_inner()
    print(f"Restored result: {restored_result}")
    
    # The issue: Does calling restored_func() mutate the closure again?
    # If it does, we'd get [1, 2, 3, 99, 99] instead of [1, 2, 3, 99]
    
    if restored_result != initial_result:
        print(f"BUG FOUND: Expected {initial_result}, got {restored_result}")
        print("The closure appears to be mutated again after deserialization!")
        return False
    
    return True


def test_simpler_mutation():
    """Simpler test case for the mutation issue"""
    
    def make_appender():
        data = []
        
        def append_and_return():
            data.append(1)
            return len(data)
        
        return append_and_return
    
    func = make_appender()
    
    # Call once before pickling
    result1 = func()
    print(f"\nSimpler test - First call result: {result1}")
    
    # Pickle and unpickle
    restored = pickle.loads(cloudpickle.dumps(func))
    
    # Call the restored function
    result2 = restored()
    print(f"Restored function result: {result2}")
    
    # If the closure state is preserved, this should be 2
    # If the closure is reset, this would be 1
    if result2 != 2:
        print(f"State not preserved correctly! Expected 2, got {result2}")
        return False
    
    return True


def test_mutation_with_nested_call():
    """Test the exact scenario from the failing test"""
    values = [0]
    
    def outer():
        data = list(values)
        
        def middle():
            data.append(99)
            
            def inner():
                return sum(data)
            
            return inner
        
        return middle
    
    func = outer()
    inner_func = func()  # This appends 99 to data
    
    # Get initial result
    initial_result = inner_func()
    print(f"\nNested call test - Initial: {initial_result} (should be {0 + 99})")
    
    # Round-trip the middle function (func)
    restored_func = pickle.loads(cloudpickle.dumps(func))
    
    # This call to restored_func() creates a NEW inner function
    # But does it also append 99 again to the data list?
    restored_inner = restored_func()
    
    # Check the result
    restored_result = restored_inner()
    print(f"Restored: {restored_result}")
    
    if restored_result != initial_result:
        print(f"BUG CONFIRMED: The data list was mutated during unpickling!")
        print(f"Expected sum to be {initial_result}, but got {restored_result}")
        print(f"This suggests data = {[0, 99, 99]} instead of {[0, 99]}")
        return False
    
    return True


if __name__ == "__main__":
    print("Testing nested closure mutations...")
    test1 = test_nested_closure_mutation()
    test2 = test_simpler_mutation()
    test3 = test_mutation_with_nested_call()
    
    if test1 and test2 and test3:
        print("\nAll tests passed - no bug found")
    else:
        print("\nBUG DETECTED in cloudpickle's handling of mutable closures!")