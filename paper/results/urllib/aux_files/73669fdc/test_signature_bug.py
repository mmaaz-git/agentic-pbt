import urllib.response
import io
import tempfile
import inspect


def test_signature_compatibility_bug():
    """Test that addbase has a signature compatibility issue with its parent class."""
    
    # Get the parent class signature
    parent_init = tempfile._TemporaryFileWrapper.__init__
    sig = inspect.signature(parent_init)
    print(f"Parent _TemporaryFileWrapper.__init__ signature: {sig}")
    print(f"Parameters: {list(sig.parameters.keys())}")
    
    # Check what addbase actually passes
    print("\nWhat addbase.__init__ does:")
    print("  super(addbase, self).__init__(fp, '<urllib response>', delete=False)")
    
    # In Python 3.12+, _TemporaryFileWrapper added delete_on_close parameter
    # Let's check if this causes issues
    params = sig.parameters
    
    if 'delete_on_close' in params:
        print(f"\n⚠️  Parent expects 'delete_on_close' parameter (added in Python 3.12+)")
        print(f"  Default value: {params['delete_on_close'].default}")
        
        # Check if the default handles the missing parameter
        if params['delete_on_close'].default == inspect.Parameter.empty:
            print("  ❌ No default value - this could cause TypeError!")
        else:
            print(f"  ✓ Has default value: {params['delete_on_close'].default}")
    
    # Test actual usage
    fp = io.BytesIO(b"test")
    try:
        base = urllib.response.addbase(fp)
        print("\n✓ addbase creation succeeded")
        base.close()
    except TypeError as e:
        print(f"\n❌ addbase creation failed: {e}")
        return False
    
    return True


def test_delete_on_close_behavior():
    """Test the actual behavior difference with delete_on_close."""
    
    # Create a wrapper directly with delete_on_close=True
    fp1 = io.BytesIO(b"test1")
    wrapper1 = tempfile._TemporaryFileWrapper(fp1, "test1", delete=False, delete_on_close=True)
    
    # Create via addbase (doesn't pass delete_on_close)
    fp2 = io.BytesIO(b"test2")
    wrapper2 = urllib.response.addbase(fp2)
    
    print("Direct wrapper with delete_on_close=True:")
    print(f"  Before close - fp closed: {fp1.closed}")
    wrapper1.close()
    print(f"  After close - fp closed: {fp1.closed}")
    
    print("\naddbase wrapper (no delete_on_close):")
    print(f"  Before close - fp closed: {fp2.closed}")
    wrapper2.close()
    print(f"  After close - fp closed: {fp2.closed}")
    
    # Both should close the underlying file
    assert fp1.closed
    assert fp2.closed


if __name__ == "__main__":
    print("=" * 60)
    print("Testing signature compatibility:")
    print("=" * 60)
    test_signature_compatibility_bug()
    
    print("\n" + "=" * 60)
    print("Testing delete_on_close behavior:")
    print("=" * 60)
    test_delete_on_close_behavior()