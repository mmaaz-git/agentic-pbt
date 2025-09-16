# Bug Report: json.tool JSON Lines File Handling Bug

**Target**: `json.tool`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `json.tool` module crashes with "I/O operation on closed file" when using `--json-lines` option with file input due to premature file closure before generator consumption.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import json
import subprocess
import sys
import tempfile
from pathlib import Path

simple_json = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.lists(st.integers(), max_size=3),
    st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), max_size=3)
)

@given(st.lists(simple_json, min_size=1, max_size=5))
@settings(max_examples=10)
def test_json_lines_file_bug(data_list):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for item in data_list:
            json.dump(item, f)
            f.write('\n')
        input_file = f.name
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'json.tool', '--json-lines', '--no-indent', input_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, f"Bug: {result.stderr}"
    finally:
        Path(input_file).unlink()
```

**Failing input**: `[None]`

## Reproducing the Bug

```python
import json
import subprocess
import sys
import tempfile

with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
    json.dump({"key": "value"}, f)
    f.write('\n')
    input_file = f.name

result = subprocess.run(
    [sys.executable, '-m', 'json.tool', '--json-lines', input_file],
    capture_output=True,
    text=True
)

print(f"Exit code: {result.returncode}")
print(f"Error: {result.stderr}")
```

## Why This Is A Bug

The bug occurs in `json.tool` lines 65-71. When using `--json-lines` with file input, the code creates a generator expression `objs = (json.loads(line) for line in infile)` but then immediately closes the file in the `finally` block. When the code later tries to iterate over `objs` (line 78), the generator attempts to read from the closed file, causing the crash. This makes the `--json-lines` option completely unusable with file input.

## Fix

```diff
--- a/json/tool.py
+++ b/json/tool.py
@@ -63,7 +63,7 @@ def main():
             infile = open(options.infile, encoding='utf-8')
         try:
             if options.json_lines:
-                objs = (json.loads(line) for line in infile)
+                objs = [json.loads(line) for line in infile]
             else:
                 objs = (json.load(infile),)
         finally:
```