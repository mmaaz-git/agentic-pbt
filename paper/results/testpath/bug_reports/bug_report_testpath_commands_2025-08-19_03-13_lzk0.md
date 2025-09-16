# Bug Report: testpath.commands Carriage Return Conversion

**Target**: `testpath.commands.MockCommand.fixed_output`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

MockCommand.fixed_output incorrectly converts carriage returns (`\r`) to newlines (`\n`) when the output is captured using subprocess in text mode, violating the "fixed output" contract.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import subprocess
import sys
import testpath.commands as commands

@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=1, max_size=50),
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=100),
    st.integers(min_value=0, max_value=255)
)
def test_fixed_output_produces_expected_output(cmd_name, stdout, stderr, exit_status):
    test_script = f"""
import subprocess
result = subprocess.run(['{cmd_name}'], capture_output=True, text=True)
sys.stdout.write(result.stdout)
sys.stderr.write(result.stderr)
sys.exit(result.returncode)
"""
    
    with commands.MockCommand.fixed_output(cmd_name, stdout, stderr, exit_status) as mc:
        result = subprocess.run(
            [sys.executable, '-c', test_script],
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )
        
        assert result.stdout == stdout
        assert result.stderr == stderr
        assert result.returncode == exit_status
```

**Failing input**: `stdout='\r'` or `stderr='\r'`

## Reproducing the Bug

```python
import subprocess
import testpath.commands as commands

with commands.MockCommand.fixed_output('test_cmd', stdout='\r', stderr='x\ry', exit_status=0):
    result = subprocess.run(['test_cmd'], capture_output=True, text=True)
    print(f"Expected stdout: '\\r', got: {repr(result.stdout)}")
    print(f"Expected stderr: 'x\\ry', got: {repr(result.stderr)}")
```

## Why This Is A Bug

The function is named `fixed_output` and its docstring states "The stdout & stderr strings will be written to the respective streams". Users expect the exact strings they specify to appear in the output. However, due to Python's subprocess text mode behavior, carriage returns are converted to newlines. This breaks tests that need to verify programs that output carriage returns (e.g., progress bars, terminal control sequences).

## Fix

The issue stems from Python's subprocess text mode behavior. Possible fixes:

1. **Document the limitation**: Add to the docstring that carriage returns will be converted to newlines when captured in text mode.

2. **Use binary mode internally**: Modify the template to write bytes directly:

```diff
--- a/testpath/commands.py
+++ b/testpath/commands.py
@@ -44,9 +44,12 @@ _record_run = """#!{python}
 """
 
 _output_template = """\
-sys.stdout.write({!r})
-sys.stderr.write({!r})
-sys.exit({!r})
+import sys
+stdout_bytes = {!r}.encode('utf-8', 'replace')
+stderr_bytes = {!r}.encode('utf-8', 'replace')
+sys.stdout.buffer.write(stdout_bytes)
+sys.stderr.buffer.write(stderr_bytes)
+sys.exit({!r})
 """
```

Note: The second approach would preserve carriage returns but might have other implications for encoding.