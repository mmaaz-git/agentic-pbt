#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from spnego.channel_bindings import GssChannelBindings, AddressType

# Test case 1: None application_data becomes empty bytes
original = GssChannelBindings(
    initiator_addrtype=AddressType.unspecified,
    initiator_address=None,
    acceptor_addrtype=AddressType.unspecified,
    acceptor_address=None,
    application_data=None
)

packed = original.pack()
unpacked = GssChannelBindings.unpack(packed)

print("Test 1: None values become empty bytes")
print(f"Original initiator_address: {original.initiator_address!r}")
print(f"Unpacked initiator_address: {unpacked.initiator_address!r}")
print(f"Original acceptor_address: {original.acceptor_address!r}")
print(f"Unpacked acceptor_address: {unpacked.acceptor_address!r}")
print(f"Original application_data: {original.application_data!r}")
print(f"Unpacked application_data: {unpacked.application_data!r}")
print()

# Test whether equality also fails
print(f"Are they equal? {unpacked == original}")
print()

# Test case 2: Empty bytes remain empty bytes
original2 = GssChannelBindings(
    initiator_addrtype=AddressType.unspecified,
    initiator_address=b'',
    acceptor_addrtype=AddressType.unspecified,
    acceptor_address=b'',
    application_data=b''
)

packed2 = original2.pack()
unpacked2 = GssChannelBindings.unpack(packed2)

print("Test 2: Empty bytes remain empty bytes")
print(f"Original initiator_address: {original2.initiator_address!r}")
print(f"Unpacked initiator_address: {unpacked2.initiator_address!r}")
print(f"Original acceptor_address: {original2.acceptor_address!r}")
print(f"Unpacked acceptor_address: {unpacked2.acceptor_address!r}")
print(f"Original application_data: {original2.application_data!r}")
print(f"Unpacked application_data: {unpacked2.application_data!r}")
print()

print(f"Are they equal? {unpacked2 == original2}")
print()

# Test that the packed data is the same for None and b''
print("Test 3: None and b'' produce the same packed data")
print(f"Packed with None values: {packed.hex()}")
print(f"Packed with b'' values: {packed2.hex()}")
print(f"Are packed bytes identical? {packed == packed2}")