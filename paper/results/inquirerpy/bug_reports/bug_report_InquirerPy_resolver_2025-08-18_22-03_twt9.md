# Bug Report: InquirerPy.resolver._get_questions Mutation Bug

**Target**: `InquirerPy.resolver._get_questions`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_get_questions` function returns the same list object when given a list input, allowing unintended mutations to the original questions list.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from InquirerPy.resolver import _get_questions

@given(st.just([]))
def test_get_questions_returns_same_object(questions):
    """_get_questions should not return the same list object."""
    result = _get_questions(questions)
    assert result == questions  # Content should be equal
    assert result is not questions  # But should be different objects
```

**Failing input**: `[]` (empty list, but applies to any list input)

## Reproducing the Bug

```python
from InquirerPy.resolver import _get_questions

# Create original questions list
original_questions = [
    {"type": "input", "message": "What's your name?", "name": "name"},
    {"type": "input", "message": "What's your email?", "name": "email"},
]

# Get result from _get_questions
result = _get_questions(original_questions)

# Verify they're the same object
print(f"Same object: {result is original_questions}")  # True

# Modify the result
result.append({"type": "input", "message": "Added question", "name": "added"})

# Original is also modified
print(f"Original list length: {len(original_questions)}")  # 3 instead of 2
```

## Why This Is A Bug

This violates the principle of immutability for input parameters. Functions should not allow their return values to modify the original input. This can lead to:

1. Unexpected side effects when the same questions list is processed multiple times
2. Accumulation of modifications across multiple function calls
3. Difficult-to-debug issues when questions are reused in different contexts

## Fix

```diff
def _get_questions(questions: InquirerPyQuestions) -> List[Dict[str, Any]]:
    """Process and validate questions.

    Args:
        questions: List of questions to create prompt.

    Returns:
        List of validated questions.
    """
    if isinstance(questions, dict):
        questions = [questions]

    if not isinstance(questions, list):
        raise InvalidArgument("argument questions should be type of list or dictionary")

-    return questions
+    return questions.copy()
```