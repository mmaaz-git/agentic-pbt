import gc
import sys
from django.dispatch import Signal


def investigate_references():
    """Investigate why receivers might not be garbage collected in Hypothesis test."""
    signal = Signal()
    
    # Recreate the pattern from the failing test
    def create_and_connect_receivers():
        receivers = []
        for i in range(1):  # Using 1 as in the failing test
            def make_receiver(idx):
                def receiver(sender, **kwargs):
                    return f"response_{idx}"
                return receiver
            
            recv = make_receiver(i)
            receivers.append(recv)
            signal.connect(recv, weak=True)
        return receivers
    
    # Connect receivers
    receivers = create_and_connect_receivers()
    
    print("Initial state:")
    print(f"  Has listeners: {signal.has_listeners()}")
    print(f"  Send responses: {signal.send(sender=None)}")
    print(f"  Receiver refcount: {sys.getrefcount(receivers[0])}")
    
    # Store the receiver to check references
    recv_to_check = receivers[0]
    
    # Check who's referencing it
    print(f"\nReferences to receiver (before del):")
    print(f"  Reference count: {sys.getrefcount(recv_to_check)}")
    
    # Delete receivers
    del receivers
    
    print(f"\nAfter del receivers:")
    print(f"  Reference count: {sys.getrefcount(recv_to_check)}")
    print(f"  Has listeners: {signal.has_listeners()}")
    
    # Force GC
    gc.collect()
    
    print(f"\nAfter gc.collect():")
    print(f"  Reference count: {sys.getrefcount(recv_to_check)}")
    print(f"  Has listeners: {signal.has_listeners()}")
    print(f"  Send responses: {signal.send(sender=None)}")
    
    # Now delete our reference
    del recv_to_check
    gc.collect()
    
    print(f"\nAfter deleting recv_to_check:")
    print(f"  Has listeners: {signal.has_listeners()}")
    print(f"  Send responses: {signal.send(sender=None)}")


def test_closure_references():
    """Test if closure variables affect garbage collection."""
    signal = Signal()
    
    print("\n\n=== Testing closure references ===")
    
    # Pattern 1: Direct nested function
    def pattern1():
        def receiver(sender, **kwargs):
            return "response"
        signal.connect(receiver, weak=True)
        return receiver
    
    recv1 = pattern1()
    print("Pattern 1 (direct nested):")
    print(f"  Before del: {signal.send(sender=None)}")
    del recv1
    gc.collect()
    print(f"  After del+gc: {signal.send(sender=None)}")
    
    # Clear signal
    signal = Signal()
    
    # Pattern 2: Function factory (like in test)
    def pattern2():
        receivers = []
        def make_receiver(idx):
            def receiver(sender, **kwargs):
                return f"response_{idx}"
            return receiver
        
        recv = make_receiver(0)
        receivers.append(recv)
        signal.connect(recv, weak=True)
        return receivers
    
    recv2 = pattern2()
    print("\nPattern 2 (function factory):")
    print(f"  Before del: {signal.send(sender=None)}")
    del recv2
    gc.collect()
    print(f"  After del+gc: {signal.send(sender=None)}")
    
    # Clear signal
    signal = Signal()
    
    # Pattern 3: Using closure variable
    def pattern3():
        receivers = []
        for i in range(1):
            # This creates a closure over 'i'
            def receiver(sender, **kwargs):
                return f"response_{i}"  # Captures 'i'
            receivers.append(receiver)
            signal.connect(receiver, weak=True)
        return receivers
    
    recv3 = pattern3()
    print("\nPattern 3 (closure over loop var):")
    print(f"  Before del: {signal.send(sender=None)}")
    del recv3
    gc.collect()
    print(f"  After del+gc: {signal.send(sender=None)}")


if __name__ == "__main__":
    investigate_references()
    test_closure_references()