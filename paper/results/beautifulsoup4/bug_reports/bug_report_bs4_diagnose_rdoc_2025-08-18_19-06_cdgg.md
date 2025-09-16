# Bug Report: bs4.diagnose.rdoc() Generates Fewer Elements Than Requested

**Target**: `bs4.diagnose.rdoc`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `rdoc(num_elements)` function in bs4.diagnose can generate fewer elements than the `num_elements` parameter specifies, including generating zero elements when num_elements > 0.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import bs4.diagnose as diagnose

@given(st.integers(min_value=1, max_value=100))
def test_rdoc_generates_elements(num_elements):
    """rdoc() should generate at least one element when num_elements > 0"""
    result = diagnose.rdoc(num_elements)
    content = result[6:-7]  # Extract content between '<html>' and '</html>'
    assert len(content) > 0, f"Expected non-empty content for {num_elements} elements"
```

**Failing input**: `num_elements=1` (with certain random seeds)

## Reproducing the Bug

```python
import bs4.diagnose as diagnose
import random

# Demonstrate the bug with specific seed
random.seed(0)
result = diagnose.rdoc(1)
print(f"rdoc(1) with seed 0: {result}")

# Count failures across multiple seeds
empty_count = 0
for seed in range(100):
    random.seed(seed)
    result = diagnose.rdoc(1)
    content = result[6:-7]
    if len(content) == 0:
        empty_count += 1

print(f"Out of 100 tests: {empty_count} produced empty content (~{empty_count}%)")
```

## Why This Is A Bug

The function parameter `num_elements` implies it will generate that number of elements. However, the implementation uses `random.randint(0, 3)` where choice 3 does nothing, causing ~25% of iterations to add no element. This means `rdoc(n)` generates between 0 and n elements, not n elements as expected.

## Fix

```diff
--- a/bs4/diagnose.py
+++ b/bs4/diagnose.py
@@ -199,9 +199,9 @@ def rdoc(num_elements: int = 1000) -> str:
     tag_names = ["p", "div", "span", "i", "b", "script", "table"]
     elements = []
     for i in range(num_elements):
-        choice = random.randint(0, 3)
+        choice = random.randint(0, 2)
         if choice == 0:
             # New tag.
             tag_name = random.choice(tag_names)
             elements.append("<%s>" % tag_name)
         elif choice == 1:
```