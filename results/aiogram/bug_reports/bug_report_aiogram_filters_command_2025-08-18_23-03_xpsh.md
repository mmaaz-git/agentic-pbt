# Bug Report: aiogram.filters.command Whitespace Arguments Lost

**Target**: `aiogram.filters.command.Command.extract_command`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `extract_command` method loses whitespace-only arguments, returning `None` instead of preserving the whitespace characters.

## Property-Based Test

```python
@given(
    command=command_names,
    args=st.text(min_size=1, max_size=100)
)
def test_extract_command_args_preservation(self, command, args):
    """Test that arguments are preserved correctly"""
    cmd_filter = Command("test")
    
    text = f"/{command} {args}"
    
    result = cmd_filter.extract_command(text)
    
    assert result.args == args
    assert result.command == command
```

**Failing input**: `command='A', args='\r'`

## Reproducing the Bug

```python
from aiogram.filters.command import Command

cmd = Command('test')

# Whitespace arguments are lost
text = '/test \r'
result = cmd.extract_command(text)
print(f"Input: {repr(text)}")
print(f"Result args: {repr(result.args)}")  # None instead of '\r'

# Also fails for other whitespace
whitespace_tests = ['/test \t', '/test \n', '/test    ']
for text in whitespace_tests:
    result = cmd.extract_command(text)
    print(f"{repr(text)} -> args={repr(result.args)}")  # All return None
```

## Why This Is A Bug

The bug violates the expected behavior that command arguments should be preserved as-is. Whitespace-only arguments are valid and might be meaningful in certain bot contexts. The issue stems from Python's `str.split(maxsplit=1)` behavior which strips trailing whitespace when no second part exists.

This causes:
1. Loss of user input when arguments consist only of whitespace
2. Inconsistent behavior between whitespace-only and mixed arguments
3. The `CommandObject.text` property cannot reconstruct the original input

## Fix

```diff
def extract_command(self, text: str) -> CommandObject:
-    try:
-        full_command, *args = text.split(maxsplit=1)
-    except ValueError:
-        raise CommandException("not enough values to unpack")
+    # Find first space to preserve all argument content including whitespace
+    space_idx = text.find(' ')
+    if space_idx == -1:
+        full_command = text
+        args = []
+    else:
+        full_command = text[:space_idx]
+        args = [text[space_idx + 1:]]

    prefix, (command, _, mention) = full_command[0], full_command[1:].partition("@")
    return CommandObject(
        prefix=prefix,
        command=command,
        mention=mention or None,
        args=args[0] if args else None,
    )
```