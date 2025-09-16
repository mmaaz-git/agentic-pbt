# Bug Report: testpath.MockCommand Records Incorrect argv[0]

**Target**: `testpath.MockCommand`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

MockCommand records the full path to the mocked command in argv[0] instead of just the command name, which differs from standard Unix command behavior and violates mock fidelity.

## Property-Based Test

```python
@given(
    st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'),
    st.lists(
        st.text(min_size=0, max_size=20).filter(lambda x: '\x00' not in x and '\n' not in x),
        min_size=0,
        max_size=5
    )
)
def test_mock_command_recording(cmd_name, args):
    """Test that MockCommand accurately records command calls."""
    assume(cmd_name not in ['python', 'python3', 'bash', 'sh'])
    
    with MockCommand(cmd_name) as mock_cmd:
        result = subprocess.run(
            [cmd_name] + args,
            capture_output=True,
            text=True,
            shell=False
        )
        
        calls = mock_cmd.get_calls()
        assert len(calls) == 1
        
        recorded_argv = calls[0]['argv']
        expected_argv = [cmd_name] + args
        assert recorded_argv == expected_argv
```

**Failing input**: `cmd_name='a', args=[]`

## Reproducing the Bug

```python
import subprocess
from testpath import MockCommand

with MockCommand('testcmd') as mock:
    subprocess.run(['testcmd', 'arg1'], capture_output=True)
    calls = mock.get_calls()
    
    print(f"Command invoked as: ['testcmd', 'arg1']")
    print(f"Recorded argv:      {calls[0]['argv']}")
    # Output: Recorded argv: ['/tmp/tmpXXX/testcmd', 'arg1']
    
    assert calls[0]['argv'][0] == 'testcmd'  # Fails
```

## Why This Is A Bug

Real Unix commands see just the command name in argv[0] when invoked by name from PATH. Testing with a C program confirms this:

```c
// When 'mycommand' is in PATH and called as: mycommand arg1
// Real command sees: argv[0] = "mycommand"
// MockCommand records: argv[0] = "/tmp/tmpXXX/mycommand"
```

This violates the principle that mocks should behave like real commands. Code under test that examines argv[0] will see different values with MockCommand than with real commands.

## Fix

The issue occurs because MockCommand's recording script captures `sys.argv` directly, which in Python contains the full path when the script is found via PATH. The fix would be to record just the basename of argv[0]:

```diff
--- a/testpath/commands.py
+++ b/testpath/commands.py
@@ -32,9 +32,10 @@
 _record_run = """#!{python}
 import os, sys
 import json
 
 with open({recording_file!r}, 'a') as f:
-    json.dump({{'env': dict(os.environ),
-               'argv': sys.argv,
+    argv_fixed = [os.path.basename(sys.argv[0])] + sys.argv[1:]
+    json.dump({{'env': dict(os.environ), 
+               'argv': argv_fixed,
                'cwd': os.getcwd()}},
               f)
     f.write('\\x1e') # ASCII record separator
```