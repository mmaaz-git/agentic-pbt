"""
Demonstrates a semantic inconsistency in Python's uuid module.

The issue: The UUID.clock_seq property doesn't correctly handle UUIDs 
created from raw fields when the variant is not RFC 4122.
"""

import uuid


def demonstrate_bug():
    """
    The clock_seq property assumes RFC 4122 format and masks out the upper 
    2 bits of clock_seq_hi_variant, treating them as variant bits.
    
    However, for non-RFC 4122 UUIDs, this is incorrect. The clock_seq should
    be the full 16-bit value when the UUID is not RFC 4122 compliant.
    """
    
    # Case 1: Create a UUID with NCS variant (bit pattern 0xx)
    # Here we set clock_seq_hi_variant = 0x40 (0100 0000 in binary)
    # This gives variant bits = 01 (NCS variant)
    # If clock_seq were 16 bits, it would be 0x4000 = 16384
    
    fields = (0, 0, 0, 0x40, 0x00, 0)
    u = uuid.UUID(fields=fields)
    
    print("BUG DEMONSTRATION:")
    print("=" * 50)
    print(f"Created UUID from fields: {fields}")
    print(f"UUID: {u}")
    print(f"UUID variant: {u.variant}")
    print()
    
    # The semantic issue:
    print("SEMANTIC INCONSISTENCY:")
    print(f"  clock_seq_hi_variant field value: {fields[3]} (0x{fields[3]:02x})")
    print(f"  clock_seq_low field value: {fields[4]} (0x{fields[4]:02x})")
    print()
    
    print("If clock_seq is 16-bit (as field names suggest):")
    print(f"  Expected: (0x{fields[3]:02x} << 8) | 0x{fields[4]:02x} = {(fields[3] << 8) | fields[4]}")
    print()
    
    print("But UUID.clock_seq property returns:")
    print(f"  Actual: {u.clock_seq}")
    print()
    
    print("This happens because clock_seq property assumes RFC 4122 format")
    print("and masks with 0x3f, removing the upper 2 bits:")
    print(f"  (0x{fields[3]:02x} & 0x3f) << 8 | 0x{fields[4]:02x} = {((fields[3] & 0x3f) << 8) | fields[4]}")
    print()
    
    # Show this affects non-RFC 4122 UUIDs
    print("AFFECTED VARIANTS:")
    print("-" * 30)
    
    test_variants = [
        (0x00, "NCS (pattern 0xx)"),
        (0x40, "NCS (pattern 0xx)"),
        (0x7F, "NCS (pattern 0xx)"),
        (0x80, "RFC 4122 (pattern 10x)"),
        (0xBF, "RFC 4122 (pattern 10x)"),
        (0xC0, "Microsoft (pattern 110)"),
        (0xDF, "Microsoft (pattern 110)"),
        (0xE0, "Future (pattern 111)"),
        (0xFF, "Future (pattern 111)"),
    ]
    
    for hi_byte, variant_name in test_variants:
        test_u = uuid.UUID(fields=(0, 0, 0, hi_byte, 0xFF, 0))
        expected_full = (hi_byte << 8) | 0xFF
        actual = test_u.clock_seq
        
        print(f"  {variant_name:20} -> Expected: {expected_full:5}, Actual: {actual:5}")
    
    return u


def show_specification_details():
    """Show that for RFC 4122 UUIDs, the behavior is correct."""
    
    print("\nRFC 4122 SPECIFICATION:")
    print("=" * 50)
    print("For RFC 4122 UUIDs, clock_seq is indeed 14-bit:")
    print("  - Bits 0-5 of clock_seq_hi_variant: high 6 bits of clock_seq")
    print("  - Bits 6-7 of clock_seq_hi_variant: variant (always 10 for RFC 4122)")
    print("  - All 8 bits of clock_seq_low: low 8 bits of clock_seq")
    print("  - Total: 6 + 8 = 14 bits for clock_seq")
    print()
    
    # Show uuid1 creates correct RFC 4122 UUIDs
    u1 = uuid.uuid1()
    print(f"Example uuid1(): {u1}")
    print(f"  Variant: {u1.variant}")
    print(f"  clock_seq: {u1.clock_seq} (max 14-bit value: {(1 << 14) - 1})")
    print(f"  clock_seq_hi_variant: {u1.clock_seq_hi_variant:08b} (bit 6-7 are '10')")


def show_the_real_issue():
    """The real issue: naming and documentation."""
    
    print("\nTHE REAL ISSUE:")
    print("=" * 50)
    print("The problem is not with RFC 4122 UUIDs, but with the semantic")
    print("interpretation of the 'clock_seq_hi_variant' field for non-RFC 4122 UUIDs.")
    print()
    print("For non-RFC 4122 UUIDs:")
    print("  - There is no standard definition of 'clock_seq'")
    print("  - The UUID.clock_seq property incorrectly applies RFC 4122 masking")
    print("  - This causes UUID.clock_seq to return incorrect values")
    print()
    print("This is likely a LOGIC BUG where the clock_seq property should check")
    print("the variant and only apply masking for RFC 4122 UUIDs.")


if __name__ == "__main__":
    demonstrate_bug()
    show_specification_details()
    show_the_real_issue()