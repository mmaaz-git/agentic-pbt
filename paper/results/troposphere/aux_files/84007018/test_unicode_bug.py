"""
Demonstrate potential bug with Unicode digit handling in troposphere.transfer validators.
"""
import troposphere.transfer as transfer
import json


def test_unicode_digits_bypass_validation():
    """
    The double() and integer() validators accept Arabic-Indic digits (٠-٩)
    but return them as Unicode strings, not ASCII numbers.
    
    This could cause issues when the values are serialized to JSON for AWS CloudFormation.
    """
    
    # Create a PosixProfile with Arabic-Indic digits
    # PosixProfile.Uid and Gid use the double validator
    arabic_uid = "١٢٣٤"  # Arabic-Indic for 1234
    arabic_gid = "٥٦٧٨"  # Arabic-Indic for 5678
    
    # These pass validation
    validated_uid = transfer.double(arabic_uid)
    validated_gid = transfer.double(arabic_gid)
    
    print(f"Validated UID: {validated_uid!r} (type: {type(validated_uid).__name__})")
    print(f"Validated GID: {validated_gid!r} (type: {type(validated_gid).__name__})")
    
    # But when serialized to JSON, they remain as Unicode strings
    data = {
        "Uid": validated_uid,
        "Gid": validated_gid
    }
    
    json_output = json.dumps(data, ensure_ascii=True)
    print(f"\nJSON output: {json_output}")
    
    # AWS CloudFormation expects numeric values or ASCII digit strings
    # But we're sending Unicode digit strings
    
    # Similarly for integer validator
    timeout_seconds = "٩٠"  # Arabic-Indic for 90
    validated_timeout = transfer.integer(timeout_seconds)
    print(f"\nValidated timeout: {validated_timeout!r}")
    
    # This would be sent to AWS as a Unicode string, not a number
    return validated_uid, validated_gid, validated_timeout


def test_comparison_with_ascii():
    """Show the difference between ASCII and Arabic-Indic digits"""
    
    ascii_num = "123"
    arabic_num = "١٢٣"
    
    # Both pass validation
    ascii_result = transfer.double(ascii_num)
    arabic_result = transfer.double(arabic_num)
    
    print(f"ASCII input: {ascii_num!r} -> {ascii_result!r}")
    print(f"Arabic input: {arabic_num!r} -> {arabic_result!r}")
    
    # But they're not equal as strings
    print(f"Are they equal? {ascii_result == arabic_result}")
    
    # Python converts them to the same number
    print(f"float(ascii): {float(ascii_num)}")
    print(f"float(arabic): {float(arabic_num)}")
    print(f"Numeric equality: {float(ascii_num) == float(arabic_num)}")
    
    # But AWS expects ASCII digits
    print(f"\nJSON with ASCII: {json.dumps({'value': ascii_result})}")
    print(f"JSON with Arabic: {json.dumps({'value': arabic_result})}")


if __name__ == "__main__":
    print("=== Testing Unicode Digit Bug ===\n")
    
    print("Test 1: Unicode digits bypass validation")
    print("-" * 40)
    test_unicode_digits_bypass_validation()
    
    print("\n\nTest 2: Comparison with ASCII digits")
    print("-" * 40)
    test_comparison_with_ascii()
    
    print("\n\n=== Summary ===")
    print("The validators accept non-ASCII Unicode digits and return them unchanged.")
    print("This could cause issues when these values are sent to AWS CloudFormation,")
    print("which expects numeric values to be in ASCII format.")