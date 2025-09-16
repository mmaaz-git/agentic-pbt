import uuid
from hypothesis import given, strategies as st

# Test the specific issue with clock_seq
def test_clock_seq_inconsistency():
    # When creating a UUID from fields, clock_seq_hi_variant contains
    # both variant bits and clock_seq high bits
    
    # Test case 1: Non-RFC 4122 variant
    fields = (0, 0, 0, 0x40, 0, 0)  # variant bits = 01 (NCS)
    u = uuid.UUID(fields=fields)
    
    # The input has clock_seq_hi_variant = 0x40
    # If we compute clock_seq as (0x40 << 8) | 0 = 16384
    # But UUID.clock_seq masks with 0x3f, giving (0x40 & 0x3f) << 8 = 0
    
    print("Test 1 - NCS variant:")
    print(f"  Input clock_seq_hi_variant: {fields[3]}")
    print(f"  Expected clock_seq (no masking): {(fields[3] << 8) | fields[4]}")
    print(f"  Actual UUID.clock_seq: {u.clock_seq}")
    print(f"  UUID.variant: {u.variant}")
    
    # Test case 2: RFC 4122 variant  
    fields2 = (0, 0, 0, 0x80, 0, 0)  # variant bits = 10 (RFC 4122)
    u2 = uuid.UUID(fields=fields2)
    
    print("\nTest 2 - RFC 4122 variant:")
    print(f"  Input clock_seq_hi_variant: {fields2[3]}")
    print(f"  Expected clock_seq (no masking): {(fields2[3] << 8) | fields2[4]}")
    print(f"  Actual UUID.clock_seq: {u2.clock_seq}")
    print(f"  UUID.variant: {u2.variant}")
    
    # Test case 3: With actual clock_seq bits set
    fields3 = (0, 0, 0, 0xBF, 0xFF, 0)  # variant=10, clock_seq_hi=0x3F
    u3 = uuid.UUID(fields=fields3)
    
    print("\nTest 3 - RFC 4122 with max clock_seq:")
    print(f"  Input clock_seq_hi_variant: {fields3[3]} (0b{fields3[3]:08b})")
    print(f"  Input clock_seq_low: {fields3[4]}")
    print(f"  Expected clock_seq (14-bit): {((fields3[3] & 0x3f) << 8) | fields3[4]}")
    print(f"  Actual UUID.clock_seq: {u3.clock_seq}")
    print(f"  UUID.variant: {u3.variant}")


def test_round_trip_issue():
    """Test if there's a round-trip issue with clock_seq"""
    
    # Create UUID with specific clock_seq_hi_variant value
    original_fields = (1234, 5678, 9012, 0xBF, 0xFF, 0xAABBCCDDEEFF)
    u1 = uuid.UUID(fields=original_fields)
    
    # Get the fields back
    retrieved_fields = u1.fields
    
    print("\nRound-trip test:")
    print(f"  Original fields: {original_fields}")
    print(f"  Retrieved fields: {retrieved_fields}")
    print(f"  Fields match: {original_fields == retrieved_fields}")
    
    # Also test clock_seq property vs manual calculation
    manual_clock_seq = (original_fields[3] << 8) | original_fields[4]
    property_clock_seq = u1.clock_seq
    
    print(f"  Manual clock_seq calc: {manual_clock_seq}")
    print(f"  Property clock_seq: {property_clock_seq}")
    print(f"  Match: {manual_clock_seq == property_clock_seq}")


def test_documentation_issue():
    """The real issue might be in the documentation/naming"""
    
    print("\nDocumentation analysis:")
    print("The field is named 'clock_seq_hi_variant' suggesting it contains:")
    print("  - High bits of clock_seq")
    print("  - Variant bits")
    print("\nBut the clock_seq property assumes RFC 4122 format where:")
    print("  - Bits 6-7 are variant (not part of clock_seq)")
    print("  - Bits 0-5 are high bits of clock_seq")
    print("\nThis means clock_seq is only 14 bits, not 16 bits!")
    
    # Show that for RFC 4122 UUIDs, clock_seq is indeed 14-bit
    u = uuid.uuid4()  # Random RFC 4122 UUID
    print(f"\nRandom UUID: {u}")
    print(f"  clock_seq: {u.clock_seq}")
    print(f"  Max possible clock_seq (14-bit): {(1 << 14) - 1}")
    print(f"  clock_seq <= max: {u.clock_seq <= (1 << 14) - 1}")


if __name__ == "__main__":
    test_clock_seq_inconsistency()
    test_round_trip_issue()
    test_documentation_issue()