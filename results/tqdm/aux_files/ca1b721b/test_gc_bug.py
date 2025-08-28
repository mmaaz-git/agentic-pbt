"""
Test for potential garbage collection bug in tqdm.notebook
"""
import gc
from tqdm.notebook import tqdm_notebook

def test_gc_with_disabled():
    """Test that tqdm_notebook properly handles garbage collection when disabled"""
    # Create a disabled tqdm_notebook that goes out of scope
    def create_and_abandon():
        t = tqdm_notebook(range(10), disable=True)
        # Don't explicitly close it
        return None
    
    # This should not raise an error
    create_and_abandon()
    gc.collect()  # Force garbage collection
    

def test_close_after_partial_init():
    """Test close() behavior after partial initialization"""
    # Test with disable=True
    t1 = tqdm_notebook(range(10), disable=True)
    print(f"Has disp: {hasattr(t1, 'disp')}")
    t1.close()  # Should not error
    
    # Test with gui=False (different path)
    t2 = tqdm_notebook(range(10), gui=False, disable=False)
    print(f"Has disp: {hasattr(t2, 'disp')}")
    t2.close()  # Should not error


def test_disp_attribute_consistency():
    """Verify disp attribute is always set correctly"""
    # Case 1: disabled
    t1 = tqdm_notebook(total=10, disable=True)
    assert hasattr(t1, 'disp'), "disabled tqdm should have disp attribute"
    assert callable(t1.disp), "disp should be callable"
    
    # Case 2: gui=False
    t2 = tqdm_notebook(total=10, gui=False)
    assert hasattr(t2, 'disp'), "gui=False tqdm should have disp attribute"
    assert callable(t2.disp), "disp should be callable"
    
    # Clean up
    t1.close()
    t2.close()


if __name__ == "__main__":
    print("Testing GC bug...")
    test_gc_with_disabled()
    print("✓ GC test passed")
    
    print("\nTesting close after partial init...")
    test_close_after_partial_init()
    print("✓ Close test passed")
    
    print("\nTesting disp attribute consistency...")
    test_disp_attribute_consistency()
    print("✓ Disp attribute test passed")
    
    print("\nAll tests passed!")