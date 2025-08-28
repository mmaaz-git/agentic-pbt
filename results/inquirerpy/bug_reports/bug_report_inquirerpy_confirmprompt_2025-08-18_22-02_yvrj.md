# Bug Report: ConfirmPrompt Crashes on Unicode Characters That Expand When Uppercased

**Target**: `InquirerPy.prompts.ConfirmPrompt`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

ConfirmPrompt crashes with ValueError when given certain Unicode characters as confirm_letter or reject_letter, specifically those that expand to multiple characters when uppercased (e.g., German eszett 'ß' -> 'SS').

## Property-Based Test

```python
from hypothesis import given, strategies as st
from InquirerPy.prompts import ConfirmPrompt
import pytest

@given(
    default=st.booleans(),
    confirm_letter=st.text(min_size=1, max_size=1).filter(lambda x: x.isalpha()),
    reject_letter=st.text(min_size=1, max_size=1).filter(lambda x: x.isalpha())
)
def test_confirm_prompt_unicode_handling(default, confirm_letter, reject_letter):
    assume(confirm_letter != reject_letter)
    
    prompt = ConfirmPrompt(
        message="Test",
        default=default,
        confirm_letter=confirm_letter,
        reject_letter=reject_letter
    )
    
    assert isinstance(prompt._default, bool)
```

**Failing input**: `confirm_letter='y', reject_letter='ß'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.prompts import ConfirmPrompt

prompt = ConfirmPrompt(
    message="Test",
    confirm_letter='y',
    reject_letter='ß'
)
```

## Why This Is A Bug

The ConfirmPrompt accepts single-character strings for confirm_letter and reject_letter parameters. However, it internally creates keybindings for both the lowercase and uppercase versions (lines 123-130 in confirm.py). When a character like 'ß' is uppercased, it becomes 'SS' (two characters), which the key binding system cannot parse as a single key, resulting in "ValueError: Invalid key: SS". This violates the API contract that single characters should be accepted.

## Fix

Check that uppercased characters remain single characters, or handle multi-character uppercase expansions gracefully:

```diff
--- a/InquirerPy/prompts/confirm.py
+++ b/InquirerPy/prompts/confirm.py
@@ -120,14 +120,22 @@ class ConfirmPrompt(BaseSimplePrompt):
 
         if not keybindings:
             keybindings = {}
+        
+        # Build keybindings, handling unicode expansion
+        confirm_keys = [{"key": self._confirm_letter}]
+        reject_keys = [{"key": self._reject_letter}]
+        
+        # Only add uppercase version if it remains a single character
+        if len(self._confirm_letter.upper()) == 1:
+            confirm_keys.append({"key": self._confirm_letter.upper()})
+        if len(self._reject_letter.upper()) == 1:
+            reject_keys.append({"key": self._reject_letter.upper()})
+        
         self.kb_maps = {
-            "confirm": [
-                {"key": self._confirm_letter},
-                {"key": self._confirm_letter.upper()},
-            ],
-            "reject": [
-                {"key": self._reject_letter},
-                {"key": self._reject_letter.upper()},
-            ],
+            "confirm": confirm_keys,
+            "reject": reject_keys,
             "any": [{"key": Keys.Any}],
             **keybindings,
         }
```