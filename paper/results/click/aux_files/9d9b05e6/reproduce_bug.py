#!/usr/bin/env python3
from click.parser import _unpack_args

# Bug 1: nargs=0 should skip arguments but returns wrong type
print("Bug 1: nargs=0 behavior")
args = ['a', 'b', 'c']
unpacked, remaining = _unpack_args(args, [0])
print(f"Input: args={args}, nargs_spec=[0]")
print(f"Output: unpacked={unpacked}, type={type(unpacked)}")
print(f"Expected: unpacked=[], type=list")
print(f"Remaining: {remaining}")
print()

# Bug 2: Wildcard with requirements after it consumes None values incorrectly
print("Bug 2: Wildcard in middle with insufficient args")
args = ['a']
nargs_spec = [1, -1, 1]  # Requires at least 2 args, but only 1 provided
unpacked, remaining = _unpack_args(args, nargs_spec)
print(f"Input: args={args}, nargs_spec={nargs_spec}")
print(f"Output: unpacked={unpacked}")
print(f"Problem: The function fills with None even though we only have 1 arg but need 2")

# Let's count the actual consumed args
total_consumed = 0
for item in unpacked:
    if item is None:
        continue
    elif isinstance(item, tuple):
        total_consumed += len([x for x in item if x is not None])
    else:
        total_consumed += 1
        
print(f"Total consumed: {total_consumed}, len(args): {len(args)}")
print(f"Bug: Consumed args should never exceed available args!")
print()

# Simpler case
print("Bug 3: Wildcard with empty args")
args = []
nargs_spec = [1, -1, 1]
unpacked, remaining = _unpack_args(args, nargs_spec)
print(f"Input: args={args}, nargs_spec={nargs_spec}")
print(f"Output: unpacked={unpacked}")
print(f"Problem: First requires 1 arg, last requires 1 arg, but we have 0 args total")
print(f"Result creates (None, (), None) which 'consumes' 2 args from 0 available")