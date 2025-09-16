# Bug Report: click.shell_completion Bash Version Comparison Uses String Instead of Numeric Comparison

**Target**: `click.shell_completion.BashComplete._check_version`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The Bash version check in `BashComplete._check_version()` uses string comparison instead of numeric comparison, causing it to incorrectly warn about versions like 4.10, 10.0, etc., being "older than 4.4".

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock
import click.shell_completion as shell_completion


@given(
    major=st.integers(min_value=1, max_value=99),
    minor=st.integers(min_value=0, max_value=99),
    patch_ver=st.integers(min_value=0, max_value=99)
)
@settings(max_examples=1000)
def test_bash_version_comparison_property(major, minor, patch_ver):
    """Version comparison should use numeric comparison, not string comparison"""
    
    version_string = f"{major}.{minor}.{patch_ver}"
    
    # Expected behavior: warn if version < 4.4
    should_warn = (major < 4) or (major == 4 and minor < 4)
    
    # Test actual behavior
    mock_result = MagicMock()
    mock_result.stdout = version_string.encode()
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('shutil.which', return_value='/bin/bash'):
            with patch('click.shell_completion.echo') as mock_echo:
                shell_completion.BashComplete._check_version()
                
                actually_warned = mock_echo.called
                
                assert actually_warned == should_warn
```

**Failing input**: `major=10, minor=0, patch_ver=0`

## Reproducing the Bug

```python
from unittest.mock import patch, MagicMock
import click.shell_completion as shell_completion

# Simulate Bash version 4.10 (should NOT trigger warning)
version_output = "4.10.0"

mock_result = MagicMock()
mock_result.stdout = version_output.encode()

with patch('subprocess.run', return_value=mock_result):
    with patch('shutil.which', return_value='/bin/bash'):
        with patch('click.shell_completion.echo') as mock_echo:
            shell_completion.BashComplete._check_version()
            
            if mock_echo.called:
                print(f"BUG: Bash {version_output} incorrectly triggers warning!")
                print("Message:", mock_echo.call_args[0][0])

# Demonstrates the core issue
print(f'"10" < "4" = {"10" < "4"}  (string comparison)')
print(f'10 < 4 = {10 < 4}  (numeric comparison)')
```

## Why This Is A Bug

The version comparison uses string comparison (`major < "4"`) instead of numeric comparison (`int(major) < 4`). In Python, string comparison is lexicographic, so `"10" < "4"` evaluates to `True` because the character '1' comes before '4'. This causes valid Bash versions like 4.10, 10.0, or 20.0 to incorrectly trigger the "version too old" warning.

## Fix

```diff
--- a/click/shell_completion.py
+++ b/click/shell_completion.py
@@ -320,7 +320,7 @@ class BashComplete(ShellComplete):
         if match is not None:
             major, minor = match.groups()
 
-            if major < "4" or major == "4" and minor < "4":
+            if int(major) < 4 or (int(major) == 4 and int(minor) < 4):
                 echo(
                     _(
                         "Shell completion is not supported for Bash"
```