"""
Minimal reproduction of the caching bug in django.dispatch.Signal
"""
from django.dispatch import Signal


def reproduce_caching_bug():
    print("=== Reproducing WeakKeyDictionary TypeError Bug ===\n")
    
    # Create a signal with caching enabled
    signal = Signal(use_caching=True)
    
    # Create a simple receiver
    def receiver(sender, **kwargs):
        return "response"
    
    # Connect the receiver
    signal.connect(receiver, weak=False)
    print("✓ Connected receiver to signal with caching enabled")
    
    # Create a plain object as sender
    sender = object()
    print(f"✓ Created sender: {sender}")
    
    # Try to send signal - this should fail with TypeError
    print("\nAttempting to send signal...")
    try:
        responses = signal.send(sender=sender)
        print(f"ERROR: Expected TypeError but got responses: {responses}")
    except TypeError as e:
        print(f"✓ Got expected TypeError: {e}")
        print("\nBUG CONFIRMED: Signal with use_caching=True crashes when sender is")
        print("a plain object() that cannot be weakly referenced.")
        return True
    
    return False


def test_weakrefable_senders():
    """Test which types of senders work with caching."""
    print("\n=== Testing Different Sender Types with Caching ===\n")
    
    def receiver(sender, **kwargs):
        return "response"
    
    # Test different sender types
    test_cases = [
        ("object()", object()),
        ("int (42)", 42),
        ("str ('test')", "test"),
        ("list ([1,2,3])", [1, 2, 3]),
        ("dict ({'a': 1})", {'a': 1}),
        ("custom class instance", type('CustomClass', (), {})()),
    ]
    
    for name, sender in test_cases:
        signal = Signal(use_caching=True)
        signal.connect(receiver, weak=False)
        
        try:
            responses = signal.send(sender=sender)
            print(f"✓ {name}: Works with caching (got {len(responses)} responses)")
        except TypeError as e:
            print(f"✗ {name}: FAILS with caching - {e}")


def test_workaround():
    """Test if there's a workaround for the bug."""
    print("\n=== Testing Potential Workarounds ===\n")
    
    # Create a weakrefable wrapper
    class WeakrefableSender:
        pass
    
    signal = Signal(use_caching=True)
    
    def receiver(sender, **kwargs):
        return "response"
    
    signal.connect(receiver, weak=False)
    
    # Use weakrefable sender instead of plain object
    sender = WeakrefableSender()
    
    try:
        responses = signal.send(sender=sender)
        print(f"✓ Workaround: Use a class instance instead of object()")
        print(f"  Got {len(responses)} responses: {responses}")
    except Exception as e:
        print(f"✗ Workaround failed: {e}")


if __name__ == "__main__":
    bug_found = reproduce_caching_bug()
    test_weakrefable_senders()
    test_workaround()
    
    if bug_found:
        print("\n" + "="*50)
        print("BUG SUMMARY:")
        print("- Signal(use_caching=True) crashes with TypeError")
        print("- Happens when sender is a non-weakrefable object")
        print("- Plain object() instances cannot be weakly referenced")
        print("- This is a REAL BUG that affects any code using cached signals")
        print("="*50)