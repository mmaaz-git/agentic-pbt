# Bug Report: DefaultBotProperties LinkPreviewOptions Not Created When All Options Are False

**Target**: `aiogram.client.default.DefaultBotProperties`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-01-18

## Summary

The `DefaultBotProperties.__post_init__` method fails to create a `LinkPreviewOptions` object when all link preview options are explicitly set to `False`, incorrectly treating explicit `False` values as if the options were not provided.

## Property-Based Test

```python
@given(
    is_disabled=st.booleans(),
    prefer_small=st.booleans(),
    prefer_large=st.booleans(),
    show_above=st.booleans()
)
def test_link_preview_auto_creation(self, is_disabled, prefer_small, prefer_large, show_above):
    """Test that link_preview is automatically created when individual options are set."""
    props = DefaultBotProperties(
        link_preview_is_disabled=is_disabled,
        link_preview_prefer_small_media=prefer_small,
        link_preview_prefer_large_media=prefer_large,
        link_preview_show_above_text=show_above
    )
    
    # link_preview should be created automatically
    assert props.link_preview is not None
```

**Failing input**: `is_disabled=False, prefer_small=False, prefer_large=False, show_above=False`

## Reproducing the Bug

```python
from aiogram.client.default import DefaultBotProperties

props = DefaultBotProperties(
    link_preview_is_disabled=False,
    link_preview_prefer_small_media=False,
    link_preview_prefer_large_media=False,
    link_preview_show_above_text=False
)

assert props.link_preview is not None  # AssertionError: link_preview is None
```

## Why This Is A Bug

The `__post_init__` method uses `any()` to check if link preview options should trigger creation of a `LinkPreviewOptions` object:

```python
has_any_link_preview_option = any(
    (
        self.link_preview_is_disabled,
        self.link_preview_prefer_small_media,
        self.link_preview_prefer_large_media,
        self.link_preview_show_above_text,
    )
)
```

This logic incorrectly conflates "option not provided" (None) with "option explicitly set to False". When a user explicitly sets all options to False, they expect a LinkPreviewOptions object with all False values, not None. The current behavior makes it impossible to explicitly disable all link preview options through individual parameters.

## Fix

```diff
--- a/aiogram/client/default.py
+++ b/aiogram/client/default.py
@@ -59,11 +59,11 @@ class DefaultBotProperties:
     def __post_init__(self) -> None:
         has_any_link_preview_option = any(
-            (
-                self.link_preview_is_disabled,
-                self.link_preview_prefer_small_media,
-                self.link_preview_prefer_large_media,
-                self.link_preview_show_above_text,
-            )
+            option is not None for option in (
+                self.link_preview_is_disabled,
+                self.link_preview_prefer_small_media,
+                self.link_preview_prefer_large_media,
+                self.link_preview_show_above_text,
+            )
         )
 
         if has_any_link_preview_option and self.link_preview is None:
```