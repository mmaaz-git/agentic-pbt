# Bug Report: argcomplete.scripts.activate_global_python_argcomplete Idempotence Violation with Carriage Returns

**Target**: `argcomplete.scripts.activate_global_python_argcomplete.append_to_config_file`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `append_to_config_file` function violates its idempotence property when the shellcode contains carriage return characters (`\r`), causing duplicate appends on repeated calls.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import tempfile
import os
from unittest.mock import patch
import argcomplete.scripts.activate_global_python_argcomplete as activate_script

@given(
    shellcode=st.text(min_size=1, max_size=1000),
    initial_content=st.text(max_size=5000)
)
def test_append_to_config_file_idempotence(shellcode, initial_content):
    """Property: Appending the same shellcode twice should not duplicate it."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        f.write(initial_content)
        f.flush()
        filepath = f.name
    
    try:
        with patch.object(activate_script, 'get_consent', return_value=True):
            activate_script.append_to_config_file(filepath, shellcode)
            
            with open(filepath, 'r') as f:
                content_after_first = f.read()
            
            activate_script.append_to_config_file(filepath, shellcode)
            
            with open(filepath, 'r') as f:
                content_after_second = f.read()
            
            assert content_after_first == content_after_second, \
                "append_to_config_file should be idempotent"
    finally:
        os.unlink(filepath)
```

**Failing input**: `shellcode='\r'`

## Reproducing the Bug

```python
import os
import tempfile
from unittest.mock import patch
import argcomplete.scripts.activate_global_python_argcomplete as activate_script

with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
    filepath = f.name

try:
    with patch.object(activate_script, 'get_consent', return_value=True):
        activate_script.append_to_config_file(filepath, '\r')
        activate_script.append_to_config_file(filepath, '\r')
        
        with open(filepath, 'rb') as f:
            content = f.read()
        
        count = content.count(b'\r')
        print(f"Carriage return appears {count} times (expected 1)")
        assert count == 1, "Idempotence violated"
finally:
    os.unlink(filepath)
```

## Why This Is A Bug

The function checks if shellcode already exists in the file before appending, intending to be idempotent. However, when the file is opened in text mode (`'r'`), Python's universal newline handling converts `\r` to `\n`. This causes the `shellcode in fh.read()` check to fail for any shellcode containing `\r`, leading to duplicate appends. This affects Windows-style line endings (`\r\n`) and any configuration containing carriage returns.

## Fix

```diff
def append_to_config_file(path, shellcode):
    if os.path.exists(path):
-       with open(path, 'r') as fh:
+       with open(path, 'rb') as fh:
-           if shellcode in fh.read():
+           if shellcode.encode() in fh.read():
                print(f"The code already exists in the file {path}.", file=sys.stderr)
                return
        print(f"argcomplete needs to append to the file {path}. The following code will be appended:", file=sys.stderr)
        for line in shellcode.splitlines():
            print(">", line, file=sys.stderr)
        if not get_consent():
            print("Not added.", file=sys.stderr)
            return
    print(f"Adding shellcode to {path}...", file=sys.stderr)
    with open(path, "a") as fh:
        fh.write(shellcode)
    print("Added.", file=sys.stderr)
```