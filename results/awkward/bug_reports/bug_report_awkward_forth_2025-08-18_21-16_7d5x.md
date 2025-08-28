# Bug Report: awkward.forth Parser Incorrectly Handles Numeric-Prefixed Words

**Target**: `awkward.forth.ForthMachine64` and `awkward.forth.ForthMachine32`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The Forth parser incorrectly tokenizes words that begin with numeric characters, treating them as literal numbers and ignoring the non-numeric suffix, rather than recognizing them as complete word tokens or raising an error.

## Property-Based Test

```python
@given(st.integers(min_value=-1000000, max_value=1000000),
       st.integers(min_value=-1000000, max_value=1000000))
def test_2dup_operation(a, b):
    """Test that '2dup' duplicates top two elements"""
    machine = ForthMachine64(f'{a} {b} 2dup')
    machine.begin()
    machine.run()
    
    assert machine.stack == [a, b, a, b]
```

**Failing input**: `a=0, b=0`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')
from awkward.forth import ForthMachine64

machine = ForthMachine64('10 20 2dup')
machine.begin()
machine.run()
print(machine.stack)  # Output: [10, 20, 2]
# Expected: [10, 20, 10, 20]
```

## Why This Is A Bug

In standard Forth, `2dup` is a word that duplicates the top two stack elements. The parser is incorrectly treating "2dup" as the literal number "2" and ignoring or misparsing the "dup" suffix. This affects all numeric-prefixed operations:

- `2dup` → parsed as `2` (should duplicate top 2 elements)
- `2swap` → parsed as `2` (should swap top 2 pairs)
- `2drop` → parsed as `2` (should drop top 2 elements)
- `2over` → parsed as `2` (should copy 2nd pair to top)
- `0x10dup` → parsed as `269` (0x10d in hex)
- `-10dup` → parsed as `-10`

## Fix

The parser needs to be modified to properly tokenize words. When encountering a numeric character, it should continue reading until whitespace to get the complete token, then determine if it's a valid number or a word. If it contains non-numeric characters after digits (like "2dup"), it should be treated as a word token, not a number.

```diff
# In the tokenizer/parser logic:
- # Current behavior: sees "2dup", parses "2" as number, ignores "dup"
+ # Fixed behavior: sees "2dup", recognizes as complete word token
+ # Either implement as Forth word or raise "unrecognized word" error
```