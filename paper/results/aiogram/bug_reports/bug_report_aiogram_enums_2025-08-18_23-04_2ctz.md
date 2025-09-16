# Bug Report: aiogram.enums String Representation Inconsistency

**Target**: `aiogram.enums` (all string-based enums)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

String-based enums in aiogram that inherit from `(str, Enum)` have inconsistent string behavior: while they equal their string values, `str()` returns the full enum representation instead of the value.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from aiogram.enums import ChatType, ParseMode, BotCommandScopeType

str_enums = [ChatType, ParseMode, BotCommandScopeType]  # and others

@given(st.sampled_from(str_enums))
def test_str_enum_value_equality(enum_class):
    """String enum members should equal their string values"""
    for member in enum_class:
        assert member == member.value
        assert str(member) == member.value  # This fails!
        assert isinstance(member, str)
```

**Failing input**: `BotCommandScopeType` (and all other string enums)

## Reproducing the Bug

```python
from aiogram.enums import ChatType

chat_type = ChatType.PRIVATE

assert isinstance(chat_type, str)
assert chat_type == "private"

result = str(chat_type)
assert result == "private"  # AssertionError: Got 'ChatType.PRIVATE'

# Practical impact in formatting
message = f"Chat type: {chat_type}"
assert message == "Chat type: private"  # Got "Chat type: ChatType.PRIVATE"
```

## Why This Is A Bug

This violates the Liskov Substitution Principle - objects that inherit from `str` and equal their string values should behave like strings in all string contexts. The current behavior breaks string formatting, logging, and any code expecting true string substitutability. Users expect `f"{ChatType.PRIVATE}"` to produce `"private"` not `"ChatType.PRIVATE"`.

## Fix

```diff
# In each enum file (e.g., chat_type.py)
 class ChatType(str, Enum):
     """
     This object represents a chat type
 
     Source: https://core.telegram.org/bots/api#chat
     """
 
     SENDER = "sender"
     PRIVATE = "private"
     GROUP = "group"
     SUPERGROUP = "supergroup"
     CHANNEL = "channel"
+    
+    def __str__(self):
+        return self.value
```