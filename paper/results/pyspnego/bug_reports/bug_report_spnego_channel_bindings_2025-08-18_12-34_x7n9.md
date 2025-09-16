# Bug Report: spnego.channel_bindings.GssChannelBindings Round-Trip Serialization Failure

**Target**: `spnego.channel_bindings.GssChannelBindings`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `GssChannelBindings` class fails to preserve the distinction between `None` and empty bytes (`b''`) during pack/unpack operations, violating the expected round-trip property.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from spnego.channel_bindings import GssChannelBindings, AddressType

address_type_strategy = st.sampled_from(list(AddressType))
optional_bytes_strategy = st.one_of(st.none(), st.binary(min_size=0, max_size=1000))

@given(
    initiator_addrtype=address_type_strategy,
    initiator_address=optional_bytes_strategy,
    acceptor_addrtype=address_type_strategy,
    acceptor_address=optional_bytes_strategy,
    application_data=optional_bytes_strategy
)
def test_gss_channel_bindings_pack_unpack_round_trip(
    initiator_addrtype, initiator_address, acceptor_addrtype, acceptor_address, application_data
):
    original = GssChannelBindings(
        initiator_addrtype=initiator_addrtype,
        initiator_address=initiator_address,
        acceptor_addrtype=acceptor_addrtype,
        acceptor_address=acceptor_address,
        application_data=application_data
    )
    
    packed = original.pack()
    unpacked = GssChannelBindings.unpack(packed)
    
    assert unpacked.initiator_address == original.initiator_address
    assert unpacked.acceptor_address == original.acceptor_address
    assert unpacked.application_data == original.application_data
```

**Failing input**: `GssChannelBindings` with any `None` value for address or application_data fields

## Reproducing the Bug

```python
from spnego.channel_bindings import GssChannelBindings, AddressType

original = GssChannelBindings(
    initiator_addrtype=AddressType.unspecified,
    initiator_address=None,
    acceptor_addrtype=AddressType.unspecified,
    acceptor_address=None,
    application_data=None
)

packed = original.pack()
unpacked = GssChannelBindings.unpack(packed)

print(f"Original initiator_address: {original.initiator_address!r}")
print(f"Unpacked initiator_address: {unpacked.initiator_address!r}")

assert unpacked.initiator_address == original.initiator_address
```

## Why This Is A Bug

The round-trip property `unpack(pack(x)) == x` should hold for serialization methods. The current implementation loses information by converting `None` values to empty bytes (`b''`), making it impossible to distinguish between:
- `None`: indicating no value/unspecified
- `b''`: indicating an explicitly empty value

This distinction is semantically important in security contexts where channel bindings are used.

## Fix

The issue is in the `_pack_value` function which converts `None` to `b''`. A proper fix would require encoding the None/empty distinction in the packed format. Here's a potential approach:

```diff
--- a/spnego/channel_bindings.py
+++ b/spnego/channel_bindings.py
@@ -8,9 +8,11 @@ import typing
 
 def _pack_value(addr_type: typing.Optional["AddressType"], b: typing.Optional[bytes]) -> bytes:
     """Packs an type/data entry into the byte structure required."""
-    if not b:
+    if b is None:
+        # Use special length value (0xFFFFFFFF) to indicate None
+        return (struct.pack("<I", addr_type) if addr_type is not None else b"") + struct.pack("<I", 0xFFFFFFFF)
+    elif not b:
         b = b""
-
     return (struct.pack("<I", addr_type) if addr_type is not None else b"") + struct.pack("<I", len(b)) + b
 
 
@@ -18,10 +20,13 @@ def _unpack_value(b_mem: memoryview, offset: int) -> typing.Tuple[bytes, int]:
     """Unpacks a raw C struct value to a byte string."""
     length = struct.unpack("<I", b_mem[offset : offset + 4].tobytes())[0]
     new_offset = offset + length + 4
+    
+    if length == 0xFFFFFFFF:
+        return None, offset + 4
 
     data = b""
     if length:
         data = b_mem[offset + 4 : offset + 4 + length].tobytes()
 
     return data, new_offset
```

Note: This fix changes the serialization format and may have compatibility implications.