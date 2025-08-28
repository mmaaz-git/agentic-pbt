"""
Minimal reproduction of the cloudpickle mutable closure bug
"""
import pickle
import sys

sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')
import srsly.cloudpickle as cloudpickle


def reproduce_bug():
    """Minimal reproduction of the bug"""
    
    def make_mutating_function():
        data = []
        
        def mutate_and_return():
            data.append(1)  # Side effect: modifies closure
            
            def get_length():
                return len(data)
            
            return get_length
        
        return mutate_and_return
    
    # Create the function
    mutating_func = make_mutating_function()
    
    # Call it once - this appends 1 to data
    inner_func = mutating_func()
    print(f"Before pickling - data length: {inner_func()}")  # Should be 1
    
    # Pickle and unpickle the mutating function
    pickled = cloudpickle.dumps(mutating_func)
    restored_mutating_func = pickle.loads(pickled)
    
    # Call the restored function - this SHOULD NOT append again
    # but it does, which is the bug
    restored_inner = restored_mutating_func()
    print(f"After unpickling - data length: {restored_inner()}")  # Should be 1, but is 2!
    
    # Verify the bug
    if restored_inner() != inner_func():
        print("\n✗ BUG CONFIRMED: Calling the unpickled function re-executes side effects")
        print("  The closure was mutated during the function call after unpickling")
        return True
    return False


if __name__ == "__main__":
    print("=== Minimal Bug Reproduction ===\n")
    if reproduce_bug():
        print("\nThis violates the round-trip property: the restored function")
        print("does not behave identically to the original function.")