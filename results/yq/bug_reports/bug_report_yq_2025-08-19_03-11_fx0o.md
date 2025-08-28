# Bug Report: yq UnboundLocalError When jq Not Found

**Target**: `yq.yq` function
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The yq.yq() function raises UnboundLocalError instead of a helpful error message when the jq executable is not found or not on PATH.

## Property-Based Test

```python
@given(
    data=st.dictionaries(
        st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'),
        st.one_of(st.integers(), st.text(), st.booleans(), st.none()),
        min_size=1, max_size=5
    )
)
def test_yq_yaml_to_json_conversion(data):
    """Test that yq can convert YAML to JSON correctly."""
    yaml_str = yaml.dump(data)
    input_stream = io.StringIO(yaml_str)
    output_stream = io.StringIO()
    
    exit_code = None
    def mock_exit(code):
        nonlocal exit_code
        exit_code = code
    
    yq.yq(
        input_streams=[input_stream],
        output_stream=output_stream,
        input_format="yaml",
        output_format="json",
        jq_args=["."],
        exit_func=mock_exit
    )
```

**Failing input**: Any input when jq is not available

## Reproducing the Bug

```python
import sys
import io
import os

sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')
import yq

test_yaml = "key: value"
input_stream = io.StringIO(test_yaml)
output_stream = io.StringIO()

# Simulate jq not being found
original_path = os.environ.get('PATH', '')
os.environ['PATH'] = '/nonexistent'

def capture_exit(msg):
    pass

try:
    yq.yq(
        input_streams=[input_stream],
        output_stream=output_stream,
        input_format="yaml",
        output_format="json",
        jq_args=["."],
        exit_func=capture_exit
    )
except UnboundLocalError as e:
    print(f"BUG: UnboundLocalError - {e}")
finally:
    os.environ['PATH'] = original_path
```

## Why This Is A Bug

The code attempts to handle the case when jq is not found (lines 207-209), but has a logic error. When subprocess.Popen raises OSError, the variable 'jq' is never assigned. The custom exit_func is called but doesn't necessarily exit the program. Line 211 then tries to access jq.stdin, causing UnboundLocalError instead of the intended error message about jq not being installed.

## Fix

```diff
--- a/yq/__init__.py
+++ b/yq/__init__.py
@@ -195,6 +195,7 @@ def yq(
     converting_output = True if output_format != "json" else False
 
     try:
+        jq = None
         # Notes: universal_newlines is just a way to induce subprocess to make stdin a text buffer and encode it for us;
         # close_fds must be false for command substitution to work (yq . t.yml --slurpfile t <(yq . t.yml))
         jq = subprocess.Popen(
@@ -207,9 +208,10 @@ def yq(
     except OSError as e:
         msg = "{}: Error starting jq: {}: {}. Is jq installed and available on PATH?"
         exit_func(msg.format(program_name, type(e).__name__, e))
+        return
 
-    assert jq.stdin is not None  # this is to keep mypy happy
+    assert jq is not None and jq.stdin is not None  # this is to keep mypy happy
 
     try:
         if converting_output:
```