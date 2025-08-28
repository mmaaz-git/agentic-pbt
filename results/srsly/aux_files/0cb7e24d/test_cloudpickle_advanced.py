"""
Advanced property-based tests for srsly.cloudpickle to find potential bugs
"""
import io
import pickle
import sys
import types
import functools
import math
import copy
import weakref
import threading
from typing import Any, Callable

import pytest
from hypothesis import assume, given, strategies as st, settings, HealthCheck

# Add the virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/srsly_env/lib/python3.13/site-packages')

import srsly.cloudpickle as cloudpickle


# Helper function for round-trip testing
def round_trip(obj: Any, protocol: int = cloudpickle.DEFAULT_PROTOCOL) -> Any:
    """Serialize and deserialize an object"""
    return pickle.loads(cloudpickle.dumps(obj, protocol=protocol))


class TestComplexClosures:
    """Test complex closure scenarios that might break pickling"""
    
    @given(st.lists(st.integers(), min_size=1, max_size=10))
    @settings(max_examples=100)
    def test_nested_closures_with_mutations(self, values):
        """Test nested functions with mutable closures"""
        def outer():
            data = list(values)
            
            def middle():
                data.append(99)
                
                def inner():
                    return sum(data)
                
                return inner
            
            return middle
        
        func = outer()
        inner_func = func()
        
        # Get initial result
        initial_result = inner_func()
        
        # Round-trip both functions
        restored_func = round_trip(func)
        restored_inner = restored_func()
        
        # The restored function should produce the same result
        assert restored_inner() == initial_result
    
    @given(st.integers())
    @settings(max_examples=50)
    def test_circular_reference_in_closure(self, value):
        """Test functions with circular references in their closures"""
        def make_circular():
            container = {'value': value}
            
            def func():
                return container['value'] + container.get('func', lambda: 0)()
            
            container['func'] = func
            return func
        
        # This might fail due to circular reference
        func = make_circular()
        try:
            restored = round_trip(func)
            # If it succeeds, the behavior should be preserved
            assert restored() == func()
        except (RecursionError, ValueError, pickle.PicklingError):
            # Circular references might not be supported
            pass


class TestDynamicCodeGeneration:
    """Test dynamically generated code and functions"""
    
    @given(st.text(min_size=1, max_size=20).filter(lambda x: x.isidentifier()))
    @settings(max_examples=50)
    def test_dynamic_function_names(self, func_name):
        """Test functions with dynamically generated names"""
        # Create a function with a dynamic name
        code = f"""
def {func_name}(x):
    return x * 2
result = {func_name}
"""
        namespace = {}
        exec(code, namespace)
        func = namespace['result']
        
        # Round-trip the function
        restored = round_trip(func)
        
        # Test that it still works
        assert restored(5) == func(5)
        assert restored.__name__ == func.__name__
    
    @given(st.integers(min_value=1, max_value=5))
    @settings(max_examples=50)
    def test_nested_lambda_chains(self, depth):
        """Test deeply nested lambda chains"""
        # Create a chain of lambdas
        func = lambda x: x
        for i in range(depth):
            func = lambda f, i=i: lambda x: f(x) + i
            func = func(func)
        
        # Round-trip the nested lambda
        restored = round_trip(func)
        
        # Test with various inputs
        for test_val in [0, 1, -1, 10]:
            assert restored(test_val) == func(test_val)


class TestStatefulObjects:
    """Test pickling of stateful objects and their methods"""
    
    @given(st.dictionaries(st.text(), st.integers()))
    @settings(max_examples=50)
    def test_instance_method_with_state(self, state_dict):
        """Test instance methods that depend on object state"""
        class StatefulClass:
            def __init__(self):
                self.state = state_dict.copy()
            
            def compute(self, key):
                return self.state.get(key, 0) * 2
        
        obj = StatefulClass()
        method = obj.compute
        
        # Round-trip the bound method
        restored_method = round_trip(method)
        
        # Test that it still accesses the correct state
        for key in list(state_dict.keys())[:5]:  # Test first 5 keys
            assert restored_method(key) == method(key)
    
    @given(st.integers())
    @settings(max_examples=50)
    def test_generator_function(self, n):
        """Test generator functions"""
        def make_generator(max_val):
            def gen():
                for i in range(max_val):
                    yield i * 2
            return gen
        
        gen_func = make_generator(abs(n) % 10)  # Limit size
        restored = round_trip(gen_func)
        
        # Generators from both should produce the same values
        assert list(gen_func()) == list(restored())


