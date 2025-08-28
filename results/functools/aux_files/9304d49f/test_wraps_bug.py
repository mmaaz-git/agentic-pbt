"""Minimal test case for functools.wraps bug with classes"""
import functools


def test_wraps_fails_on_classes():
    """functools.wraps should work with classes but fails due to mappingproxy"""
    
    class OriginalClass:
        """Original class documentation"""
        class_var = "test"
    
    # This should work but raises AttributeError
    try:
        @functools.wraps(OriginalClass)
        class WrapperClass:
            """Wrapper class documentation"""
            pass
        
        # If it worked, these assertions should pass
        assert WrapperClass.__doc__ == "Original class documentation"
        assert WrapperClass.__name__ == "OriginalClass"
        
    except AttributeError as e:
        # This is the bug - class __dict__ is a mappingproxy without update()
        assert "'mappingproxy' object has no attribute 'update'" in str(e)
        print(f"Bug confirmed: {e}")
        return True
    
    return False


def test_update_wrapper_fails_on_classes():
    """functools.update_wrapper also fails with classes"""
    
    class OriginalClass:
        """Original class"""
        pass
    
    class WrapperClass:
        """Wrapper class"""
        pass
    
    try:
        functools.update_wrapper(WrapperClass, OriginalClass)
        return False
    except AttributeError as e:
        assert "'mappingproxy' object has no attribute 'update'" in str(e)
        print(f"update_wrapper also affected: {e}")
        return True


if __name__ == "__main__":
    bug1 = test_wraps_fails_on_classes()
    bug2 = test_update_wrapper_fails_on_classes()
    
    if bug1 and bug2:
        print("\n✗ BUG CONFIRMED: functools.wraps and update_wrapper fail with classes")
        print("  Problem: Class __dict__ is a mappingproxy without update() method")
        print("  Location: functools.py line 59")