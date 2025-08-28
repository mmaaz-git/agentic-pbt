import weakref
from hypothesis import given, strategies as st, assume, settings
from django.dispatch import Signal, receiver
import gc


# Strategy for generating unique ids
unique_ids = st.text(min_size=1, max_size=20)


# Test property 1: Connect/disconnect round-trip
@given(dispatch_uid=st.one_of(st.none(), unique_ids))
def test_connect_disconnect_roundtrip(dispatch_uid):
    """After connecting a receiver, disconnecting it should return True."""
    signal = Signal()
    
    def test_receiver(sender, **kwargs):
        pass
    
    # Connect the receiver
    signal.connect(test_receiver, dispatch_uid=dispatch_uid)
    
    # Disconnect should return True since it was connected
    result = signal.disconnect(test_receiver, dispatch_uid=dispatch_uid)
    assert result is True, f"Expected disconnect to return True after connect, got {result}"
    
    # Second disconnect should return False since already disconnected
    result2 = signal.disconnect(test_receiver, dispatch_uid=dispatch_uid)
    assert result2 is False, f"Expected second disconnect to return False, got {result2}"


# Test property 2: dispatch_uid prevents duplicates
@given(dispatch_uid=unique_ids, num_connects=st.integers(min_value=2, max_value=10))
def test_dispatch_uid_prevents_duplicates(dispatch_uid, num_connects):
    """Connecting multiple times with same dispatch_uid should not create duplicates."""
    signal = Signal()
    
    def test_receiver(sender, **kwargs):
        return "response"
    
    # Connect multiple times with same dispatch_uid
    for _ in range(num_connects):
        signal.connect(test_receiver, dispatch_uid=dispatch_uid)
    
    # Send signal and count responses
    responses = signal.send(sender=None)
    
    # Should only have one response despite multiple connects
    assert len(responses) == 1, f"Expected 1 response with dispatch_uid, got {len(responses)}"


# Test property 3: send returns correct format
@given(num_receivers=st.integers(min_value=0, max_value=10))
def test_send_returns_tuple_list(num_receivers):
    """send() should return list of (receiver, response) tuples."""
    signal = Signal()
    receivers = []
    
    for i in range(num_receivers):
        def make_receiver(idx):
            def receiver(sender, **kwargs):
                return f"response_{idx}"
            return receiver
        
        recv = make_receiver(i)
        receivers.append(recv)
        signal.connect(recv, weak=False)
    
    responses = signal.send(sender=None)
    
    # Check it's a list
    assert isinstance(responses, list), f"Expected list, got {type(responses)}"
    
    # Check length matches number of receivers
    assert len(responses) == num_receivers, f"Expected {num_receivers} responses, got {len(responses)}"
    
    # Check each item is a tuple of (receiver, response)
    for item in responses:
        assert isinstance(item, tuple), f"Expected tuple, got {type(item)}"
        assert len(item) == 2, f"Expected 2-tuple, got {len(item)}-tuple"


# Test property 4: has_listeners consistency
@given(
    num_receivers=st.integers(min_value=0, max_value=10),
    use_weak=st.booleans(),
    use_sender=st.booleans()
)
def test_has_listeners_consistency(num_receivers, use_weak, use_sender):
    """has_listeners should reflect whether receivers are connected."""
    signal = Signal()
    receivers = []
    sender = object() if use_sender else None
    
    # Initially should have no listeners
    assert not signal.has_listeners(sender), "Signal should initially have no listeners"
    
    # Connect receivers
    for i in range(num_receivers):
        def make_receiver(idx):
            def receiver(sender, **kwargs):
                return f"response_{idx}"
            return receiver
        
        recv = make_receiver(i)
        receivers.append(recv)
        signal.connect(recv, sender=sender, weak=use_weak)
    
    # Should have listeners if we connected any
    if num_receivers > 0:
        assert signal.has_listeners(sender), f"Should have listeners after connecting {num_receivers} receivers"
    else:
        assert not signal.has_listeners(sender), "Should have no listeners when num_receivers=0"
    
    # Disconnect all
    for recv in receivers:
        signal.disconnect(recv, sender=sender)
    
    # Should have no listeners after disconnecting all
    assert not signal.has_listeners(sender), "Should have no listeners after disconnecting all"


# Test property 5: send_robust error handling
@given(
    num_good=st.integers(min_value=0, max_value=5),
    num_bad=st.integers(min_value=1, max_value=5),
    error_message=st.text(min_size=1, max_size=50)
)
def test_send_robust_catches_exceptions(num_good, num_bad, error_message):
    """send_robust should catch exceptions and include them in responses."""
    signal = Signal()
    
    # Add receivers that work fine
    good_receivers = []
    for i in range(num_good):
        def make_good_receiver(idx):
            def receiver(sender, **kwargs):
                return f"good_{idx}"
            return receiver
        
        recv = make_good_receiver(i)
        good_receivers.append(recv)
        signal.connect(recv, weak=False)
    
    # Add receivers that raise exceptions
    bad_receivers = []
    for i in range(num_bad):
        def make_bad_receiver(idx, msg):
            def receiver(sender, **kwargs):
                raise ValueError(f"{msg}_{idx}")
            return receiver
        
        recv = make_bad_receiver(i, error_message)
        bad_receivers.append(recv)
        signal.connect(recv, weak=False)
    
    # Use send_robust
    responses = signal.send_robust(sender=None)
    
    # Should get responses for all receivers
    assert len(responses) == num_good + num_bad, f"Expected {num_good + num_bad} responses, got {len(responses)}"
    
    # Count exceptions and normal responses
    exceptions = []
    normal_responses = []
    
    for receiver, response in responses:
        if isinstance(response, Exception):
            exceptions.append(response)
        else:
            normal_responses.append(response)
    
    # Should have caught all the exceptions
    assert len(exceptions) == num_bad, f"Expected {num_bad} exceptions, got {len(exceptions)}"
    assert len(normal_responses) == num_good, f"Expected {num_good} normal responses, got {len(normal_responses)}"
    
    # Check exception messages contain our error_message
    for exc in exceptions:
        assert error_message in str(exc), f"Expected '{error_message}' in exception message '{exc}'"


# Test for weak reference cleanup
@given(num_receivers=st.integers(min_value=1, max_value=10))
@settings(max_examples=50)
def test_weak_reference_cleanup(num_receivers):
    """Weak references should be cleaned up when receivers are garbage collected."""
    signal = Signal()
    
    # Create receivers in a scope so they can be garbage collected
    def create_and_connect_receivers():
        receivers = []
        for i in range(num_receivers):
            def make_receiver(idx):
                def receiver(sender, **kwargs):
                    return f"response_{idx}"
                return receiver
            
            recv = make_receiver(i)
            receivers.append(recv)
            signal.connect(recv, weak=True)  # Use weak references
        return receivers
    
    # Connect receivers
    receivers = create_and_connect_receivers()
    
    # Should have listeners
    assert signal.has_listeners(), f"Should have {num_receivers} listeners"
    
    # Send should get responses from all
    responses = signal.send(sender=None)
    assert len(responses) == num_receivers, f"Expected {num_receivers} responses, got {len(responses)}"
    
    # Delete receivers and force garbage collection
    del receivers
    gc.collect()
    
    # Give weak references time to be cleared
    # Send signal again - weak refs should be gone
    responses = signal.send(sender=None)
    assert len(responses) == 0, f"Expected 0 responses after GC, got {len(responses)}"
    
    # Should have no listeners
    assert not signal.has_listeners(), "Should have no listeners after garbage collection"