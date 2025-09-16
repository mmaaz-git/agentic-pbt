# Bug Report: fixit.api Type Annotation Mismatch in print_result

**Target**: `fixit.api.print_result`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `print_result` function has a type annotation that claims to return `int`, but the docstring and implementation clearly return boolean values (`True`/`False`).

## Property-Based Test

```python
from hypothesis import given, strategies as st
from fixit.api import print_result
from fixit.ftypes import Result

@given(st.builds(Result, 
    path=st.builds(Path, st.text(min_size=1)),
    violation=st.none(),
    error=st.none()
))
def test_print_result_returns_bool_not_int(result):
    """The function is annotated as -> int but returns bool values."""
    return_value = print_result(result)
    # While bool is a subclass of int in Python, the semantic intent
    # is clearly boolean (True for dirty, False for clean)
    assert isinstance(return_value, bool)
    assert return_value in [True, False]
```

**Failing input**: Any valid Result object demonstrates the type mismatch

## Reproducing the Bug

```python
import sys
from pathlib import Path
sys.path.insert(0, "/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages")

from fixit.api import print_result
from fixit.ftypes import Result
import io
import contextlib

# Check the function annotation
print(f"Function annotation: {print_result.__annotations__}")
# Output: {'result': <class 'fixit.ftypes.Result'>, 'show_diff': <class 'bool'>, 'stderr': <class 'bool'>, 'return': <class 'int'>}

# Test actual return values
clean_result = Result(path=Path("test.py"), violation=None, error=None)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    return_value = print_result(clean_result)

print(f"Return value: {return_value}, Type: {type(return_value)}")
# Output: Return value: False, Type: <class 'bool'>
```

## Why This Is A Bug

The function signature on line 27 declares `-> int` as the return type, but:
1. The docstring (line 34) explicitly states: "Returns ``True`` if the result is "dirty""
2. The implementation returns `True` (lines 56, 63) or `False` (line 67)
3. Callers expect boolean semantics (True = dirty, False = clean)

While `bool` is technically a subclass of `int` in Python, the type annotation should reflect the semantic intent of the function, which is clearly boolean.

## Fix

```diff
--- a/fixit/api.py
+++ b/fixit/api.py
@@ -24,7 +24,7 @@ LOG = logging.getLogger(__name__)
 
 def print_result(
     result: Result, *, show_diff: bool = False, stderr: bool = False
-) -> int:
+) -> bool:
     """
     Print linting results in a simple format designed for human eyes.
```