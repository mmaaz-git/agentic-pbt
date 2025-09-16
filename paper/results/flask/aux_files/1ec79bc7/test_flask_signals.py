import gc
import weakref
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, Bundle
from flask.signals import *
from blinker import Signal, Namespace, ANY
import sys


# Test 1: Namespace.signal() idempotence - documented in base.py line 488
@given(st.text(min_size=1), st.text())
def test_namespace_signal_idempotence(name, doc):
    """Repeated calls with the same name return the same signal object."""
    ns = Namespace()
    
    signal1 = ns.signal(name, doc)
    signal2 = ns.signal(name)  # doc is optional on repeated calls
    signal3 = ns.signal(name, "different doc")
    
    # All should be the exact same object
    assert signal1 is signal2
    assert signal2 is signal3
    assert id(signal1) == id(signal2) == id(signal3)


# Test 2: Signal connect/disconnect round-trip property
@given(st.integers(), st.integers())
def test_signal_connect_disconnect_roundtrip(sender_val, data):
    """Connected receivers should be called; disconnected should not."""
    signal = Signal()
    results = []
    
    def receiver(sender, **kwargs):
        results.append((sender, kwargs))
        return data
    
    # Initially, no receivers
    ret = signal.send(sender_val, test_data=data)
    assert ret == []
    assert len(results) == 0
    
    # After connect, receiver should be called
    signal.connect(receiver)
    ret = signal.send(sender_val, test_data=data)
    assert len(ret) == 1
    assert ret[0] == (receiver, data)
    assert len(results) == 1
    assert results[0] == (sender_val, {'test_data': data})
    
    # After disconnect, receiver should not be called
    results.clear()
    signal.disconnect(receiver)
    ret = signal.send(sender_val, test_data=data)
    assert ret == []
    assert len(results) == 0


# Test 3: Signal muting property - documented behavior
@given(st.integers(), st.integers())
def test_signal_muting_invariant(sender_val, data):
    """When muted, send() returns empty list and receivers aren't called."""
    signal = Signal()
    called = []
    
    def receiver(sender, **kwargs):
        called.append(sender)
        return data
    
    signal.connect(receiver)
    
    # Normal send works
    ret = signal.send(sender_val)
    assert len(ret) == 1
    assert len(called) == 1
    
    # When muted, no calls
    called.clear()
    signal.is_muted = True
    ret = signal.send(sender_val)
    assert ret == []  # Documented: returns empty list when muted
    assert len(called) == 0
    
    # Unmuted works again
    signal.is_muted = False
    ret = signal.send(sender_val)
    assert len(ret) == 1
    assert len(called) == 1


# Test 4: ANY sender behavior
@given(st.lists(st.integers(), min_size=1, max_size=5))
def test_any_sender_receives_all(senders):
    """Receivers connected to ANY should receive all sends."""
    signal = Signal()
    any_calls = []
    specific_calls = []
    
    def any_receiver(sender, **kwargs):
        any_calls.append(sender)
        return "any"
    
    def specific_receiver(sender, **kwargs):
        specific_calls.append(sender)
        return "specific"
    
    # Connect one to ANY, one to specific sender
    signal.connect(any_receiver, sender=ANY)
    if senders:
        signal.connect(specific_receiver, sender=senders[0])
    
    # Send from each sender
    for sender in senders:
        signal.send(sender)
    
    # ANY receiver should have received all
    assert any_calls == senders
    
    # Specific receiver only gets its sender
    if senders:
        assert specific_calls == [s for s in senders if s == senders[0]]


# Test 5: Send return value structure
@given(
    st.lists(st.tuples(st.text(min_size=1), st.integers()), min_size=0, max_size=5),
    st.integers()
)
def test_send_return_structure(receiver_data, sender):
    """send() always returns list of (receiver, return_value) tuples."""
    signal = Signal()
    receivers = []
    
    for name, ret_val in receiver_data:
        def make_receiver(rv):
            def receiver(sender, **kwargs):
                return rv
            receiver.__name__ = name
            return receiver
        
        rec = make_receiver(ret_val)
        receivers.append((rec, ret_val))
        signal.connect(rec)
    
    result = signal.send(sender)
    
    # Must be a list
    assert isinstance(result, list)
    
    # Each item must be (callable, value) tuple
    for item in result:
        assert isinstance(item, tuple)
        assert len(item) == 2
        assert callable(item[0])
    
    # Check we got the right return values
    assert len(result) == len(receivers)
    returned_values = {r[1] for r in result}
    expected_values = {rv for _, rv in receiver_data}
    assert returned_values == expected_values


