"""
Property-based tests for srsly.cloudpickle using Hypothesis
"""
import io
import pickle
import sys
import types
import functools
import math
from typing import Any, Callable

import pytest
from hypothesis import assume, given, strategies as st, settings

# Add the virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

import srsly.cloudpickle as cloudpickle


# Helper function for round-trip testing
def round_trip(obj: Any, protocol: int = cloudpickle.DEFAULT_PROTOCOL) -> Any:
    """Serialize and deserialize an object"""
    return pickle.loads(cloudpickle.dumps(obj, protocol=protocol))


# Strategy for generating simple Python objects
simple_objects = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.binary(),
    st.tuples(st.integers()),
    st.lists(st.integers()),
    st.sets(st.integers()),
    st.dictionaries(st.text(), st.integers()),
)

# Strategy for valid pickle protocols
# Protocol 5 is the highest in Python 3.8+
valid_protocols = st.integers(min_value=0, max_value=pickle.HIGHEST_PROTOCOL)


class TestRoundTripProperties:
    """Test round-trip properties: dumps then loads should preserve the object"""
    
    @given(simple_objects)
    @settings(max_examples=200)
    def test_simple_objects_round_trip(self, obj):
        """Test that simple Python objects can be pickled and unpickled correctly"""
        result = round_trip(obj)
        assert result == obj
    
    @given(st.integers(), st.integers())
    @settings(max_examples=100)
    def test_lambda_round_trip(self, a, b):
        """Test that lambdas can be pickled and unpickled correctly"""
        # Create a lambda that captures variables
        f = lambda x: x + a * b
        
        # Round-trip the lambda
        f_restored = round_trip(f)
        
        # Test that it works the same way
        test_values = [0, 1, -1, 42, a, b]
        for x in test_values:
            assert f_restored(x) == f(x)
    
    @given(st.integers())
    @settings(max_examples=100)
    def test_nested_function_round_trip(self, multiplier):
        """Test that nested functions with closures work correctly"""
        def make_multiplier(m):
            def multiply(x):
                return x * m
            return multiply
        
        func = make_multiplier(multiplier)
        func_restored = round_trip(func)
        
        # Test the restored function
        test_values = [0, 1, -1, 42]
        for x in test_values:
            assert func_restored(x) == func(x)
    
    @given(st.integers(), st.integers())
    @settings(max_examples=50)
    def test_partial_function_round_trip(self, a, b):
        """Test that partial functions can be pickled correctly"""
        def add_three(x, y, z):
            return x + y + z
        
        partial_func = functools.partial(add_three, a, b)
        restored = round_trip(partial_func)
        
        # Test with various z values
        for z in [0, 1, -1, 42]:
            assert restored(z) == partial_func(z)
    
    @given(st.lists(st.integers()))
    @settings(max_examples=100)
    def test_class_round_trip(self, data):
        """Test that dynamically created classes can be pickled"""
        class DataHolder:
            def __init__(self):
                self.data = data
            
            def get_sum(self):
                return sum(self.data) if self.data else 0
            
            def get_length(self):
                return len(self.data)
        
        # Test the class itself
        RestoredClass = round_trip(DataHolder)
        instance = RestoredClass()
        assert instance.get_sum() == (sum(data) if data else 0)
        assert instance.get_length() == len(data)
        
        # Test an instance
        original_instance = DataHolder()
        restored_instance = round_trip(original_instance)
        assert restored_instance.get_sum() == original_instance.get_sum()
        assert restored_instance.get_length() == original_instance.get_length()


class TestProtocolHandling:
    """Test that different pickle protocols work correctly"""
    
    @given(simple_objects, valid_protocols)
    @settings(max_examples=100)
    def test_protocol_parameter(self, obj, protocol):
        """Test that all valid protocols work for serialization"""
        serialized = cloudpickle.dumps(obj, protocol=protocol)
        assert isinstance(serialized, bytes)
        assert len(serialized) >= 0
        
        # Should be able to deserialize
        result = pickle.loads(serialized)
        assert result == obj
    
    @given(st.integers(), valid_protocols)
    @settings(max_examples=50)
    def test_lambda_with_protocol(self, value, protocol):
        """Test that lambdas work with different protocols"""
        f = lambda x: x + value
        result = pickle.loads(cloudpickle.dumps(f, protocol=protocol))
        
        # Test the lambda still works
        assert result(10) == f(10)
        assert result(0) == f(0)


