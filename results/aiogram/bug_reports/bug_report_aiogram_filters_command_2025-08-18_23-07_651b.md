# Bug Report: aiogram.filters.command Whitespace Normalization Bug

**Target**: `aiogram.filters.command.CommandObject.text`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `CommandObject.text` property fails to preserve original whitespace when reconstructing command text, violating its documented contract to "Generate original text from object".

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from aiogram.filters.command import Command

@given(
    whitespace=st.sampled_from([" ", "  ", "\t", "\t\t", " \t", "\t "]),
    command=st.from_regex(r"[a-zA-Z][a-zA-Z0-9_]{0,10}", fullmatch=True),
    args=st.text(min_size=1, max_size=20).filter(lambda x: x.strip())
)
@settings(max_examples=100)
def test_whitespace_preservation_in_round_trip(whitespace, command, args):
    original = f"/{command}{whitespace}{args}"
    cmd_filter = Command(command)
    cmd_obj = cmd_filter.extract_command(original)
    reconstructed = cmd_obj.text
    assert reconstructed == original
```

**Failing input**: `/A  0` (command with double space before arguments)

## Reproducing the Bug

```python
from aiogram.filters.command import Command

user_input = "/start  John"
cmd_filter = Command("start")
cmd_obj = cmd_filter.extract_command(user_input)
reconstructed = cmd_obj.text

print(f"Original:      {user_input!r}")
print(f"Reconstructed: {reconstructed!r}")
assert reconstructed == user_input
```

## Why This Is A Bug

The `CommandObject.text` property's docstring states it will "Generate original text from object", but it normalizes all whitespace to single spaces. This breaks the round-trip property: parsing a command and then reconstructing it doesn't yield the original text when multiple spaces or tabs are present.

## Fix

```diff
 @property
 def text(self) -> str:
     """
     Generate original text from object
     """
     line = self.prefix + self.command
     if self.mention:
         line += "@" + self.mention
     if self.args:
-        line += " " + self.args
+        # Preserve original whitespace if stored, otherwise use single space
+        line += getattr(self, '_original_separator', ' ') + self.args
     return line
```

Note: A complete fix would require storing the original separator during parsing in the `extract_command` method.