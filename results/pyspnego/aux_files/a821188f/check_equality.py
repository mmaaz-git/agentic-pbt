"""Check why equality returns True despite differences"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyspnego_env/lib/python3.13/site-packages')

from spnego.channel_bindings import GssChannelBindings, AddressType

# Create two bindings - one with None, one with b''
bindings_none = GssChannelBindings(
    initiator_address=None,
    acceptor_address=None,
    application_data=None
)

bindings_empty = GssChannelBindings(
    initiator_address=b'',
    acceptor_address=b'',
    application_data=b''
)

print("Comparing None vs b'' bindings:")
print(f"  bindings_none == bindings_empty: {bindings_none == bindings_empty}")

# Check their packed representations
packed_none = bindings_none.pack()
packed_empty = bindings_empty.pack()

print(f"\nPacked representations:")
print(f"  packed_none:  {packed_none!r}")
print(f"  packed_empty: {packed_empty!r}")
print(f"  Are they equal? {packed_none == packed_empty}")

print("\nThe __eq__ method (line 115-118) compares packed representations")
print("Since None and b'' pack to the same bytes, they are considered equal")
print("This masks the bug in normal equality checks but not in attribute comparisons")