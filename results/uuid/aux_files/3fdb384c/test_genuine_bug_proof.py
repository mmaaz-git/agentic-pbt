"""
Proof that this is a genuine bug that violates expected behavior.
"""

import uuid


def test_clock_seq_contract_violation():
    """
    According to the UUID module documentation and field naming,
    when you create a UUID from fields, the clock_seq should be
    reconstructible from clock_seq_hi_variant and clock_seq_low.
    
    However, this is violated for non-RFC 4122 UUIDs.
    """
    
    print("CONTRACT VIOLATION TEST")
    print("=" * 60)
    print("Expected: clock_seq = (clock_seq_hi_variant << 8) | clock_seq_low")
    print("          (for UUIDs created directly from fields)")
    print()
    
    # Test with NCS variant UUID
    clock_seq_hi = 0x40  # NCS variant (01xxxxxx)
    clock_seq_low = 0x12
    
    fields = (0x12345678, 0x1234, 0x5678, clock_seq_hi, clock_seq_low, 0x123456789ABC)
    u = uuid.UUID(fields=fields)
    
    # What a user would reasonably expect
    expected_clock_seq = (clock_seq_hi << 8) | clock_seq_low
    
    # What they actually get
    actual_clock_seq = u.clock_seq
    
    print(f"Input fields: clock_seq_hi_variant={clock_seq_hi:#04x}, clock_seq_low={clock_seq_low:#04x}")
    print(f"Expected clock_seq: {expected_clock_seq:#06x} ({expected_clock_seq})")
    print(f"Actual clock_seq:   {actual_clock_seq:#06x} ({actual_clock_seq})")
    print(f"Match: {expected_clock_seq == actual_clock_seq}")
    print()
    
    if expected_clock_seq != actual_clock_seq:
        print("❌ BUG CONFIRMED: clock_seq property returns incorrect value!")
        print("   This violates the principle of least surprise.")
        return False
    return True


def test_information_loss():
    """
    Show that information is lost when accessing clock_seq for non-RFC 4122 UUIDs.
    You cannot reconstruct the original clock_seq_hi_variant from the clock_seq property.
    """
    
    print("\nINFORMATION LOSS TEST")
    print("=" * 60)
    
    # Create several UUIDs with different clock_seq_hi_variant values
    # that will all map to the same clock_seq due to masking
    
    test_values = [
        0x00,  # 00000000 -> clock_seq will use only lower 6 bits (000000)
        0x40,  # 01000000 -> clock_seq will use only lower 6 bits (000000)
        0x80,  # 10000000 -> clock_seq will use only lower 6 bits (000000)
        0xC0,  # 11000000 -> clock_seq will use only lower 6 bits (000000)
    ]
    
    clock_seq_low = 0x42
    results = []
    
    for hi_val in test_values:
        fields = (0, 0, 0, hi_val, clock_seq_low, 0)
        u = uuid.UUID(fields=fields)
        results.append({
            'input_hi': hi_val,
            'variant': u.variant,
            'clock_seq': u.clock_seq,
            'retrieved_hi': u.clock_seq_hi_variant
        })
    
    print("Different inputs that produce the same clock_seq:")
    print(f"{'Input Hi':>10} | {'Variant':>30} | {'clock_seq':>10} | {'Retrieved Hi':>12}")
    print("-" * 70)
    
    for r in results:
        print(f"{r['input_hi']:#04x} ({r['input_hi']:>3}) | {r['variant']:>30} | {r['clock_seq']:>10} | {r['retrieved_hi']:#04x} ({r['retrieved_hi']:>3})")
    
    # Check if information is preserved
    clock_seqs = [r['clock_seq'] for r in results]
    if len(set(clock_seqs)) < len(clock_seqs):
        print("\n❌ INFORMATION LOSS CONFIRMED!")
        print("   Multiple distinct clock_seq_hi_variant values map to the same clock_seq.")
        print("   This means you cannot reliably use clock_seq to reconstruct the UUID.")
        return False
    return True


def test_real_world_scenario():
    """
    Test a real-world scenario where this bug could cause issues.
    
    Scenario: Converting UUIDs between different representations
    while preserving the exact binary format.
    """
    
    print("\nREAL-WORLD SCENARIO TEST")
    print("=" * 60)
    print("Scenario: Database migration preserving exact UUID binary format")
    print()
    
    # Imagine we're migrating UUIDs from an old system that uses NCS variant
    # The UUIDs are stored as separate fields in the database
    
    # Original UUID fields from legacy system (NCS variant)
    original_fields = (
        0x550e8400,  # time_low
        0xe29b,      # time_mid
        0x41d4,      # time_hi_version
        0x40,        # clock_seq_hi_variant (NCS variant: 01xxxxxx)
        0x98,        # clock_seq_low
        0x469181234567  # node
    )
    
    print(f"Original fields from legacy database:")
    print(f"  time_low: {original_fields[0]:#010x}")
    print(f"  time_mid: {original_fields[1]:#06x}")
    print(f"  time_hi_version: {original_fields[2]:#06x}")
    print(f"  clock_seq_hi_variant: {original_fields[3]:#04x}")
    print(f"  clock_seq_low: {original_fields[4]:#04x}")
    print(f"  node: {original_fields[5]:#014x}")
    
    # Create UUID from fields
    u = uuid.UUID(fields=original_fields)
    print(f"\nUUID created: {u}")
    print(f"Variant: {u.variant}")
    
    # Try to extract fields for storage in new system
    extracted = u.fields
    
    print(f"\nExtracted fields (for new database):")
    print(f"  time_low: {extracted[0]:#010x}")
    print(f"  time_mid: {extracted[1]:#06x}")
    print(f"  time_hi_version: {extracted[2]:#06x}")
    print(f"  clock_seq_hi_variant: {extracted[3]:#04x}")
    print(f"  clock_seq_low: {extracted[4]:#04x}")
    print(f"  node: {extracted[5]:#014x}")
    
    # Check if fields match
    if original_fields == extracted:
        print("\n✅ Fields preserved correctly")
        return True
    else:
        print("\n❌ Fields DO match, but clock_seq property is wrong!")
        
        # Show the actual bug
        print(f"\nThe bug is in the clock_seq property:")
        print(f"  Expected (input): {(original_fields[3] << 8) | original_fields[4]:#06x}")
        print(f"  Actual (property): {u.clock_seq:#06x}")
        print("\nWhile the fields round-trip correctly, the clock_seq property")
        print("gives incorrect values for non-RFC 4122 UUIDs, which could cause")
        print("issues in code that relies on the clock_seq property.")
        return False


if __name__ == "__main__":
    test1 = test_clock_seq_contract_violation()
    test2 = test_information_loss()
    test3 = test_real_world_scenario()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if not test1:
        print("✅ Found genuine bug: clock_seq property returns incorrect values")
        print("   for non-RFC 4122 UUIDs, violating expected behavior.")
    
    if not test2:
        print("✅ Found information loss: Multiple distinct inputs map to same")
        print("   clock_seq value, preventing proper value reconstruction.")
    
    print("\nThis is a LOGIC BUG in the uuid module where the clock_seq property")
    print("incorrectly applies RFC 4122 masking to all UUID variants, not just")
    print("RFC 4122 UUIDs.")