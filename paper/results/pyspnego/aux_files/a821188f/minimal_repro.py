"""Minimal reproduction of GssChannelBindings pack/unpack bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from spnego.channel_bindings import GssChannelBindings, AddressType

# Test case from hypothesis: all None values
bindings = GssChannelBindings(
    initiator_addrtype=AddressType.unspecified,
    initiator_address=None,
    acceptor_addrtype=AddressType.unspecified,
    acceptor_address=None,
    application_data=None
)

print("Original bindings:")
print(f"  initiator_address: {bindings.initiator_address!r}")
print(f"  acceptor_address: {bindings.acceptor_address!r}")
print(f"  application_data: {bindings.application_data!r}")

# Pack and unpack
packed = bindings.pack()
print(f"\nPacked data: {packed!r}")

unpacked = GssChannelBindings.unpack(packed)
print("\nUnpacked bindings:")
print(f"  initiator_address: {unpacked.initiator_address!r}")
print(f"  acceptor_address: {unpacked.acceptor_address!r}")
print(f"  application_data: {unpacked.application_data!r}")

# Check equality
print(f"\nAre they equal? {unpacked == bindings}")
print(f"initiator_address match? {unpacked.initiator_address == bindings.initiator_address}")
print(f"acceptor_address match? {unpacked.acceptor_address == bindings.acceptor_address}")
print(f"application_data match? {unpacked.application_data == bindings.application_data}")

# The issue: None becomes b'' after pack/unpack
print("\nBug demonstrated:")
print(f"  Original: None -> Unpacked: {unpacked.initiator_address!r}")
print(f"  This violates the round-trip property: unpack(pack(x)) != x")