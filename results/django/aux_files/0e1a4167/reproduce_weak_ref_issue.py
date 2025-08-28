import gc
import weakref
from django.dispatch import Signal


def test_weak_reference_issue():
    """Minimal reproduction of weak reference cleanup issue."""
    signal = Signal()
    
    # Create a function and connect it with weak=True
    def receiver(sender, **kwargs):
        return "response"
    
    print("Step 1: Connect receiver with weak=True")
    signal.connect(receiver, weak=True)
    
    print(f"Step 2: Check has_listeners - {signal.has_listeners()}")
    print(f"Step 3: Send signal - responses: {signal.send(sender=None)}")
    
    # Try to trigger cleanup
    print("\nStep 4: Delete receiver and run garbage collection")
    del receiver
    gc.collect()
    
    print(f"Step 5: Check has_listeners after GC - {signal.has_listeners()}")
    print(f"Step 6: Send signal after GC - responses: {signal.send(sender=None)}")
    
    # Check internal state
    print(f"\nInternal state - receivers: {signal.receivers}")
    
    # Try with multiple GC cycles
    print("\nStep 7: Run multiple GC cycles")
    for i in range(3):
        gc.collect()
        print(f"  After GC cycle {i+1}: has_listeners={signal.has_listeners()}, responses={signal.send(sender=None)}")


def test_weak_reference_with_local_function():
    """Test with function created in local scope."""
    signal = Signal()
    
    def create_and_connect():
        def receiver(sender, **kwargs):
            return "response"
        signal.connect(receiver, weak=True)
        return receiver
    
    print("\n\n=== Test with local function ===")
    print("Step 1: Create and connect receiver in local scope")
    recv = create_and_connect()
    
    print(f"Step 2: Send signal - responses: {signal.send(sender=None)}")
    
    print("Step 3: Delete reference and GC")
    del recv
    gc.collect()
    
    print(f"Step 4: Send signal after GC - responses: {signal.send(sender=None)}")
    
    # Check if the receiver is really gone
    print(f"Step 5: Check receivers list: {signal.receivers}")
    
    # Check dead receivers flag
    print(f"Step 6: Dead receivers flag: {signal._dead_receivers}")


def test_comparison_with_plain_weakref():
    """Compare Django's behavior with plain weakref."""
    print("\n\n=== Comparison with plain weakref ===")
    
    # Test plain weakref behavior
    def test_func():
        return "test"
    
    weak_ref = weakref.ref(test_func)
    print(f"Before deletion: weak_ref() = {weak_ref()}")
    
    del test_func
    gc.collect()
    
    print(f"After deletion and GC: weak_ref() = {weak_ref()}")
    
    # Now test with a nested function
    def create_func():
        def inner():
            return "inner"
        return inner
    
    func = create_func()
    weak_ref2 = weakref.ref(func)
    print(f"\nNested function before deletion: weak_ref2() = {weak_ref2()}")
    
    del func
    gc.collect()
    
    print(f"Nested function after deletion and GC: weak_ref2() = {weak_ref2()}")


if __name__ == "__main__":
    test_weak_reference_issue()
    test_weak_reference_with_local_function()
    test_comparison_with_plain_weakref()