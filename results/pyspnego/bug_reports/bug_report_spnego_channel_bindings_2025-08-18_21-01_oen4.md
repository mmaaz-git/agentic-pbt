# Bug Report: spnego.channel_bindings Pack/Unpack Round-Trip Violation

**Target**: `spnego.channel_bindings.GssChannelBindings`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `GssChannelBindings` class violates the round-trip property: `None` values for address and application_data fields become empty bytes `b''` after pack/unpack, breaking field value preservation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import spnego.channel_bindings as cb

address_type_strategy = st.sampled_from(list(cb.AddressType))
optional_bytes_strategy = st.one_of(st.none(), st.binary(max_size=1024))

gss_channel_bindings_strategy = st.builds(
    cb.GssChannelBindings,
    initiator_addrtype=address_type_strategy,
    initiator_address=optional_bytes_strategy,
    acceptor_addrtype=address_type_strategy,
    acceptor_address=optional_bytes_strategy,
    application_data=optional_bytes_strategy,
)

@given(gss_channel_bindings_strategy)
def test_pack_unpack_round_trip(obj):
    packed = obj.pack()
    unpacked = cb.GssChannelBindings.unpack(packed)
    
    assert unpacked.initiator_address == obj.initiator_address
    assert unpacked.acceptor_address == obj.acceptor_address
    assert unpacked.application_data == obj.application_data
```

**Failing input**: `GssChannelBindings(initiator_addrtype=<AddressType.unspecified: 0>, initiator_address=None, acceptor_addrtype=<AddressType.unspecified: 0>, acceptor_address=None, application_data=None)`

## Reproducing the Bug

```python
import spnego.channel_bindings as cb

original = cb.GssChannelBindings(
    initiator_addrtype=cb.AddressType.unspecified,
    initiator_address=None,
    acceptor_addrtype=cb.AddressType.unspecified,
    acceptor_address=None,
    application_data=None,
)

packed = original.pack()
unpacked = cb.GssChannelBindings.unpack(packed)

assert original.initiator_address == unpacked.initiator_address
```

## Why This Is A Bug

The pack/unpack methods should form a proper round-trip where `unpack(pack(x))` preserves all field values. However, `None` values are converted to `b''` during packing (in `_pack_value`) and remain as `b''` after unpacking, violating this invariant. This breaks code that distinguishes between `None` (no value provided) and `b''` (empty value provided).

## Fix

```diff
--- a/spnego/channel_bindings.py
+++ b/spnego/channel_bindings.py
@@ -16,12 +16,14 @@ def _pack_value(addr_type: typing.Optional["AddressType"], b: typing.Optional[b
 
 def _unpack_value(b_mem: memoryview, offset: int) -> typing.Tuple[bytes, int]:
     """Unpacks a raw C struct value to a byte string."""
     length = struct.unpack("<I", b_mem[offset : offset + 4].tobytes())[0]
     new_offset = offset + length + 4
 
-    data = b""
+    data = None
     if length:
         data = b_mem[offset + 4 : offset + 4 + length].tobytes()
+    else:
+        data = b""
 
     return data, new_offset
 
@@ -138,7 +140,7 @@ class GssChannelBindings:
         acceptor_addrtype = struct.unpack("<I", b_mem[offset : offset + 4].tobytes())[0]
         acceptor_address, offset = _unpack_value(b_mem, offset + 4)
 
         application_data = _unpack_value(b_mem, offset)[0]
 
         return GssChannelBindings(
             initiator_addrtype=initiator_addrtype,
-            initiator_address=initiator_address,
+            initiator_address=initiator_address if initiator_address != b"" else None,
             acceptor_addrtype=acceptor_addrtype,
-            acceptor_address=acceptor_address,
-            application_data=application_data,
+            acceptor_address=acceptor_address if acceptor_address != b"" else None,
+            application_data=application_data if application_data != b"" else None,
         )
```