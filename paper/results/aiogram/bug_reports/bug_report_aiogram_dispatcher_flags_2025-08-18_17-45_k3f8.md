# Bug Report: aiogram.dispatcher.flags FlagDecorator Fails to Validate Falsy Values

**Target**: `aiogram.dispatcher.flags.FlagDecorator`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

FlagDecorator's __call__ method fails to raise ValueError when both a falsy value (0, False, "", [], {}, None) and kwargs are provided, violating its documented API contract.

## Property-Based Test

```python
@given(
    st.one_of(st.integers(), st.text(), st.booleans()),
    st.dictionaries(st.text(min_size=1), st.integers(), min_size=1, max_size=3)
)
def test_flag_decorator_value_kwargs_exclusive(value, kwargs):
    """Test that FlagDecorator can't use both value and kwargs (flags.py:46)"""
    flag = Flag("test_flag", True)
    decorator = FlagDecorator(flag)
    
    def dummy_func():
        pass
    
    with pytest.raises(ValueError, match="The arguments `value` and \\*\\*kwargs can not be used together"):
        decorator(value, **kwargs)
```

**Failing input**: `value=0, kwargs={'0': 0}`

## Reproducing the Bug

```python
from aiogram.dispatcher.flags import FlagDecorator, Flag

flag = Flag("test_flag", True)
decorator = FlagDecorator(flag)

# Should raise ValueError but doesn't when value is falsy
result = decorator(0, some_kwarg=123)  # No error!
print(f"Result: {result}")  # FlagDecorator(flag=Flag(name='test_flag', value=0))

# Also fails for other falsy values
decorator(False, kwarg=1)  # No error!
decorator("", kwarg=1)      # No error!
decorator([], kwarg=1)      # No error!
decorator({}, kwarg=1)      # No error!
decorator(None, kwarg=1)    # No error!
```

## Why This Is A Bug

The code at flags.py:46 states "The arguments `value` and **kwargs can not be used together", but the validation check uses `if value and kwargs:` which fails for falsy values. This allows invalid combinations to pass through, violating the API contract and potentially causing unexpected behavior.

## Fix

```diff
--- a/aiogram/dispatcher/flags.py
+++ b/aiogram/dispatcher/flags.py
@@ -43,7 +43,7 @@ class FlagDecorator:
         value: Optional[Any] = None,
         **kwargs: Any,
     ) -> Union[Callable[..., Any], "FlagDecorator"]:
-        if value and kwargs:
+        if value is not None and kwargs:
             raise ValueError("The arguments `value` and **kwargs can not be used together")
 
         if value is not None and callable(value):
```