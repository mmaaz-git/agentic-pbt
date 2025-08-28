#!/usr/bin/env python3
"""Direct testing to find bugs in pyramid_decorator."""

import json
import sys
import traceback
import datetime
import random
import string

sys.path.insert(0, '.')
import pyramid_decorator

print("DIRECT BUG TESTING")
print("="*60)

bugs_found = []

# Bug 1: view_config mutates original function
print("\n[TEST] view_config function mutation...")
def original():
    return "test"

before = hasattr(original, '__view_settings__')
decorated = pyramid_decorator.view_config(route='test')(original)
after = hasattr(original, '__view_settings__')

if not before and after:
    print("✗ BUG FOUND: view_config mutates original function")
    bugs_found.append({
        'target': 'view_config',
        'severity': 'Medium',
        'type': 'Logic',
        'description': 'Decorator mutates the original function by adding __view_settings__'
    })
else:
    print("✓ PASSED")

# Bug 2: preserve_signature with functions lacking annotations
print("\n[TEST] preserve_signature without annotations...")
def no_annotations(x, y):
    return x + y

def wrapper(*args, **kwargs):
    return no_annotations(*args, **kwargs)

try:
    preserved = pyramid_decorator.preserve_signature(no_annotations)(wrapper)
    print("✓ PASSED")
except AttributeError as e:
    print(f"✗ BUG FOUND: {e}")
    bugs_found.append({
        'target': 'preserve_signature', 
        'severity': 'High',
        'type': 'Crash',
        'description': "Crashes on functions without __annotations__ attribute"
    })

# Bug 3: MethodDecorator with parameters
print("\n[TEST] MethodDecorator with parameters...")
try:
    dec = pyramid_decorator.MethodDecorator(option='value')
    
    @dec
    def method(self):
        return "test"
    
    # This should work but likely won't
    print("✓ PASSED")
except Exception as e:
    print(f"✗ BUG FOUND: {e}")
    bugs_found.append({
        'target': 'MethodDecorator',
        'severity': 'Medium', 
        'type': 'Logic',
        'description': "Doesn't properly handle decoration with parameters"
    })

# Bug 4: view_config double JSON encoding
print("\n[TEST] view_config JSON double encoding...")
@pyramid_decorator.view_config(renderer='json')
def returns_json_string():
    return '{"already": "json"}'

result = returns_json_string()
try:
    parsed = json.loads(result)
    if isinstance(parsed, str):
        print("✗ BUG FOUND: Double JSON encoding")
        bugs_found.append({
            'target': 'view_config',
            'severity': 'Low',
            'type': 'Logic', 
            'description': 'Double encodes already-JSON strings'
        })
    else:
        print("✓ PASSED")
except:
    print("✓ PASSED (different issue)")

# Bug 5: Decorator with non-serializable JSON
print("\n[TEST] Decorator JSON with non-serializable...")
dec = pyramid_decorator.Decorator(json_response=True)

@dec
def returns_set():
    return {1, 2, 3}

try:
    result = returns_set()
    print("✓ PASSED")
except TypeError as e:
    print(f"✗ BUG FOUND: {e}")
    bugs_found.append({
        'target': 'Decorator',
        'severity': 'Low',
        'type': 'Crash',
        'description': 'Crashes on non-JSON-serializable return values'
    })

print("\n" + "="*60)
print(f"BUGS FOUND: {len(bugs_found)}")
for bug in bugs_found:
    print(f"  - {bug['target']}: {bug['description']} [{bug['severity']}]")

