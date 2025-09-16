# Bug Report: pyatlan.utils.to_camel_case Idempotence and Unicode Handling Issues

**Target**: `pyatlan.utils.to_camel_case`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `to_camel_case` function has two distinct bugs: (1) it is not idempotent - applying it twice produces different results than applying it once, and (2) it doesn't preserve certain Unicode characters like the German sharp s (ß).

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyatlan.utils import to_camel_case

# Bug 1: Idempotence failure
@given(st.text(min_size=1, max_size=100))
def test_to_camel_case_idempotence(s):
    once = to_camel_case(s)
    twice = to_camel_case(once)
    assert once == twice

# Bug 2: Unicode content not preserved
@given(st.text(alphabet=st.characters(categories=["Lu", "Ll", "Nd"]), min_size=1))
def test_to_camel_case_preserves_content(s):
    result = to_camel_case(s)
    original_alphanum = ''.join(c for c in s.lower() if c.isalnum())
    result_alphanum = ''.join(c for c in result.lower() if c.isalnum())
    assert original_alphanum == result_alphanum
```

**Failing input**: 
- Bug 1: `'A A'`
- Bug 2: `'ß'`

## Reproducing the Bug

```python
from pyatlan.utils import to_camel_case

# Bug 1: Idempotence issue
input1 = 'A A'
once = to_camel_case(input1)
twice = to_camel_case(once)
print(f"Input: '{input1}'")
print(f"First application: '{once}'")  # Output: 'aA'
print(f"Second application: '{twice}'")  # Output: 'aa'
assert once == twice  # Fails!

# Bug 2: Unicode handling issue
input2 = 'ß'
result = to_camel_case(input2)
print(f"Input: '{input2}'")
print(f"Result: '{result}'")  # Output: 'ss'
assert input2.lower() == result.lower()  # Fails! 'ß' != 'ss'
```

## Why This Is A Bug

1. **Idempotence violation**: A string transformation function like `to_camel_case` should be idempotent - applying it multiple times should give the same result as applying it once. This is important for data processing pipelines where the function might be accidentally applied multiple times. The current implementation destroys camelCase formatting when applied to already camelCased strings.

2. **Unicode content alteration**: The function changes the actual content of strings containing certain Unicode characters. The German sharp s (ß) is converted to 'ss', which is a different string with different length and content. This could break string comparisons, database lookups, and data integrity in internationalized applications.

## Fix

```diff
def to_camel_case(s: str) -> str:
+    # Check if already in camelCase format to ensure idempotence
+    if s and not any(c in s for c in ['_', '-', ' ']):
+        # Already in camelCase, just ensure first letter is lowercase
+        return s[0].lower() + s[1:] if len(s) > 0 else s
+    
     s = re.sub(r"(_|-)+", " ", s).title().replace(" ", "")
     return "".join([s[0].lower(), s[1:]])
```

Note: The Unicode issue is more complex to fix as it stems from Python's `.title()` method behavior. A complete fix would require either:
1. Using a different case conversion approach that preserves Unicode characters
2. Documenting this as expected behavior and warning users about Unicode transformations
3. Implementing custom Unicode-aware title casing logic