#!/usr/bin/env python3
"""Manually run property-based tests without pytest."""

import sys
import traceback

# First, let's check if we can import hypothesis
try:
    import hypothesis
    print("✓ Hypothesis is available")
except ImportError:
    print("✗ Hypothesis not installed, attempting to install...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "hypothesis", "-q"])
    import hypothesis
    print("✓ Hypothesis installed")

sys.path.insert(0, '.')
import pyramid_decorator

from hypothesis import given, strategies as st, settings
from hypothesis import HealthCheck

# Configure hypothesis
settings.register_profile("bug_hunting", 
    max_examples=100,
    suppress_health_check=[HealthCheck.too_slow]
)
settings.load_profile("bug_hunting")

print("\n" + "="*60)
print("PROPERTY-BASED TESTING: pyramid_decorator")
print("="*60)

test_results = []

# Test 1: reify single call property
print("\n[TEST 1] Testing reify single-call caching...")
try:
    @given(
        values=st.lists(st.integers() | st.floats(allow_nan=False) | st.text(), min_size=1),
        call_count=st.integers(min_value=2, max_value=10)
    )
    def test_reify_single_call(values, call_count):
        call_tracker = []
        
        class TestClass:
            @pyramid_decorator.reify
            def computed_value(self):
                call_tracker.append(1)
                return values[0]
        
        obj = TestClass()
        results = [obj.computed_value for _ in range(call_count)]
        
        assert len(call_tracker) == 1, f"Function called {len(call_tracker)} times, expected 1"
        assert all(r == results[0] for r in results), "Not all results are identical"
        assert hasattr(obj, 'computed_value')
        assert getattr(obj, 'computed_value') == results[0]
    
    test_reify_single_call()
    print("✓ PASSED: reify only calls function once")
    test_results.append(("reify single call", "PASSED", None))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("reify single call", "FAILED", str(e)))
    traceback.print_exc()

# Test 2: cached_property caching
print("\n[TEST 2] Testing cached_property caching...")
try:
    @given(
        initial_value=st.integers() | st.floats(allow_nan=False) | st.text(),
        access_count=st.integers(min_value=2, max_value=10)
    )
    def test_cached_property_caching(initial_value, access_count):
        call_count = []
        
        class TestClass:
            @pyramid_decorator.cached_property
            def value(self):
                call_count.append(1)
                return initial_value
        
        obj = TestClass()
        results = [obj.value for _ in range(access_count)]
        
        assert len(call_count) == 1
        assert all(r == initial_value for r in results)
    
    test_cached_property_caching()
    print("✓ PASSED: cached_property caches correctly")
    test_results.append(("cached_property caching", "PASSED", None))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("cached_property caching", "FAILED", str(e)))
    traceback.print_exc()

# Test 3: compose decorator order
print("\n[TEST 3] Testing compose decorator order...")
try:
    @given(
        input_value=st.integers(),
        add_values=st.lists(st.integers(min_value=-100, max_value=100), min_size=1, max_size=3)
    )
    def test_compose_order(input_value, add_values):
        import functools
        
        decorators = []
        for val in add_values:
            def make_decorator(v):
                def decorator(func):
                    @functools.wraps(func)
                    def wrapper(x):
                        return func(x) + v
                    return wrapper
                return decorator
            decorators.append(make_decorator(val))
        
        def base_func(x):
            return x
        
        composed = pyramid_decorator.compose(*decorators)(base_func)
        result1 = composed(input_value)
        
        manual = base_func
        for dec in reversed(decorators):
            manual = dec(manual)
        result2 = manual(input_value)
        
        assert result1 == result2, f"Compose result {result1} != manual result {result2}"
    
    test_compose_order()
    print("✓ PASSED: compose maintains correct decorator order")
    test_results.append(("compose order", "PASSED", None))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("compose order", "FAILED", str(e)))
    traceback.print_exc()

# Test 4: view_config JSON renderer
print("\n[TEST 4] Testing view_config JSON renderer...")
try:
    import json
    
    @given(
        result_value=st.dictionaries(
            st.text(min_size=1, max_size=10), 
            st.integers() | st.floats(allow_nan=False) | st.text(max_size=20) | st.booleans(),
            max_size=5
        )
    )
    def test_view_config_json(result_value):
        @pyramid_decorator.view_config(renderer='json')
        def view_func():
            return result_value
        
        result = view_func()
        
        assert isinstance(result, str), f"Result should be string, got {type(result)}"
        parsed = json.loads(result)
        assert parsed == result_value
    
    test_view_config_json()
    print("✓ PASSED: view_config JSON renderer works correctly")
    test_results.append(("view_config JSON", "PASSED", None))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("view_config JSON", "FAILED", str(e)))
    traceback.print_exc()

