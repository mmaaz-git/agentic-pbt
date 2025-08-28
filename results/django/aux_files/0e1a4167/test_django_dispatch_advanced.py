import threading
import time
from hypothesis import given, strategies as st, assume
from django.dispatch import Signal, receiver
import weakref


# Test caching behavior
@given(use_caching=st.booleans(), num_senders=st.integers(min_value=1, max_value=5))
def test_caching_consistency(use_caching, num_senders):
    """Test that caching doesn't affect correctness of signal dispatch."""
    signal = Signal(use_caching=use_caching)
    
    # Create different senders
    senders = [object() for _ in range(num_senders)]
    
    # Connect receivers for specific senders and None
    responses_expected = {}
    
    def make_receiver(sender_id):
        def recv(sender, **kwargs):
            return f"response_for_{sender_id}"
        return recv
    
    # Connect receiver for each sender
    for i, sender in enumerate(senders):
        recv = make_receiver(i)
        signal.connect(recv, sender=sender, weak=False)
        responses_expected[sender] = f"response_for_{i}"
    
    # Connect a receiver for all senders
    def universal_receiver(sender, **kwargs):
        return "universal"
    signal.connect(universal_receiver, sender=None, weak=False)
    
    # Test sending from each sender
    for sender in senders:
        responses = signal.send(sender=sender)
        # Should get response from specific receiver and universal receiver
        assert len(responses) == 2, f"Expected 2 responses for sender, got {len(responses)}"
        
        response_values = [r[1] for r in responses]
        assert responses_expected[sender] in response_values
        assert "universal" in response_values
    
    # Test with a new sender not in list
    new_sender = object()
    responses = signal.send(sender=new_sender)
    # Should only get universal receiver
    assert len(responses) == 1, f"Expected 1 response for new sender, got {len(responses)}"
    assert responses[0][1] == "universal"


# Test edge case with dispatch_uid as None 
@given(use_none_uid=st.booleans())
def test_dispatch_uid_none_handling(use_none_uid):
    """Test that dispatch_uid=None is handled differently from no dispatch_uid."""
    signal = Signal()
    
    def receiver1(sender, **kwargs):
        return "receiver1"
    
    def receiver2(sender, **kwargs):
        return "receiver2"
    
    # Connect with explicit None vs implicit None
    if use_none_uid:
        signal.connect(receiver1, dispatch_uid=None)
        signal.connect(receiver2, dispatch_uid=None)
    else:
        signal.connect(receiver1)
        signal.connect(receiver2)
    
    responses = signal.send(sender=None)
    
    # Both should be connected since dispatch_uid=None means "no dispatch_uid"
    assert len(responses) == 2, f"Expected 2 receivers, got {len(responses)}"


# Test disconnect with mismatched parameters
@given(
    connect_with_sender=st.booleans(),
    disconnect_with_sender=st.booleans(),
    connect_with_uid=st.booleans(),
    disconnect_with_uid=st.booleans()
)
def test_disconnect_parameter_matching(connect_with_sender, disconnect_with_sender, 
                                      connect_with_uid, disconnect_with_uid):
    """Test that disconnect only works with matching parameters."""
    signal = Signal()
    
    sender = object() if connect_with_sender else None
    uid = "test_uid" if connect_with_uid else None
    
    def test_receiver(sender, **kwargs):
        return "response"
    
    # Connect with specific parameters
    signal.connect(test_receiver, sender=sender, dispatch_uid=uid)
    
    # Try to disconnect with potentially different parameters
    disconnect_sender = object() if disconnect_with_sender else None
    disconnect_uid = "test_uid" if disconnect_with_uid else None
    
    result = signal.disconnect(test_receiver, sender=disconnect_sender, dispatch_uid=disconnect_uid)
    
    # Should only disconnect if parameters match
    if connect_with_uid and disconnect_with_uid:
        # dispatch_uid takes precedence - should match if both use same uid
        expected = True
    elif not connect_with_uid and not disconnect_with_uid:
        # No uid, so must match on receiver and sender
        if connect_with_sender == disconnect_with_sender:
            if connect_with_sender:
                # Both have senders but different objects
                expected = False
            else:
                # Both have None sender
                expected = True
        else:
            expected = False
    else:
        # Mismatch in whether uid is used
        expected = False
    
    assert result == expected, f"Expected disconnect={expected}, got {result}"


