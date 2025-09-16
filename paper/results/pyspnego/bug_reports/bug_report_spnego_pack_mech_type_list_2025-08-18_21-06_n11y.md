# Bug Report: spnego._spnego.pack_mech_type_list OID Encoding Overflow

**Target**: `spnego._spnego.pack_mech_type_list`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The pack_mech_type_list function crashes with ValueError when encoding OIDs where the first two components result in a value >= 256, violating the ASN.1 OID encoding specification.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import spnego._spnego as sp

@st.composite
def valid_oid_strategy(draw):
    first = draw(st.sampled_from([0, 1, 2]))
    if first in [0, 1]:
        second = draw(st.integers(min_value=0, max_value=39))
    else:
        second = draw(st.integers(min_value=0, max_value=255))
    rest = draw(st.lists(st.integers(min_value=0, max_value=2**31-1), min_size=0, max_size=5))
    components = [first, second] + rest
    return ".".join(str(c) for c in components)

@given(st.lists(valid_oid_strategy(), min_size=1, max_size=10))
def test_pack_mech_type_list_round_trip(oid_list):
    packed = sp.pack_mech_type_list(oid_list)
    # Should be able to pack any valid OID
    assert isinstance(packed, bytes)
```

**Failing input**: `['2.176']`

## Reproducing the Bug

```python
import spnego._spnego as sp

# This OID causes (2 * 40) + 176 = 256, which overflows byte range
oid = '2.176'
try:
    sp.pack_mech_type_list([oid])
except ValueError as e:
    print(f"Error: {e}")  # Error: byte must be in range(0, 256)

# Boundary test shows 2.175 works, 2.176 fails
sp.pack_mech_type_list(['2.175'])  # Works
sp.pack_mech_type_list(['2.176'])  # Fails
```

## Why This Is A Bug

The ASN.1 OID encoding specification states that the first octet encodes the first two OID components as `(first * 40) + second`. When `first=2`, the valid range for `second` should be 0-175, not 0-255 as the code assumes. The bug violates the constraint that the encoded value must fit in a single byte (0-255).

## Fix

```diff
--- a/spnego/_asn1.py
+++ b/spnego/_asn1.py
@@ -354,8 +354,13 @@ def pack_asn1_object_identifier(
     if len(oid_split) < 2:
         raise ValueError("An OID must have 2 or more elements split by '.'")
 
+    # Validate first two components stay within byte range
+    first_byte = (oid_split[0] * 40) + oid_split[1]
+    if first_byte > 255:
+        raise ValueError(f"OID components {oid_split[0]}.{oid_split[1]} encode to {first_byte}, exceeding byte range")
+    
     # The first byte of the OID is the first 2 elements (x.y) as (x * 40) + y
-    b_oid.append((oid_split[0] * 40) + oid_split[1])
+    b_oid.append(first_byte)
 
     for val in oid_split[2:]:
         b_oid.extend(_pack_asn1_octet_number(val))
```