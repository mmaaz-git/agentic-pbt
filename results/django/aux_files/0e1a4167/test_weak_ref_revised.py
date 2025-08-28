import gc
import sys
import weakref
from hypothesis import given, strategies as st, settings
from django.dispatch import Signal


@given(num_receivers=st.integers(min_value=1, max_value=10))
@settings(max_examples=50)
def test_weak_reference_behavior_revised(num_receivers):
    """Test that weak references behave correctly when there are no external references."""
    signal = Signal()
    
    # Track weak refs ourselves to verify cleanup
    weak_refs = []
    
    # Create receivers in a controlled way
    for i in range(num_receivers):
        # Create receiver without storing strong reference
        def make_receiver(idx):
            def receiver(sender, **kwargs):
                return f"response_{idx}"
            return receiver
        
        recv = make_receiver(i)
        weak_refs.append(weakref.ref(recv))
        signal.connect(recv, weak=True)
        # Immediately delete the only strong reference
        del recv
    
    # At this point, only weak references should exist
    # Force garbage collection
    gc.collect()
    
    # Check that weak refs are indeed dead
    alive_count = sum(1 for wr in weak_refs if wr() is not None)
    
    # All weak refs should be dead now
    assert alive_count == 0, f"Expected all weak refs to be dead, but {alive_count}/{num_receivers} are still alive"
    
    # Signal should have no active listeners
    assert not signal.has_listeners(), "Signal should have no listeners after GC"
    
    # Send should return empty list
    responses = signal.send(sender=None)
    assert len(responses) == 0, f"Expected 0 responses, got {len(responses)}"


def test_weak_reference_finalization():
    """Test that weakref finalization triggers dead receiver cleanup."""
    signal = Signal()
    
    # Track if finalization happens
    finalized = []
    
    def receiver(sender, **kwargs):
        return "response"
    
    # Connect with weak reference
    signal.connect(receiver, weak=True)
    
    # Set up finalization callback
    weakref.finalize(receiver, lambda: finalized.append(True))
    
    # Should have listener
    assert signal.has_listeners()
    
    # Delete receiver
    del receiver
    gc.collect()
    
    # Check finalization happened
    assert finalized, "Finalization should have occurred"
    
    # Dead receivers flag should be set
    assert signal._dead_receivers, "Dead receivers flag should be set"
    
    # Next operation should clean up dead receivers
    assert not signal.has_listeners(), "Should have no listeners after cleanup"


def test_strong_vs_weak_references():
    """Compare behavior of strong vs weak references."""
    signal_weak = Signal()
    signal_strong = Signal()
    
    def create_receiver(idx):
        def receiver(sender, **kwargs):
            return f"response_{idx}"
        return receiver
    
    # Test weak references
    recv_weak = create_receiver(1)
    signal_weak.connect(recv_weak, weak=True)
    weak_ref = weakref.ref(recv_weak)
    
    # Test strong references  
    recv_strong = create_receiver(2)
    signal_strong.connect(recv_strong, weak=False)
    strong_ref = weakref.ref(recv_strong)
    
    # Delete local references
    del recv_weak
    del recv_strong
    gc.collect()
    
    # Weak ref should be dead
    assert weak_ref() is None, "Weak reference should be dead after GC"
    assert not signal_weak.has_listeners(), "Weak signal should have no listeners"
    
    # Strong ref should still be alive (held by signal)
    assert strong_ref() is not None, "Strong reference should be alive (held by signal)"
    assert signal_strong.has_listeners(), "Strong signal should still have listeners"
    
    # Strong signal should still work
    responses = signal_strong.send(sender=None)
    assert len(responses) == 1, "Strong signal should still send to receiver"


if __name__ == "__main__":
    # Run revised tests
    print("Testing revised weak reference behavior...")
    test_weak_reference_behavior_revised(5)
    print("✓ Revised weak reference test passed")
    
    print("\nTesting finalization...")
    test_weak_reference_finalization()
    print("✓ Finalization test passed")
    
    print("\nTesting strong vs weak...")
    test_strong_vs_weak_references()
    print("✓ Strong vs weak test passed")