# Test with bound methods
class TestClass:
    def __init__(self, value):
        self.value = value
        self.called = False
    
    def method_receiver(self, sender, **kwargs):
        self.called = True
        return f"method_{self.value}"


@given(num_instances=st.integers(min_value=1, max_value=5))
def test_bound_method_weak_references(num_instances):
    """Test that bound methods are properly handled with weak references."""
    signal = Signal()
    
    # Create instances and connect their methods
    instances = []
    for i in range(num_instances):
        instance = TestClass(i)
        instances.append(instance)
        signal.connect(instance.method_receiver, weak=True)
    
    # All should respond
    responses = signal.send(sender=None)
    assert len(responses) == num_instances
    
    # Delete one instance
    if num_instances > 1:
        del instances[0]
        import gc
        gc.collect()
        
        # Should have one less listener
        responses = signal.send(sender=None)
        assert len(responses) == num_instances - 1


# Test empty signal behavior
def test_empty_signal_operations():
    """Test operations on signals with no receivers."""
    signal = Signal()
    
    # Empty signal should have no listeners
    assert not signal.has_listeners()
    assert not signal.has_listeners(sender=object())
    
    # Send should return empty list
    assert signal.send(sender=None) == []
    assert signal.send_robust(sender=None) == []
    
    # Disconnect non-existent should return False
    def dummy(sender, **kwargs):
        pass
    
    assert signal.disconnect(dummy) is False
    assert signal.disconnect(dummy, dispatch_uid="nonexistent") is False


# Test receiver decorator with multiple signals
@given(num_signals=st.integers(min_value=1, max_value=5))
def test_receiver_decorator_multiple_signals(num_signals):
    """Test that @receiver decorator works with multiple signals."""
    signals = [Signal() for _ in range(num_signals)]
    
    call_count = [0]
    
    @receiver(signals)
    def multi_receiver(sender, **kwargs):
        call_count[0] += 1
        return "response"
    
    # Send from each signal
    for sig in signals:
        responses = sig.send(sender=None)
        assert len(responses) == 1
        assert responses[0][1] == "response"
    
    # Should have been called once per signal
    assert call_count[0] == num_signals


# Test thread safety of connect/disconnect
def test_concurrent_connect_disconnect():
    """Test that concurrent connect/disconnect operations are thread-safe."""
    signal = Signal()
    errors = []
    
    def connect_disconnect_loop(thread_id):
        try:
            for i in range(50):
                def receiver(sender, **kwargs):
                    return f"thread_{thread_id}_{i}"
                
                # Connect
                signal.connect(receiver, dispatch_uid=f"thread_{thread_id}", weak=False)
                
                # Small delay
                time.sleep(0.001)
                
                # Disconnect
                signal.disconnect(dispatch_uid=f"thread_{thread_id}")
        except Exception as e:
            errors.append(e)
    
    # Run multiple threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=connect_disconnect_loop, args=(i,))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Should have no errors
    assert not errors, f"Thread safety errors: {errors}"
    
    # Final state should be consistent
    assert not signal.has_listeners()


# Test lookup_key generation edge cases
@given(
    use_dispatch_uid=st.booleans(),
    sender_is_none=st.booleans()
)
def test_lookup_key_consistency(use_dispatch_uid, sender_is_none):
    """Test that lookup keys are generated consistently for connect/disconnect."""
    signal = Signal()
    
    sender = None if sender_is_none else object()
    dispatch_uid = "test_uid" if use_dispatch_uid else None
    
    def test_receiver(sender, **kwargs):
        return "response"
    
    # Connect
    signal.connect(test_receiver, sender=sender, dispatch_uid=dispatch_uid)
    
    # Should be able to disconnect with same parameters
    assert signal.disconnect(test_receiver, sender=sender, dispatch_uid=dispatch_uid) is True
    
    # Should not be connected anymore
    assert not signal.has_listeners(sender)
    
    # Second disconnect should return False
    assert signal.disconnect(test_receiver, sender=sender, dispatch_uid=dispatch_uid) is False