# Test 5: validate_arguments
print("\n[TEST 5] Testing validate_arguments...")
try:
    @given(
        valid_value=st.integers(min_value=1, max_value=100),
        invalid_value=st.one_of(st.integers(max_value=0), st.integers(min_value=101))
    )
    def test_validate_arguments(valid_value, invalid_value):
        def is_valid(x):
            return 1 <= x <= 100
        
        @pyramid_decorator.validate_arguments(x=is_valid)
        def func(x):
            return x * 2
        
        # Valid value should pass
        assert func(valid_value) == valid_value * 2
        
        # Invalid value should raise ValueError
        error_raised = False
        try:
            func(invalid_value)
        except ValueError as e:
            error_raised = True
            assert "Invalid value for x" in str(e)
        
        assert error_raised, "Should have raised ValueError for invalid value"
    
    test_validate_arguments()
    print("✓ PASSED: validate_arguments validates correctly")
    test_results.append(("validate_arguments", "PASSED", None))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("validate_arguments", "FAILED", str(e)))
    traceback.print_exc()

# Test 6: preserve_signature
print("\n[TEST 6] Testing preserve_signature...")
try:
    import inspect
    
    @given(st.data())
    def test_preserve_signature(data):
        param_names = data.draw(st.lists(
            st.text(alphabet='abcdefgh', min_size=1, max_size=3),
            min_size=1,
            max_size=3,
            unique=True
        ))
        
        func_str = f"def original_func({', '.join(param_names)}): return 42"
        local_dict = {}
        exec(func_str, local_dict)
        original_func = local_dict['original_func']
        
        def wrapper(*args, **kwargs):
            return original_func(*args, **kwargs) * 2
        
        preserved = pyramid_decorator.preserve_signature(original_func)(wrapper)
        
        assert inspect.signature(preserved) == inspect.signature(original_func)
    
    test_preserve_signature()
    print("✓ PASSED: preserve_signature preserves function signatures")
    test_results.append(("preserve_signature", "PASSED", None))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("preserve_signature", "FAILED", str(e)))
    traceback.print_exc()

# Test 7: Decorator callbacks
print("\n[TEST 7] Testing Decorator class callbacks...")
try:
    @given(
        num_callbacks=st.integers(min_value=0, max_value=5),
        return_value=st.integers(),
        use_json=st.booleans()
    )
    def test_decorator_callbacks(num_callbacks, return_value, use_json):
        callback_order = []
        
        settings = {'json_response': use_json}
        dec = pyramid_decorator.Decorator(**settings)
        
        for i in range(num_callbacks):
            def make_callback(idx):
                def callback(wrapped, args, kwargs):
                    callback_order.append(idx)
                return callback
            dec.add_callback(make_callback(i))
        
        @dec
        def func():
            return return_value
        
        result = func()
        
        assert callback_order == list(range(num_callbacks))
        
        if use_json:
            import json
            assert result == json.dumps(return_value)
        else:
            assert result == return_value
    
    test_decorator_callbacks()
    print("✓ PASSED: Decorator callbacks execute in order")
    test_results.append(("Decorator callbacks", "PASSED", None))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("Decorator callbacks", "FAILED", str(e)))
    traceback.print_exc()

# Test 8: cached_property set/delete
print("\n[TEST 8] Testing cached_property set/delete...")
try:
    from hypothesis import assume
    
    @given(
        computed_value=st.integers(),
        set_value=st.integers()
    )
    def test_cached_property_set_delete(computed_value, set_value):
        assume(computed_value != set_value)
        
        class TestClass:
            @pyramid_decorator.cached_property
            def prop(self):
                return computed_value
        
        obj = TestClass()
        
        # Initial access
        assert obj.prop == computed_value
        
        # Setting should change the value
        obj.prop = set_value
        assert obj.prop == set_value
        
        # Deleting should clear the cache
        del obj.prop
        # Next access should recompute
        assert obj.prop == computed_value
    
    test_cached_property_set_delete()
    print("✓ PASSED: cached_property set/delete works correctly")
    test_results.append(("cached_property set/delete", "PASSED", None))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("cached_property set/delete", "FAILED", str(e)))
    traceback.print_exc()

# Test 9: view_config settings accumulation  
print("\n[TEST 9] Testing view_config settings accumulation...")
try:
    @given(
        settings_list=st.lists(
            st.dictionaries(
                st.text(min_size=1, max_size=5), 
                st.integers(),
                max_size=3
            ),
            min_size=1,
            max_size=3
        )
    )
    def test_view_config_accumulation(settings_list):
        def base_func():
            return "test"
        
        func = base_func
        for settings in settings_list:
            func = pyramid_decorator.view_config(**settings)(func)
        
        assert hasattr(func, '__view_settings__')
        assert len(func.__view_settings__) == len(settings_list)
        
        for i, settings in enumerate(settings_list):
            assert func.__view_settings__[i] == settings
    
    test_view_config_accumulation()
    print("✓ PASSED: view_config accumulates settings correctly")  
    test_results.append(("view_config accumulation", "PASSED", None))
except Exception as e:
    print(f"✗ FAILED: {e}")
    test_results.append(("view_config accumulation", "FAILED", str(e)))
    traceback.print_exc()

# Summary
print("\n" + "="*60)
print("TEST SUMMARY")
print("="*60)

passed = sum(1 for _, status, _ in test_results if status == "PASSED")
failed = sum(1 for _, status, _ in test_results if status == "FAILED")

print(f"Total tests: {len(test_results)}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")

if failed > 0:
    print("\nFailed tests:")
    for name, status, error in test_results:
        if status == "FAILED":
            print(f"  - {name}: {error}")

print("\n" + "="*60)