class TestProtocolConsistency:
    """Test consistency across different pickle protocols"""
    
    @given(
        st.integers(),
        st.integers(min_value=0, max_value=pickle.HIGHEST_PROTOCOL),
        st.integers(min_value=0, max_value=pickle.HIGHEST_PROTOCOL)
    )
    @settings(max_examples=50)
    def test_cross_protocol_compatibility(self, value, protocol1, protocol2):
        """Test that objects pickled with one protocol can be unpickled with another"""
        func = lambda: value
        
        # Pickle with protocol1
        data1 = cloudpickle.dumps(func, protocol=protocol1)
        func1 = pickle.loads(data1)
        
        # Re-pickle with protocol2
        data2 = cloudpickle.dumps(func1, protocol=protocol2)
        func2 = pickle.loads(data2)
        
        # Both should produce the same result
        assert func() == func1() == func2()


class TestMemoryAndBuffer:
    """Test memory and buffer-related edge cases"""
    
    @given(st.binary(min_size=1, max_size=1000))
    @settings(max_examples=50)
    def test_function_with_large_constant(self, data):
        """Test functions with large constants in closure"""
        def make_func_with_data():
            large_constant = data * 100  # Make it larger
            
            def func():
                return len(large_constant)
            
            return func
        
        func = make_func_with_data()
        restored = round_trip(func)
        
        assert restored() == func()
    
    def test_dump_to_small_buffer(self):
        """Test dumping to a buffer with limited capacity"""
        # Create a function with a reasonably sized closure
        data = list(range(1000))
        func = lambda: sum(data)
        
        # Try dumping to a BytesIO buffer
        buffer = io.BytesIO()
        cloudpickle.dump(func, buffer)
        buffer.seek(0)
        
        # Should be able to load it back
        restored = pickle.load(buffer)
        assert restored() == func()


class TestTypeHints:
    """Test functions with type hints and annotations"""
    
    @given(st.integers())
    @settings(max_examples=50)
    def test_function_with_annotations(self, default_val):
        """Test functions with type annotations"""
        def typed_func(x: int, y: int = default_val) -> int:
            """A function with type hints"""
            return x + y
        
        restored = round_trip(typed_func)
        
        # Check that annotations are preserved
        assert restored.__annotations__ == typed_func.__annotations__
        assert restored(5) == typed_func(5)
        assert restored(5, 3) == typed_func(5, 3)


class TestWeirdFunctions:
    """Test unusual function constructs"""
    
    def test_function_modifying_own_closure(self):
        """Test a function that modifies its own closure"""
        def make_self_modifying():
            counter = [0]
            
            def func():
                counter[0] += 1
                return counter[0]
            
            return func
        
        func = make_self_modifying()
        
        # Call it a few times
        results_before = [func() for _ in range(3)]
        
        # Round-trip
        restored = round_trip(func)
        
        # The restored function should start from the saved state
        assert restored() == results_before[-1] + 1
    
    @given(st.lists(st.integers()))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.filter_too_much])
    def test_function_with_local_import(self, data):
        """Test functions with local imports"""
        assume(len(data) > 0)
        
        def func_with_import():
            import statistics
            return statistics.mean(data) if data else 0
        
        restored = round_trip(func_with_import)
        assert restored() == func_with_import()
    
    def test_empty_function(self):
        """Test completely empty function"""
        def empty():
            pass
        
        restored = round_trip(empty)
        assert restored() is None
        assert empty() is None


class TestConcurrency:
    """Test thread-safety and concurrency issues"""
    
    def test_concurrent_serialization(self):
        """Test that concurrent serialization doesn't cause issues"""
        import concurrent.futures
        
        def make_func(n):
            return lambda: n * 2
        
        funcs = [make_func(i) for i in range(10)]
        
        # Serialize all functions concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(cloudpickle.dumps, f) for f in funcs]
            serialized = [f.result() for f in futures]
        
        # Deserialize and check
        for i, data in enumerate(serialized):
            restored = pickle.loads(data)
            assert restored() == i * 2


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])