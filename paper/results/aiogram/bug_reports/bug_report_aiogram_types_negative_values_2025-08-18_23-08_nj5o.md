# Bug Report: aiogram.types Accepts Negative Values for Non-Negative Fields

**Target**: `aiogram.types.MessageEntity`, `aiogram.types.PhotoSize`, `aiogram.types.Video`, `aiogram.types.PollOption`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Multiple aiogram type classes accept negative values for fields that should be non-negative (dimensions, offsets, lengths, durations, counts), violating logical constraints and Telegram API expectations.

## Property-Based Test

```python
@given(
    offset=st.integers(min_value=-1000, max_value=1000),
    length=st.integers(min_value=-1000, max_value=1000)
)
def test_message_entity_accepts_negative_values(offset, length):
    entity = types.MessageEntity(type='bold', offset=offset, length=length)
    assert entity.offset == offset
    assert entity.length == length
```

**Failing input**: `offset=-10, length=-5`

## Reproducing the Bug

```python
import aiogram.types as types

# MessageEntity with negative offset and length
entity = types.MessageEntity(type="bold", offset=-10, length=-5)
print(f"MessageEntity: offset={entity.offset}, length={entity.length}")

# PhotoSize with negative dimensions
photo = types.PhotoSize(
    file_id="photo123",
    file_unique_id="unique123",
    width=-100,
    height=-200
)
print(f"PhotoSize: width={photo.width}, height={photo.height}")

# PollOption with negative voter count
poll_option = types.PollOption(text="Option", voter_count=-50)
print(f"PollOption: voter_count={poll_option.voter_count}")

# Video with negative duration
video = types.Video(
    file_id="video123",
    file_unique_id="unique123",
    width=100,
    height=100,
    duration=-30
)
print(f"Video: duration={video.duration}")
```

## Why This Is A Bug

Negative values for these fields are illogical and will cause:
1. API rejection when sending to Telegram
2. Rendering issues or crashes in Telegram clients
3. Logical errors in bot code that assumes non-negative values
4. Data corruption when persisting these objects

## Fix

Add field validators to ensure non-negative values:

```diff
+ from pydantic import Field, field_validator
  
  class MessageEntity(BaseModel):
      type: str
-     offset: int
-     length: int
+     offset: int = Field(ge=0)
+     length: int = Field(ge=0)
      
  class PhotoSize(BaseModel):
-     width: int
-     height: int
+     width: int = Field(gt=0)
+     height: int = Field(gt=0)
      
  class Video(BaseModel):
-     duration: int
+     duration: int = Field(ge=0)
      
  class PollOption(BaseModel):
-     voter_count: int
+     voter_count: int = Field(ge=0)
```