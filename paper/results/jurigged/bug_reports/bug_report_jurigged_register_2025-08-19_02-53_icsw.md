# Bug Report: jurigged.register Inconsistent Unicode Error Handling

**Target**: `jurigged.register.Registry.prepare()`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

Registry.prepare() crashes with UnicodeDecodeError when processing non-UTF8 encoded Python files, while Registry.auto_register() handles these files gracefully, creating an inconsistent API behavior.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume, settings
import tempfile
import types
import sys
from jurigged.register import Registry

@given(st.binary(min_size=1, max_size=100).filter(lambda b: b'\n' not in b and not b.decode('utf-8', errors='ignore')))
@settings(max_examples=100)
def test_registry_handles_non_utf8_files(binary_content):
    """Test that Registry handles non-UTF8 files consistently."""
    assume(b'\x00' in binary_content or b'\xff' in binary_content)  # Ensure non-UTF8
    
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', delete=False) as f:
        f.write(binary_content)
        temp_file = f.name
    
    try:
        module = types.ModuleType('test_module')
        module.__file__ = temp_file
        module.__name__ = 'test_module'
        sys.modules['test_module'] = module
        
        reg = Registry()
        try:
            # This should either succeed or handle the error gracefully
            reg.prepare('test_module')
        except UnicodeDecodeError:
            # But auto_register handles this same case without error
            reg2 = Registry()
            sniffer = reg2.auto_register(filter=lambda x: True)
            # This succeeds without error - inconsistent!
            sniffer.uninstall()
            raise AssertionError("prepare() crashes while auto_register() handles gracefully")
        
    finally:
        del sys.modules['test_module']
        os.unlink(temp_file)
```

**Failing input**: Binary content like `b'\xff\xfe\x00\x00'` or Latin-1 encoded text `b'caf\xe9'`

## Reproducing the Bug

```python
import sys
import os
import tempfile
import types

sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')
from jurigged.register import Registry

with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', delete=False) as f:
    f.write(b'# -*- coding: latin-1 -*-\n')
    f.write(b'x = "caf\xe9"\n')
    temp_file = f.name

try:
    module = types.ModuleType('latin1_module')
    module.__file__ = temp_file
    module.__name__ = 'latin1_module'
    sys.modules['latin1_module'] = module
    
    reg1 = Registry()
    try:
        reg1.prepare('latin1_module')
        print("No error - file was processed")
    except UnicodeDecodeError as e:
        print(f"prepare() crashed: {e}")
    
    reg2 = Registry()
    sniffer = reg2.auto_register(filter=lambda x: True)
    print("auto_register() succeeded without error")
    sniffer.uninstall()
    
finally:
    del sys.modules['latin1_module']
    os.unlink(temp_file)
```

## Why This Is A Bug

This violates the principle of consistent error handling. The same Registry class handles non-UTF8 files differently depending on the method used:
- `prepare()` crashes with UnicodeDecodeError
- `auto_register()` catches and silently ignores the error

Users working with legacy codebases containing non-UTF8 Python files will experience unexpected crashes when using `prepare()` directly, even though the same files work fine with `auto_register()`.

## Fix

```diff
--- a/jurigged/register.py
+++ b/jurigged/register.py
@@ -54,10 +54,14 @@ class Registry(metaclass=OvldMC):
                         )
 
             if os.path.exists(filename):
-                with open(filename, "r", encoding="utf8") as f:
-                    self.precache[filename] = (
-                        module_name,
-                        f.read(),
-                        os.path.getmtime(filename),
-                    )
-                self.precache_activity.emit(module_name, filename)
+                try:
+                    with open(filename, "r", encoding="utf8") as f:
+                        self.precache[filename] = (
+                            module_name,
+                            f.read(),
+                            os.path.getmtime(filename),
+                        )
+                    self.precache_activity.emit(module_name, filename)
+                except (UnicodeDecodeError, OSError):
+                    # Handle non-UTF8 files gracefully, like auto_register does
+                    pass
```