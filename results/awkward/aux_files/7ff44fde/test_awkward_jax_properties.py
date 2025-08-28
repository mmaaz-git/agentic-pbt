#!/usr/bin/env python3
"""
Property-based tests for awkward.jax module
"""

import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages")

import threading
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from hypothesis import given, strategies as st, assume, settings
import pytest

import awkward as ak
import awkward.jax
from awkward._connect.jax.trees import split_buffers, AuxData
from awkward._layout import HighLevelContext
import awkward._connect.jax as jax_connect


# Property 1: Buffer splitting invariant
@given(st.dictionaries(
    st.text(min_size=1, max_size=50).filter(lambda s: "-" in s),
    st.binary(min_size=1, max_size=100)
))
def test_buffer_splitting_invariant(buffers):
    """Test that buffer splitting correctly separates data and non-data buffers"""
    data_buffers, other_buffers = split_buffers(buffers)
    
    # Invariant 1: All keys ending with "-data" are in data_buffers
    for key in data_buffers:
        assert key.endswith("-data"), f"Key {key} in data_buffers doesn't end with '-data'"
    
    # Invariant 2: No keys ending with "-data" are in other_buffers
    for key in other_buffers:
        assert not key.endswith("-data"), f"Key {key} in other_buffers ends with '-data'"
    
    # Invariant 3: All original keys are preserved (no loss)
    assert set(data_buffers.keys()) | set(other_buffers.keys()) == set(buffers.keys())
    
    # Invariant 4: No overlap between data and other buffers
    assert set(data_buffers.keys()) & set(other_buffers.keys()) == set()
    
    # Invariant 5: Values are preserved
    for key, value in buffers.items():
        if key.endswith("-data"):
            assert data_buffers[key] == value
        else:
            assert other_buffers[key] == value


# Property 2: Registration state machine
def test_registration_state_transitions():
    """Test that registration state machine transitions are valid"""
    from awkward.jax import _RegistrationState, _registration_state, _registration_lock
    
    # The state should be one of the valid enum values
    with _registration_lock:
        assert _registration_state in [
            _RegistrationState.INIT,
            _RegistrationState.SUCCESS, 
            _RegistrationState.FAILED
        ]


# Property 3: AuxData equality properties
@given(
    st.tuples(st.text(min_size=1, max_size=20)),
    st.dictionaries(st.text(min_size=1, max_size=20), st.binary(min_size=1, max_size=50)),
    st.integers(min_value=0, max_value=1000)
)
def test_auxdata_equality_reflexive(data_buffer_keys, other_buffers, length):
    """Test that AuxData equality is reflexive (a == a)"""
    # Create a simple form for testing
    form = ak.forms.NumpyForm(
        "bool",
        form_key="test"
    )
    
    with HighLevelContext() as ctx:
        aux = AuxData(
            data_buffer_keys=data_buffer_keys,
            other_buffers=other_buffers,
            form=form,
            length=length,
            ctx=ctx,
            highlevel=True
        )
        
        # Reflexive property: a == a
        assert aux == aux
        assert not (aux != aux)


@given(
    st.tuples(st.text(min_size=1, max_size=20)),
    st.dictionaries(st.text(min_size=1, max_size=20), st.binary(min_size=1, max_size=50)),
    st.integers(min_value=0, max_value=1000),
    st.booleans()
)
def test_auxdata_equality_symmetric(data_buffer_keys, other_buffers, length, same_form):
    """Test that AuxData equality is symmetric (a == b implies b == a)"""
    # Create forms
    form1 = ak.forms.NumpyForm("bool", form_key="test1")
    form2 = form1 if same_form else ak.forms.NumpyForm("bool", form_key="test2")
    
    with HighLevelContext() as ctx1:
        aux1 = AuxData(
            data_buffer_keys=data_buffer_keys,
            other_buffers=other_buffers,
            form=form1,
            length=length,
            ctx=ctx1,
            highlevel=True
        )
    
    with HighLevelContext() as ctx2:
        aux2 = AuxData(
            data_buffer_keys=data_buffer_keys,
            other_buffers=other_buffers,
            form=form2,
            length=length,
            ctx=ctx2,
            highlevel=True
        )
        
        # Symmetric property
        if aux1 == aux2:
            assert aux2 == aux1
        if aux1 != aux2:
            assert aux2 != aux1


# Property 4: Thread safety of registration
def test_registration_thread_safety():
    """Test that concurrent registration attempts are handled safely"""
    from awkward.jax import register_behavior_class, _known_highlevel_classes
    
    # Create a test class that inherits from Array
    class TestArray(ak.Array):
        pass
    
    # Try to register the same class from multiple threads
    def register_class():
        try:
            register_behavior_class(TestArray)
            return "success"
        except Exception as e:
            return f"error: {e}"
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(register_class) for _ in range(10)]
        results = [f.result() for f in futures]
    
    # All attempts should succeed (thread-safe)
    for result in results:
        assert result == "success", f"Registration failed: {result}"
    
    # The class should be in the known classes
    assert TestArray in _known_highlevel_classes


# Property 5: assert_never should always raise
@given(st.text())
def test_assert_never_always_raises(value):
    """Test that assert_never always raises AssertionError"""
    from awkward.jax import assert_never
    
    with pytest.raises(AssertionError) as exc_info:
        assert_never(value)
    
    assert f"this should never be run: {value}" in str(exc_info.value)


# Property 6: JAX import functions
def test_import_jax_requires_registration():
    """Test that import_jax requires registration"""
    from awkward.jax import import_jax, _registration_state, _RegistrationState, _registration_lock
    
    # If not registered (INIT state), should raise RuntimeError
    with _registration_lock:
        if _registration_state == _RegistrationState.INIT:
            with pytest.raises(RuntimeError) as exc_info:
                import_jax()
            assert "JAX features require `ak.jax.register_and_check()`" in str(exc_info.value)


# Property 7: Float0 dtype rejection
def test_float0_dtype_rejection():
    """Test that float0 dtypes are properly rejected during unflattening"""
    # Create a mock buffer with float0 dtype
    class MockBuffer:
        dtype = np.dtype([("float0", "V")])
    
    form = ak.forms.NumpyForm("bool", form_key="test")
    
    with HighLevelContext() as ctx:
        aux = AuxData(
            data_buffer_keys=("test-data",),
            other_buffers={},
            form=form,
            length=1,
            ctx=ctx,
            highlevel=True
        )
        
        # Should raise TypeError when encountering float0
        with pytest.raises(TypeError) as exc_info:
            aux.unflatten((MockBuffer(),))
        
        assert "float0" in str(exc_info.value)
        assert "tangents of integer/boolean outputs" in str(exc_info.value)


if __name__ == "__main__":
    # Run with pytest to get detailed output
    import subprocess
    subprocess.run([
        "/root/hypothesis-llm/envs/awkward_env/bin/python3", "-m", "pytest", 
        __file__, "-v", "--tb=short"
    ])