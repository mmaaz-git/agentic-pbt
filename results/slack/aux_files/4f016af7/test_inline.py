#!/usr/bin/env python3
import sys
sys.path.append('/root/hypothesis-llm/envs/slack_env/lib/python3.13/site-packages')

import slack
from hypothesis import given, strategies as st, assume, settings, find
import string

# Test 1: Registration and retrieval
print("Test 1: Registration and retrieval")
try:
    container = slack.Container()
    container.register("test_key", 42)
    result = container.provide("test_key")
    assert result == 42
    print("  Basic test passed")
    
    # Now test with hypothesis
    valid_identifier = st.text(alphabet=string.ascii_letters + '_', min_size=1, max_size=20).filter(lambda x: x.isidentifier() and not x.startswith('_'))
    
    @given(valid_identifier, st.integers())
    @settings(max_examples=100)
    def test_reg(name, value):
        c = slack.Container()
        c.register(name, value)
        assert c.provide(name) == value
        assert getattr(c, name) == value
    
    test_reg()
    print("  Property test passed")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 2: invoke function
print("\nTest 2: invoke function with missing params")
try:
    def test_func(required_param):
        return required_param
    
    # This should raise an error
    slack.invoke(test_func, {})
    print("  FAILED: Should have raised exception")
except slack.ParamterMissingError as e:
    print(f"  Passed: Correctly raised ParamterMissingError: {e}")
except Exception as e:
    print(f"  FAILED with unexpected error: {e}")

# Test 3: invoke with defaults
print("\nTest 3: invoke with defaults")
try:
    def test_func(param=10):
        return param
    
    result = slack.invoke(test_func, {})
    assert result == 10
    print(f"  Passed: Got default value {result}")
except Exception as e:
    print(f"  FAILED: {e}")

# Test 4: Test reset functionality
print("\nTest 4: Reset group functionality")
try:
    container = slack.Container()
    container.register("item1", 1, group="test_group")
    container.register("item2", 2, group="test_group")
    container.register("item3", 3, group="other_group")
    
    # Access all items
    container.provide("item1")
    container.provide("item2")
    container.provide("item3")
    
    # All should be in __dict__
    assert "item1" in container.__dict__
    assert "item2" in container.__dict__
    assert "item3" in container.__dict__
    
    # Reset test_group
    container.reset("test_group")
    
    # test_group items should be removed, other_group should remain
    assert "item1" not in container.__dict__
    assert "item2" not in container.__dict__
    assert "item3" in container.__dict__
    
    print("  Passed: Reset correctly removes group items")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Container with callable
print("\nTest 5: Container with callable factory")
try:
    counter = {'count': 0}
    def factory():
        counter['count'] += 1
        return counter['count']
    
    container = slack.Container()
    container.register("factory_item", factory)
    
    first = container.provide("factory_item")
    second = container.provide("factory_item")
    
    assert first == 1, f"First call should return 1, got {first}"
    assert second == 1, f"Second call should return same instance (1), got {second}"
    
    print("  Passed: Factory called once, result cached")
except Exception as e:
    print(f"  FAILED: {e}")

# Test 6: Test apply method
print("\nTest 6: Container apply method")
try:
    def test_func(dep1, dep2=None):
        return {'dep1': dep1, 'dep2': dep2}
    
    container = slack.Container()
    container.register("dep1", "value1")
    
    result = container.apply(test_func)
    assert result['dep1'] == "value1"
    assert result['dep2'] is None
    
    print(f"  Passed: apply injected dependencies correctly")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Test invoke with self parameter
print("\nTest 7: invoke with class methods")
try:
    class TestClass:
        def method(self, param):
            return param * 2
    
    obj = TestClass()
    result = slack.invoke(obj.method, {'param': 5})
    assert result == 10
    print("  Passed: Class method invoked correctly")
except Exception as e:
    print(f"  FAILED: {e}")

print("\n" + "="*60)
print("Basic tests completed. Running more comprehensive property tests...")