class TestDumpDumpsEquivalence:
    """Test that dump and dumps produce equivalent results"""
    
    @given(simple_objects)
    @settings(max_examples=100)
    def test_dump_dumps_equivalence(self, obj):
        """Test that dump(obj, file) and dumps(obj) produce the same bytes"""
        # Get bytes using dumps
        bytes_from_dumps = cloudpickle.dumps(obj)
        
        # Get bytes using dump
        buffer = io.BytesIO()
        cloudpickle.dump(obj, buffer)
        bytes_from_dump = buffer.getvalue()
        
        # They should be identical
        assert bytes_from_dump == bytes_from_dumps
        
        # Both should deserialize to the same object
        assert pickle.loads(bytes_from_dumps) == pickle.loads(bytes_from_dump)
    
    @given(st.integers(), valid_protocols)
    @settings(max_examples=50)
    def test_dump_dumps_equivalence_with_protocol(self, value, protocol):
        """Test dump/dumps equivalence with different protocols"""
        f = lambda: value
        
        # Using dumps
        bytes_from_dumps = cloudpickle.dumps(f, protocol=protocol)
        
        # Using dump
        buffer = io.BytesIO()
        cloudpickle.dump(f, buffer, protocol=protocol)
        bytes_from_dump = buffer.getvalue()
        
        # Should produce the same serialization
        assert bytes_from_dump == bytes_from_dumps


class TestEdgeCases:
    """Test edge cases and special behaviors"""
    
    @given(st.integers(min_value=0, max_value=10))
    @settings(max_examples=50)
    def test_recursive_function(self, n):
        """Test pickling recursive functions"""
        
        def factorial(x):
            if x <= 1:
                return 1
            return x * factorial(x - 1)
        
        restored = round_trip(factorial)
        
        # Test the restored function
        assert restored(n) == factorial(n)
    
    @given(st.floats(allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_functions_using_builtins(self, x):
        """Test functions that use builtin functions"""
        def use_math(val):
            if val > 0:
                return math.sqrt(val)
            return abs(val)
        
        restored = round_trip(use_math)
        assert restored(x) == use_math(x)
    
    def test_empty_closure_preserved(self):
        """Test that functions with empty closure cells are preserved correctly"""
        def make_func_with_empty_cell():
            if False:
                cell = None
            
            def inner():
                return cell  # This will raise NameError
            
            return inner
        
        func = make_func_with_empty_cell()
        restored = round_trip(func)
        
        # Both should raise NameError
        with pytest.raises(NameError):
            func()
        
        with pytest.raises(NameError):
            restored()
    
    def test_none_closure_preserved(self):
        """Test that functions with no closure are preserved correctly"""
        def simple_func(x):
            return x * 2
        
        assert simple_func.__closure__ is None
        
        restored = round_trip(simple_func)
        assert restored.__closure__ is None
        assert restored(5) == simple_func(5)
    
    @given(st.lists(st.integers(), min_size=1))
    @settings(max_examples=50)
    def test_unhashable_closure(self, initial_data):
        """Test functions with unhashable objects in closure"""
        def make_func_with_set():
            s = set(initial_data)  # mutable set is unhashable
            
            def get_size():
                return len(s)
            
            return get_size
        
        func = make_func_with_set()
        restored = round_trip(func)
        
        assert restored() == func()


class TestIdempotence:
    """Test that multiple round-trips produce stable results"""
    
    @given(simple_objects)
    @settings(max_examples=100)
    def test_double_round_trip(self, obj):
        """Test that pickling twice gives the same result"""
        once = round_trip(obj)
        twice = round_trip(once)
        assert once == twice == obj
    
    @given(st.integers())
    @settings(max_examples=50)
    def test_lambda_idempotence(self, value):
        """Test that lambdas remain stable through multiple round-trips"""
        f = lambda x: x * value + 1
        
        f1 = round_trip(f)
        f2 = round_trip(f1)
        f3 = round_trip(f2)
        
        # All should produce the same results
        test_inputs = [0, 1, -1, 42]
        for x in test_inputs:
            result = f(x)
            assert f1(x) == result
            assert f2(x) == result
            assert f3(x) == result


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])