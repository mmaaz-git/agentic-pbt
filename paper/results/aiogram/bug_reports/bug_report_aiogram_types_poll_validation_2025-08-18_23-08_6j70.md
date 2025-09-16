# Bug Report: aiogram.types.Poll Missing Options Validation

**Target**: `aiogram.types.Poll`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Poll accepts invalid configurations including empty options lists and single options, violating Telegram Bot API requirement that polls must have at least 2 options.

## Property-Based Test

```python
@given(
    option_texts=st.lists(text_strategy, min_size=0, max_size=10),
    voter_counts=st.lists(st.integers(min_value=-100, max_value=100), min_size=0, max_size=10)
)
def test_poll_accepts_invalid_configurations(option_texts, voter_counts):
    min_len = min(len(option_texts), len(voter_counts))
    options = [
        types.PollOption(text=text, voter_count=count)
        for text, count in zip(option_texts[:min_len], voter_counts[:min_len])
    ]
    
    poll = types.Poll(
        id="test_poll",
        question="Question?",
        options=options,
        total_voter_count=sum(voter_counts[:min_len]) if voter_counts else 0,
        is_closed=False,
        is_anonymous=True,
        type="regular",
        allows_multiple_answers=False
    )
    assert poll.options == options
```

**Failing input**: `options=[]` or `options=[PollOption(text="Only", voter_count=0)]`

## Reproducing the Bug

```python
import aiogram.types as types

# Bug 1: Poll with empty options list
empty_poll = types.Poll(
    id="poll1",
    question="Question?",
    options=[],  # Empty - should require at least 2
    total_voter_count=0,
    is_closed=False,
    is_anonymous=True,
    type="regular",
    allows_multiple_answers=False
)
print(f"Empty poll created with {len(empty_poll.options)} options")

# Bug 2: Poll with single option
single_option_poll = types.Poll(
    id="poll2",
    question="Question?",
    options=[types.PollOption(text="Only option", voter_count=0)],
    total_voter_count=0,
    is_closed=False,
    is_anonymous=True,
    type="regular",
    allows_multiple_answers=False
)
print(f"Single-option poll created with {len(single_option_poll.options)} options")

# Bug 3: Poll with inconsistent voter counts
opt1 = types.PollOption(text="Option 1", voter_count=100)
opt2 = types.PollOption(text="Option 2", voter_count=200)
inconsistent_poll = types.Poll(
    id="poll3",
    question="Question?",
    options=[opt1, opt2],
    total_voter_count=50,  # Should be 300 for single-answer poll
    is_closed=False,
    is_anonymous=True,
    type="regular",
    allows_multiple_answers=False
)
print(f"Poll total_voter_count: {inconsistent_poll.total_voter_count}")
print(f"Sum of option votes: {sum(o.voter_count for o in inconsistent_poll.options)}")
```

## Why This Is A Bug

The Telegram Bot API requires polls to have between 2 and 10 options. Accepting invalid poll configurations will cause:
1. API rejection when sending the poll
2. Runtime errors in production bots
3. Logical inconsistencies in vote counting

## Fix

Add validation to ensure polls have at least 2 options:

```diff
+ from pydantic import field_validator
  
  class Poll(BaseModel):
      id: str
      question: str
      options: List[PollOption]
      total_voter_count: int
      # ... other fields ...
      
+     @field_validator('options')
+     @classmethod
+     def validate_options_count(cls, v):
+         if len(v) < 2:
+             raise ValueError(f"Poll must have at least 2 options, got {len(v)}")
+         if len(v) > 10:
+             raise ValueError(f"Poll can have at most 10 options, got {len(v)}")
+         return v
```