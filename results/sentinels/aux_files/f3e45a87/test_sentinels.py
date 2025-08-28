#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sentinels_env/lib/python3.13/site-packages')

import pickle
from hypothesis import given, strategies as st, settings
from sentinels import Sentinel


@given(st.text(min_size=1))
def test_singleton_property(name):
    """Multiple calls to Sentinel(name) should return the same object."""
    sentinel1 = Sentinel(name)
    sentinel2 = Sentinel(name)
    assert sentinel1 is sentinel2
    assert id(sentinel1) == id(sentinel2)


@given(st.text(min_size=1))
def test_pickle_round_trip_identity(name):
    """A pickled and unpickled sentinel should be the same object as the original."""
    original = Sentinel(name)
    pickled = pickle.dumps(original)
    unpickled = pickle.loads(pickled)
    
    assert unpickled is original
    assert id(unpickled) == id(original)
    assert unpickled._name == original._name


@given(st.text(min_size=1))
def test_repr_format(name):
    """String representation should be <name>."""
    sentinel = Sentinel(name)
    expected_repr = f"<{name}>"
    assert repr(sentinel) == expected_repr
    assert str(sentinel) == expected_repr


@given(st.text(min_size=1))
def test_registry_consistency(name):
    """The _existing_instances dict should track all created sentinels correctly."""
    sentinel = Sentinel(name)
    
    assert name in Sentinel._existing_instances
    assert Sentinel._existing_instances[name] is sentinel
    
    # Creating again should not change the registry
    sentinel2 = Sentinel(name)
    assert Sentinel._existing_instances[name] is sentinel
    assert Sentinel._existing_instances[name] is sentinel2


@given(st.lists(st.text(min_size=1), min_size=1, unique=True))
def test_multiple_sentinels_independence(names):
    """Different sentinels should be different objects."""
    sentinels = [Sentinel(name) for name in names]
    
    # All sentinels should be different objects
    for i, s1 in enumerate(sentinels):
        for j, s2 in enumerate(sentinels):
            if i != j:
                assert s1 is not s2
                assert s1._name != s2._name


@given(st.text(min_size=1))
@settings(max_examples=100)
def test_pickle_multiple_times(name):
    """Pickling multiple times should maintain identity."""
    original = Sentinel(name)
    
    # Multiple pickle round-trips
    temp = original
    for _ in range(3):
        pickled = pickle.dumps(temp)
        temp = pickle.loads(pickled)
    
    assert temp is original
    assert id(temp) == id(original)


@given(st.lists(st.text(min_size=1), min_size=2, max_size=10, unique=True))
def test_pickle_preserves_registry(names):
    """Pickling should preserve the singleton registry."""
    sentinels = [Sentinel(name) for name in names]
    
    # Pickle all sentinels
    pickled_sentinels = [pickle.dumps(s) for s in sentinels]
    
    # Unpickle them
    unpickled = [pickle.loads(p) for p in pickled_sentinels]
    
    # They should be the same objects as the originals
    for original, restored in zip(sentinels, unpickled):
        assert original is restored
        assert original._name in Sentinel._existing_instances
        assert Sentinel._existing_instances[original._name] is original


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])