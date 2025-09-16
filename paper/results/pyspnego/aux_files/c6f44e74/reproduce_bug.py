#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

import spnego.channel_bindings as cb

# Create a GssChannelBindings with None values
original = cb.GssChannelBindings(
    initiator_addrtype=cb.AddressType.unspecified,
    initiator_address=None,
    acceptor_addrtype=cb.AddressType.unspecified,
    acceptor_address=None,
    application_data=None,
)

print("Original object:")
print(f"  initiator_address: {original.initiator_address!r}")
print(f"  acceptor_address: {original.acceptor_address!r}")
print(f"  application_data: {original.application_data!r}")

# Pack and unpack
packed = original.pack()
unpacked = cb.GssChannelBindings.unpack(packed)

print("\nUnpacked object:")
print(f"  initiator_address: {unpacked.initiator_address!r}")
print(f"  acceptor_address: {unpacked.acceptor_address!r}")
print(f"  application_data: {unpacked.application_data!r}")

print("\nComparison:")
print(f"  initiator_address equal? {original.initiator_address == unpacked.initiator_address}")
print(f"  acceptor_address equal? {original.acceptor_address == unpacked.acceptor_address}")
print(f"  application_data equal? {original.application_data == unpacked.application_data}")
print(f"  Objects equal? {original == unpacked}")

# The bug: None becomes b'' after round-trip
assert original.initiator_address == unpacked.initiator_address, f"initiator_address mismatch: {original.initiator_address!r} != {unpacked.initiator_address!r}"