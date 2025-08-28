# Bug Report: yq.yq UnboundLocalError when jq is not installed

**Target**: `yq.yq`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `yq.yq()` function raises an `UnboundLocalError` instead of a proper error message when the `jq` command is not installed or available on PATH.

## Property-Based Test

```python
@given(toml_documents)
@settings(max_examples=100)
def test_yq_function_toml_no_crash(data):
    """Test that the yq() function doesn't crash on valid TOML input."""
    toml_str = tomlkit.dumps(data)
    input_stream = io.StringIO(toml_str)
    output_stream = io.StringIO()
    
    exit_code = None
    def capture_exit(code):
        nonlocal exit_code
        exit_code = code
    
    yq.yq(
        input_streams=[input_stream],
        output_stream=output_stream,
        input_format="toml",
        output_format="json",
        jq_args=["."],
        exit_func=capture_exit
    )
```

**Failing input**: Any input when `jq` is not installed

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')
import io
import yq

toml_input = "[package]\nname = \"test\""
input_stream = io.StringIO(toml_input)
output_stream = io.StringIO()

def capture_exit(msg):
    pass

yq.yq(
    input_streams=[input_stream],
    output_stream=output_stream,
    input_format="toml",
    output_format="json",
    jq_args=["."],
    exit_func=capture_exit
)
```

## Why This Is A Bug

When `jq` is not installed, the code should provide a helpful error message like "Error starting jq: Is jq installed and available on PATH?". Instead, it crashes with `UnboundLocalError: cannot access local variable 'jq' where it is not associated with a value`.

The bug occurs because:
1. Line 200-206: `jq = subprocess.Popen(...)` is in a try block
2. Line 207-209: If `Popen` raises `OSError`, the except block calls `exit_func()` 
3. Line 211: Code continues and tries to access `jq.stdin`, but `jq` was never assigned

The code assumes `exit_func()` will terminate execution, but when a custom `exit_func` is provided (as allowed by the API), execution continues and hits the undefined variable.

## Fix

```diff
--- a/yq/__init__.py
+++ b/yq/__init__.py
@@ -207,8 +207,9 @@ def yq(
     except OSError as e:
         msg = "{}: Error starting jq: {}: {}. Is jq installed and available on PATH?"
         exit_func(msg.format(program_name, type(e).__name__, e))
+        return
 
     assert jq.stdin is not None  # this is to keep mypy happy
 
     try:
```