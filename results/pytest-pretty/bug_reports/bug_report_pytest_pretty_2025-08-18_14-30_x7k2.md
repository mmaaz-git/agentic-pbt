# Bug Report: pytest_pretty ANSI Escape Regex Fails to Remove Many Valid Sequences

**Target**: `pytest_pretty.ansi_escape` regex
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The ANSI escape removal regex in pytest_pretty fails to remove many legitimate ANSI escape sequences, causing parsing failures when these sequences appear in test output.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest_pretty

@given(st.text())
def test_ansi_escape_removes_all_ansi_sequences(text):
    cleaned = pytest_pretty.ansi_escape.sub('', text)
    assert '\x1B' not in cleaned
```

**Failing input**: `'\x1b'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pytest-pretty_env/lib/python3.13/site-packages')
import pytest_pretty
from unittest.mock import Mock

# Bug 1: Regex doesn't remove many ANSI sequences
sequences = ['\x1b', '\x1bM', '\x1b7', '\x1b[']
for seq in sequences:
    cleaned = pytest_pretty.ansi_escape.sub('', seq)
    if '\x1b' in cleaned:
        print(f"Failed: {repr(seq)} -> {repr(cleaned)}")

# Bug 2: This causes parsing failures
mock_result = Mock()
mock_result.outlines = ['Results (1.00s):', '\x1bM       10 passed']
parseoutcomes = pytest_pretty.create_new_parseoutcomes(mock_result)
result = parseoutcomes()
print(f"Parse result: {result}, expected: {{'passed': 10}}")
```

## Why This Is A Bug

The regex pattern `(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]` only matches CSI-style sequences but misses:
1. Single-character ESC sequences (ESC M, ESC 7, ESC 8, etc.) - legitimate ANSI control codes
2. Incomplete sequences (lone ESC, ESC[) - can appear in truncated output
3. This causes `parseoutcomes` to fail when terminal output contains these sequences

## Fix

```diff
--- a/pytest_pretty/__init__.py
+++ b/pytest_pretty/__init__.py
@@ -107,7 +107,7 @@ def pytest_configure(config):
     config.pluginmanager.register(custom_reporter, 'terminalreporter')
 
 
-ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
+ansi_escape = re.compile(r'(?:\x1B(?:[@-_]|[0-?]*[ -/]*[@-~]|\[?[0-9;]*[a-zA-Z]?)?|[\x80-\x9F][0-?]*[ -/]*[@-~])')
 stat_re = re.compile(r'(\d+) (\w+)')
```