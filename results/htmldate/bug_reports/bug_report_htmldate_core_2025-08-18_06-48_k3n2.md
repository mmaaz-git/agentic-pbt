# Bug Report: htmldate.core IndexError in select_candidate Function

**Target**: `htmldate.core.select_candidate`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `select_candidate` function in htmldate.core raises an IndexError when processing date pattern candidates that contain fewer than 2 patterns with valid 4-digit years, causing the date extraction to fail unexpectedly.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from collections import Counter
import re
from datetime import datetime
from htmldate.core import select_candidate
from htmldate.utils import Extractor

@given(
    occurrences=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.integers(min_value=1, max_value=100),
        min_size=0,
        max_size=10
    )
)
def test_select_candidate_empty_input(occurrences):
    """Test select_candidate with various Counter inputs"""
    counter = Counter(occurrences)
    catch = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
    yearpat = re.compile(r'(\d{4})')
    
    options = Extractor(
        False,  # extensive_search
        datetime(2030, 12, 31),  # max_date
        datetime(2000, 1, 1),  # min_date
        True,  # original_date
        "%Y-%m-%d"  # outputformat
    )
    
    result = select_candidate(counter, catch, yearpat, options)
    
    if result is not None:
        assert hasattr(result, 'group') or hasattr(result, 'groups')
```

**Failing input**: `occurrences={'0': 1, '00': 2}`

## Reproducing the Bug

```python
import re
from collections import Counter
from datetime import datetime
from htmldate.core import select_candidate
from htmldate.utils import Extractor

occurrences = Counter({'0': 1, '00': 2})
catch = re.compile(r'(\d{4})-(\d{2})-(\d{2})')
yearpat = re.compile(r'(\d{4})')

options = Extractor(
    False,
    datetime(2030, 12, 31),
    datetime(2000, 1, 1),
    True,
    "%Y-%m-%d"
)

result = select_candidate(occurrences, catch, yearpat, options)
```

## Why This Is A Bug

The `select_candidate` function assumes it will always have at least 2 valid year patterns when processing candidates. However, when patterns don't contain valid 4-digit years or contain fewer than 2 such patterns, the function attempts to access `years[0]` and `years[1]` (lines 397 and 405 in core.py) without checking if the `years` list has sufficient elements, causing an IndexError. This violates the function's contract to gracefully handle various input patterns and return None for invalid cases.

## Fix

```diff
--- a/htmldate/core.py
+++ b/htmldate/core.py
@@ -388,6 +388,10 @@ def select_candidate(
         for year in years
     ]
 
+    # Check if we have enough years to compare
+    if len(years) < 2:
+        return None if not years else catch.search(patterns[0]) if validation[0] else None
+
     # safety net: plausibility
     if all(validation):
         # same number of occurrences: always take top of the pile?
```