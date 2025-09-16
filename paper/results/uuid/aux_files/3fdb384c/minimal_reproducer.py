import uuid

fields = (0, 0, 0, 0x40, 0x00, 0)
u = uuid.UUID(fields=fields)

expected_clock_seq = (0x40 << 8) | 0x00  
actual_clock_seq = u.clock_seq

print(f"Expected clock_seq: {expected_clock_seq}")
print(f"Actual clock_seq: {actual_clock_seq}")
assert expected_clock_seq == actual_clock_seq, "Bug: clock_seq is incorrect for non-RFC 4122 UUIDs"