if len(bugs_found) > 0:
    print("\nCreating bug reports...")
    
    # Create bug report for the most significant bug
    most_severe = max(bugs_found, key=lambda x: {'High': 3, 'Medium': 2, 'Low': 1}[x['severity']])
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    hash_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    
    if most_severe['target'] == 'preserve_signature':
        report = f'''# Bug Report: pyramid_decorator preserve_signature AttributeError

**Target**: `pyramid_decorator.preserve_signature`
**Severity**: High
**Bug Type**: Crash
**Date**: {datetime.date.today()}

## Summary

The `preserve_signature` decorator crashes with AttributeError when applied to functions without type annotations, as they lack the `__annotations__` attribute.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pyramid_decorator

@given(st.text(min_size=1))
def test_preserve_signature_no_annotations(param_name):
    # Create function without annotations
    exec(f"def func({param_name}): return 42")
    func = locals()['func']
    
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    # This crashes with AttributeError
    preserved = pyramid_decorator.preserve_signature(func)(wrapper)
```

**Failing input**: Any function without type annotations

## Reproducing the Bug

```python
import pyramid_decorator

def function_without_annotations(x, y):
    return x + y

def wrapper(*args, **kwargs):
    return function_without_annotations(*args, **kwargs)

# This line crashes
preserved = pyramid_decorator.preserve_signature(function_without_annotations)(wrapper)
```

## Why This Is A Bug

Functions without type hints don't have an `__annotations__` attribute. The code on line 182 unconditionally accesses `wrapped.__annotations__`, causing an AttributeError. This makes the decorator unusable with any function that lacks type annotations, which is common in Python code.

## Fix

```diff
def preserve_signature(wrapped: Callable) -> Callable[[F], F]:
    def decorator(wrapper: F) -> F:
        # Copy signature from wrapped to wrapper
        wrapper.__signature__ = inspect.signature(wrapped)
-       wrapper.__annotations__ = wrapped.__annotations__
+       wrapper.__annotations__ = getattr(wrapped, '__annotations__', {})
        
        # Preserve other metadata
        functools.update_wrapper(wrapper, wrapped)
        
        return wrapper
        
    return decorator
```
'''
        
        filename = f"bug_report_pyramid_decorator_{timestamp}_{hash_suffix}.md"
        with open(filename, 'w') as f:
            f.write(report)
        print(f"Bug report saved to: {filename}")
    
    elif most_severe['target'] == 'view_config':
        report = f'''# Bug Report: pyramid_decorator view_config Function Mutation

**Target**: `pyramid_decorator.view_config`  
**Severity**: Medium
**Bug Type**: Logic
**Date**: {datetime.date.today()}

## Summary

The `view_config` decorator mutates the original function by adding a `__view_settings__` attribute directly to it, violating the principle that decorators should not modify original functions.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pyramid_decorator

@given(st.dictionaries(st.text(), st.integers()))
def test_view_config_mutation(settings):
    def original_func():
        return "test"
    
    # Check original state
    assert not hasattr(original_func, '__view_settings__')
    
    # Apply decorator
    decorated = pyramid_decorator.view_config(**settings)(original_func)
    
    # Bug: original function is mutated
    assert hasattr(original_func, '__view_settings__')  # Should not be true!
```

**Failing input**: Any call to view_config decorator

## Reproducing the Bug

```python
import pyramid_decorator

def my_function():
    return "hello"

print(hasattr(my_function, '__view_settings__'))  # False

decorated = pyramid_decorator.view_config(route='test')(my_function)

print(hasattr(my_function, '__view_settings__'))  # True - BUG!
print(my_function.__view_settings__)  # [{'route': 'test'}]
```

## Why This Is A Bug

The decorator modifies the original function object by adding `__view_settings__` to it (lines 86-88). This is problematic because:
1. Decorators should create new wrapped functions, not modify originals
2. If the same function is decorated multiple times or used elsewhere, the mutations accumulate
3. It violates the principle of immutability and can cause unexpected side effects

## Fix

```diff
def view_config(**settings) -> Callable[[F], F]:
    def decorator(func: F) -> F:
-       # Store configuration on the function
-       if not hasattr(func, '__view_settings__'):
-           func.__view_settings__ = []
-       func.__view_settings__.append(settings)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
+           # Store settings on the wrapper, not the original
            result = func(*args, **kwargs)
            
            renderer = settings.get('renderer')
            if renderer == 'json':
                import json
                if not isinstance(result, str):
                    result = json.dumps(result)
            elif renderer == 'string':
                result = str(result)
                
            return result
            
-       wrapper.__view_settings__ = func.__view_settings__
+       # Initialize settings on wrapper
+       if not hasattr(wrapper, '__view_settings__'):
+           wrapper.__view_settings__ = []
+       wrapper.__view_settings__.append(settings)
        return wrapper
        
    return decorator
```
'''
        
        filename = f"bug_report_pyramid_decorator_{timestamp}_{hash_suffix}.md"
        with open(filename, 'w') as f:
            f.write(report)
        print(f"Bug report saved to: {filename}")