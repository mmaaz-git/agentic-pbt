# Bug Report: GssChannelBindings None Values Lost in Pack/Unpack Round-Trip

**Target**: `spnego.channel_bindings.GssChannelBindings`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The GssChannelBindings class violates the round-trip property: `unpack(pack(x)) != x` when address fields or application_data are None. After packing and unpacking, None values become empty byte strings (b'').

## Property-Based Test

```python
from hypothesis import given, strategies as st
from spnego.channel_bindings import GssChannelBindings, AddressType

address_type_strategy = st.sampled_from(list(AddressType))
optional_bytes_strategy = st.one_of(st.none(), st.binary(min_size=0, max_size=1000))

@st.composite
def channel_bindings_strategy(draw):
    return GssChannelBindings(
        initiator_addrtype=draw(address_type_strategy),
        initiator_address=draw(optional_bytes_strategy),
        acceptor_addrtype=draw(address_type_strategy),
        acceptor_address=draw(optional_bytes_strategy),
        application_data=draw(optional_bytes_strategy)
    )

@given(channel_bindings_strategy())
def test_channel_bindings_pack_unpack_round_trip(bindings):
    packed = bindings.pack()
    unpacked = GssChannelBindings.unpack(packed)
    
    assert unpacked.initiator_address == bindings.initiator_address
    assert unpacked.acceptor_address == bindings.acceptor_address
    assert unpacked.application_data == bindings.application_data
```

**Failing input**: `GssChannelBindings(initiator_address=None, acceptor_address=None, application_data=None)`

## Reproducing the Bug

```python
from spnego.channel_bindings import GssChannelBindings, AddressType

bindings = GssChannelBindings(
    initiator_addrtype=AddressType.unspecified,
    initiator_address=None,
    acceptor_addrtype=AddressType.unspecified,
    acceptor_address=None,
    application_data=None
)

packed = bindings.pack()
unpacked = GssChannelBindings.unpack(packed)

assert unpacked.initiator_address == bindings.initiator_address  # Fails: b'' != None
assert unpacked.acceptor_address == bindings.acceptor_address    # Fails: b'' != None
assert unpacked.application_data == bindings.application_data    # Fails: b'' != None
```

## Why This Is A Bug

This violates the fundamental round-trip property expected from pack/unpack operations. Code that creates a GssChannelBindings with None values and expects to preserve that semantic distinction after serialization will fail. The issue occurs because `_pack_value` converts None to b'' before packing, making it impossible for `_unpack_value` to distinguish between an intentional empty byte string and a None value.

## Fix

```diff
--- a/spnego/channel_bindings.py
+++ b/spnego/channel_bindings.py
@@ -8,10 +8,14 @@ import typing
 
 def _pack_value(addr_type: typing.Optional["AddressType"], b: typing.Optional[bytes]) -> bytes:
     """Packs an type/data entry into the byte structure required."""
-    if not b:
-        b = b""
+    if b is None:
+        # Use a special marker for None (length = 0xFFFFFFFF)
+        return (struct.pack("<I", addr_type) if addr_type is not None else b"") + struct.pack("<I", 0xFFFFFFFF)
+    else:
+        return (struct.pack("<I", addr_type) if addr_type is not None else b"") + struct.pack("<I", len(b)) + b
 
-    return (struct.pack("<I", addr_type) if addr_type is not None else b"") + struct.pack("<I", len(b)) + b
 
 def _unpack_value(b_mem: memoryview, offset: int) -> typing.Tuple[bytes, int]:
     """Unpacks a raw C struct value to a byte string."""
     length = struct.unpack("<I", b_mem[offset : offset + 4].tobytes())[0]
+    
+    # Check for None marker
+    if length == 0xFFFFFFFF:
+        return None, offset + 4
+    
     new_offset = offset + length + 4
 
     data = b""
```

Note: This fix uses a sentinel value (0xFFFFFFFF) to distinguish None from empty bytes. An alternative approach would be to change the return type of unpack_value to Optional[bytes] and handle the distinction more explicitly throughout the codebase.