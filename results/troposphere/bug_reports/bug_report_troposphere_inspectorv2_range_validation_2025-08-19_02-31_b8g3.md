# Bug Report: troposphere.inspectorv2 Missing Range Validation

**Target**: `troposphere.inspectorv2.PortRangeFilter`, `DateFilter`, `NumberFilter`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Range filter classes in troposphere.inspectorv2 do not validate that begin/start/lower values are less than or equal to end/upper values, allowing semantically invalid ranges.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.inspectorv2 import PortRangeFilter, DateFilter, NumberFilter

@given(st.integers(min_value=0, max_value=65535),
       st.integers(min_value=0, max_value=65535))
def test_portrange_invariant(begin, end):
    """PortRangeFilter should ensure BeginInclusive <= EndInclusive."""
    prf = PortRangeFilter(BeginInclusive=begin, EndInclusive=end)
    if 'BeginInclusive' in prf.properties and 'EndInclusive' in prf.properties:
        actual_begin = prf.properties['BeginInclusive']
        actual_end = prf.properties['EndInclusive']
        assert actual_begin <= actual_end, f"Invalid range [{actual_begin}, {actual_end}]"
```

**Failing input**: `begin=1, end=0`

## Reproducing the Bug

```python
from troposphere.inspectorv2 import PortRangeFilter, DateFilter, NumberFilter

# Bug 1: PortRangeFilter accepts invalid ranges
prf = PortRangeFilter(BeginInclusive=443, EndInclusive=80)
print(prf.properties)  # {'BeginInclusive': 443, 'EndInclusive': 80}

# Bug 2: DateFilter accepts invalid ranges
df = DateFilter(StartInclusive=200, EndInclusive=100)
print(df.properties)  # {'StartInclusive': 200, 'EndInclusive': 100}

# Bug 3: NumberFilter accepts invalid ranges
nf = NumberFilter(LowerInclusive=10.5, UpperInclusive=1.5)
print(nf.properties)  # {'LowerInclusive': 10.5, 'UpperInclusive': 1.5}

# Bug 4: PortRangeFilter accepts invalid port numbers
prf2 = PortRangeFilter(BeginInclusive=-100, EndInclusive=999999)
print(prf2.properties)  # {'BeginInclusive': -100, 'EndInclusive': 999999}
```

## Why This Is A Bug

Range filters should enforce that begin <= end to maintain semantic correctness. Invalid ranges will likely be rejected by AWS CloudFormation during deployment, causing runtime failures instead of catching errors early during object construction. Additionally, port numbers have a well-defined valid range (0-65535) that is not enforced.

## Fix

Add validation to the filter classes' `__init__` or `validate` methods to ensure range validity:

```diff
--- a/troposphere/inspectorv2.py
+++ b/troposphere/inspectorv2.py
@@ -158,6 +158,16 @@ class PortRangeFilter(AWSProperty):
     props: PropsDictType = {
         "BeginInclusive": (integer, False),
         "EndInclusive": (integer, False),
     }
+    
+    def validate(self):
+        super().validate()
+        begin = self.properties.get('BeginInclusive')
+        end = self.properties.get('EndInclusive')
+        if begin is not None and end is not None:
+            if begin > end:
+                raise ValueError(f"BeginInclusive ({begin}) must be <= EndInclusive ({end})")
+            if begin < 0 or begin > 65535 or end < 0 or end > 65535:
+                raise ValueError(f"Port numbers must be in range 0-65535")
```