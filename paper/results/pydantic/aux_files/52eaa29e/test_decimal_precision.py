from decimal import Decimal
import pydantic.v1


def test_decimal_trailing_zeros_lost():
    """Demonstrate that Decimal trailing zeros are lost in JSON round-trip"""
    
    class DecimalModel(pydantic.v1.BaseModel):
        value: Decimal
    
    # Test case 1: Trailing zeros after decimal point
    original = DecimalModel(value=Decimal('1.00'))
    json_str = original.json()
    reconstructed = DecimalModel.parse_raw(json_str)
    
    print(f"Original value: {original.value}")
    print(f"Original str:   '{str(original.value)}'")
    print(f"JSON:           {json_str}")
    print(f"Reconstructed:  {reconstructed.value}")
    print(f"Reconst. str:   '{str(reconstructed.value)}'")
    print()
    
    # The values are equal as Decimals
    assert original.value == reconstructed.value
    
    # But their string representations differ (trailing zeros lost)
    assert str(original.value) == '1.00'
    assert str(reconstructed.value) == '1.0'
    assert str(original.value) != str(reconstructed.value)
    
    # Test case 2: Scientific notation precision
    original2 = DecimalModel(value=Decimal('1.2300E+2'))
    json_str2 = original2.json()
    reconstructed2 = DecimalModel.parse_raw(json_str2)
    
    print(f"Original value: {original2.value}")
    print(f"Original str:   '{str(original2.value)}'")
    print(f"JSON:           {json_str2}")
    print(f"Reconstructed:  {reconstructed2.value}")
    print(f"Reconst. str:   '{str(reconstructed2.value)}'")
    
    # Values equal, strings different
    assert original2.value == reconstructed2.value
    assert str(original2.value) != str(reconstructed2.value)


if __name__ == "__main__":
    test_decimal_trailing_zeros_lost()
    print("\nTrailing zeros in Decimals are not preserved through JSON serialization!")