# Test 6: Context manager invariants
@given(st.integers(), st.integers())
def test_connected_to_context_manager(sender_val, data):
    """connected_to context manager should connect/disconnect properly."""
    signal = Signal()
    calls = []
    
    def receiver(sender, **kwargs):
        calls.append(sender)
        return data
    
    # Before context: not connected
    signal.send(sender_val)
    assert len(calls) == 0
    
    # During context: connected
    with signal.connected_to(receiver):
        signal.send(sender_val)
        assert len(calls) == 1
        assert calls[0] == sender_val
    
    # After context: disconnected
    calls.clear()
    signal.send(sender_val)
    assert len(calls) == 0


@given(st.integers())
def test_muted_context_manager(sender_val):
    """muted context manager should mute/unmute properly."""
    signal = Signal()
    calls = []
    
    def receiver(sender, **kwargs):
        calls.append(sender)
    
    signal.connect(receiver)
    
    # Before context: not muted
    signal.send(sender_val)
    assert len(calls) == 1
    
    # During context: muted
    calls.clear()
    with signal.muted():
        signal.send(sender_val)
        assert len(calls) == 0
        assert signal.is_muted == True
    
    # After context: unmuted
    assert signal.is_muted == False
    signal.send(sender_val)
    assert len(calls) == 1


# Test 7: Multiple receivers order independence for results
@given(
    st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=10, unique=True)
)
def test_multiple_receivers_all_called(return_values):
    """All connected receivers should be called and return their values."""
    signal = Signal()
    receivers = []
    
    for val in return_values:
        def make_receiver(v):
            def receiver(sender, **kwargs):
                return v
            return receiver
        rec = make_receiver(val)
        receivers.append(rec)
        signal.connect(rec)
    
    results = signal.send("test")
    
    # All receivers called
    assert len(results) == len(return_values)
    
    # All return values present (order may vary due to set usage)
    returned = sorted([r[1] for r in results])
    expected = sorted(return_values)
    assert returned == expected


# Test 8: Weakref cleanup behavior
@given(st.integers())
def test_weakref_receiver_cleanup(data):
    """Weakly referenced receivers should auto-disconnect when garbage collected."""
    signal = Signal()
    calls = []
    
    def make_receiver():
        def receiver(sender, **kwargs):
            calls.append(sender)
            return data
        return receiver
    
    # Connect with weak=True (default)
    receiver = make_receiver()
    signal.connect(receiver, weak=True)
    
    # Should work initially
    signal.send("test")
    assert len(calls) == 1
    
    # Delete receiver and force garbage collection
    calls.clear()
    receiver_id = id(receiver)
    del receiver
    gc.collect()
    
    # Should not be called after GC
    signal.send("test")
    assert len(calls) == 0


# Test 9: Duplicate connect behavior
@given(st.integers(), st.lists(st.integers(), min_size=1, max_size=5))
def test_duplicate_connect_single_call(data, senders):
    """Connecting same receiver multiple times to same sender shouldn't duplicate calls."""
    signal = Signal()
    calls = []
    
    def receiver(sender, **kwargs):
        calls.append(sender)
        return data
    
    # Connect multiple times to same sender
    for _ in range(3):
        signal.connect(receiver, sender=senders[0] if senders else ANY)
    
    signal.send(senders[0] if senders else "test")
    
    # Should only be called once despite multiple connects
    assert len(calls) == 1


# Test 10: NamedSignal name persistence
@given(st.text(min_size=1), st.text())
def test_named_signal_name_property(name, doc):
    """NamedSignal should maintain its name property."""
    from blinker import NamedSignal
    
    sig = NamedSignal(name, doc)
    assert sig.name == name
    
    # Name should be immutable through normal usage
    sig2 = NamedSignal(name + "_modified", doc)
    assert sig.name == name  # Original unchanged
    assert sig2.name == name + "_modified"