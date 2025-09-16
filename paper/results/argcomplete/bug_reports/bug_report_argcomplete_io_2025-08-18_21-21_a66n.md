# Bug Report: argcomplete.io File Descriptor Leak in mute_stdout()

**Target**: `argcomplete.io.mute_stdout`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `mute_stdout()` context manager in argcomplete.io fails to close the file descriptor it opens for `/dev/null`, causing a resource leak.

## Property-Based Test

```python
import sys
import os
import gc
from hypothesis import given, strategies as st, settings
import argcomplete.io


@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_mute_stdout_file_descriptor_leak(n_iterations):
    """Property: Repeated use of mute_stdout should not leak file descriptors"""
    initial_fds = len(os.listdir('/proc/self/fd'))
    
    for _ in range(n_iterations):
        with argcomplete.io.mute_stdout():
            print("test")
    
    gc.collect()
    final_fds = len(os.listdir('/proc/self/fd'))
    
    assert final_fds - initial_fds < 10
```

**Failing input**: Any usage of `mute_stdout()` leaves the file unclosed

## Reproducing the Bug

```python
import argcomplete.io
import os

original_open = open
opened_devnull = None

def tracking_open(*args, **kwargs):
    global opened_devnull
    f = original_open(*args, **kwargs)
    if args and args[0] == os.devnull:
        opened_devnull = f
    return f

import builtins
builtins.open = tracking_open

with argcomplete.io.mute_stdout():
    print("test")

assert opened_devnull.closed, f"File not closed! closed={opened_devnull.closed}"
```

## Why This Is A Bug

The `mute_stdout()` function opens `/dev/null` but never closes it, unlike `mute_stderr()` which properly closes the file. This violates the principle that resources acquired in a context manager should be released when exiting the context, potentially leading to file descriptor exhaustion in long-running processes.

## Fix

```diff
@contextlib.contextmanager
def mute_stdout():
    stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        yield
    finally:
+       sys.stdout.close()
        sys.stdout = stdout
```