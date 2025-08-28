# Bug Report: aiogram.types InlineKeyboardButton Missing Validation

**Target**: `aiogram.types.InlineKeyboardButton`
**Severity**: High
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

InlineKeyboardButton accepts invalid configurations that violate Telegram Bot API specification, which states "Exactly one of the optional fields must be used to specify type of the button."

## Property-Based Test

```python
@given(text=text_strategy)
def test_inline_keyboard_button_without_action(text):
    button = types.InlineKeyboardButton(text=text)
    action_fields = [
        button.url, button.callback_data, button.switch_inline_query,
        button.switch_inline_query_current_chat, button.pay,
        button.web_app, button.login_url, button.switch_inline_query_chosen_chat,
        button.copy_text, button.callback_game
    ]
    assert all(field is None for field in action_fields)
```

**Failing input**: Any text value, e.g., `text="Click me"`

## Reproducing the Bug

```python
import aiogram.types as types

# Bug 1: Button with NO action fields (should be rejected)
button_no_action = types.InlineKeyboardButton(text="Click me")
print(f"Button created with no action: {button_no_action}")
print(f"All action fields are None: {button_no_action.callback_data is None and button_no_action.url is None}")

# Bug 2: Button with MULTIPLE action fields (should be rejected)  
button_multi = types.InlineKeyboardButton(
    text="Multi",
    url="https://example.com",
    callback_data="callback",
    pay=True
)
print(f"Button created with 3 actions: url={button_multi.url}, callback_data={button_multi.callback_data}, pay={button_multi.pay}")
```

## Why This Is A Bug

The Telegram Bot API documentation explicitly states that inline keyboard buttons must have exactly one action field set. Accepting buttons without any action or with multiple actions will cause:
1. API rejection when sending the keyboard to Telegram
2. Runtime errors in production bots
3. Confusing behavior for developers who expect validation

## Fix

Add validation in InlineKeyboardButton's `__init__` or use Pydantic validators:

```diff
+ from pydantic import model_validator
  
  class InlineKeyboardButton(BaseModel):
      text: str
      url: Optional[str] = None
      callback_data: Optional[str] = None
      # ... other fields ...
      
+     @model_validator(mode='after')
+     def validate_exactly_one_action(self):
+         action_fields = [
+             self.url, self.callback_data, self.web_app,
+             self.login_url, self.switch_inline_query,
+             self.switch_inline_query_current_chat,
+             self.switch_inline_query_chosen_chat,
+             self.copy_text, self.callback_game, self.pay
+         ]
+         action_count = sum(1 for field in action_fields if field is not None)
+         if action_count != 1:
+             raise ValueError(f"Exactly one action field must be set, got {action_count}")
+         return self
```