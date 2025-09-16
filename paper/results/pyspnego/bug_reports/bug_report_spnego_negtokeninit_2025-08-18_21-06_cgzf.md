# Bug Report: spnego._spnego.NegTokenInit Pack/Unpack Failure with Empty mech_types

**Target**: `spnego._spnego.NegTokenInit`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

NegTokenInit fails to unpack its own packed output when initialized with an empty mech_types list, violating the round-trip property that pack/unpack should be inverse operations.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import spnego._spnego as sp

@given(
    mech_types=st.lists(st.text(min_size=1), min_size=0, max_size=5),
    mech_token=st.one_of(st.none(), st.binary(min_size=0, max_size=100))
)
def test_negtokeninit_pack_unpack_round_trip(mech_types, mech_token):
    token = sp.NegTokenInit(
        mech_types=mech_types if mech_types else None,
        mech_token=mech_token
    )
    
    packed = token.pack()
    unpacked = sp.NegTokenInit.unpack(packed)
    
    assert unpacked.mech_types == (mech_types if mech_types else [])
    assert unpacked.mech_token == mech_token
```

**Failing input**: `mech_types=[]`

## Reproducing the Bug

```python
import spnego._spnego as sp

# Create NegTokenInit with empty mech_types
token = sp.NegTokenInit(mech_types=[])
packed = token.pack()

# Try to unpack - this fails
try:
    unpacked = sp.NegTokenInit.unpack(packed)
except ValueError as e:
    print(f"Error: {e}")
    # Error: Invalid ASN.1 SEQUENCE or SEQUENCE OF tags, actual tag class TagClass.application and tag number 0
```

## Why This Is A Bug

The NegTokenInit class should handle the edge case of empty mechanism lists correctly. According to the SPNEGO specification (RFC 4178), while uncommon, an empty mech_types list is structurally valid. The pack() method successfully creates a token, but unpack() fails to parse it, violating the fundamental property that serialization and deserialization should be inverse operations.

## Fix

The issue appears to be in how the packed empty sequence is handled during unpacking. The unpack method needs to handle the case where an empty SEQUENCE is encoded, which may have different ASN.1 encoding than a non-empty sequence.

```diff
--- a/spnego/_spnego.py
+++ b/spnego/_spnego.py
@@ -371,8 +371,13 @@ class NegTokenInit:
     @classmethod
     def unpack(cls, b_data: bytes) -> "NegTokenInit":
         """Unpacks a byte string into a NegTokenInit object."""
-        neg_seq = unpack_asn1_tagged_sequence(unpack_asn1(b_data)[0])
-
+        raw_data = unpack_asn1(b_data)[0]
+        
+        # Handle empty sequence case
+        if not raw_data.b_data:
+            return cls(mech_types=[])
+        
+        neg_seq = unpack_asn1_tagged_sequence(raw_data)
         mech_types = []
         context_flags = None
         mech_token = None
```