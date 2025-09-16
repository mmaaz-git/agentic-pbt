"""Focused test to reproduce the Unicode title validation bug."""

from troposphere.billingconductor import BillingGroup, AccountGrouping, ComputationPreference
import unicodedata

# Test specific Unicode letters that are valid letters but fail validation
test_cases = [
    'ª',  # FEMININE ORDINAL INDICATOR (Ll - lowercase letter)  
    'º',  # MASCULINE ORDINAL INDICATOR (Ll - lowercase letter)
    'À',  # LATIN CAPITAL LETTER A WITH GRAVE (Lu - uppercase letter)
    'É',  # LATIN CAPITAL LETTER E WITH ACUTE (Lu - uppercase letter)
    'ñ',  # LATIN SMALL LETTER N WITH TILDE (Ll - lowercase letter)
    'Ω',  # GREEK CAPITAL LETTER OMEGA (Lu - uppercase letter)
]

print("Testing Unicode letter characters that should be valid letters:")
print("=" * 60)

for char in test_cases:
    # Show that Python considers these as letters
    category = unicodedata.category(char)
    is_letter = category.startswith('L')
    
    print(f"\nCharacter: '{char}'")
    print(f"  Unicode name: {unicodedata.name(char, 'UNKNOWN')}")
    print(f"  Unicode category: {category}")
    print(f"  Is letter (category starts with 'L'): {is_letter}")
    print(f"  char.isalpha(): {char.isalpha()}")
    print(f"  char.isalnum(): {char.isalnum()}")
    
    # Try to create a BillingGroup with this character as title
    try:
        account_grouping = AccountGrouping(LinkedAccountIds=["123456789012"])
        computation_pref = ComputationPreference(PricingPlanArn="arn:aws:pricing::123456789012:plan/test")
        
        billing_group = BillingGroup(
            char,  # Using Unicode character as title
            Name="TestBillingGroup",
            PrimaryAccountId="123456789012",
            AccountGrouping=account_grouping,
            ComputationPreference=computation_pref
        )
        print(f"  ✅ SUCCESS: BillingGroup created with title '{char}'")
    except ValueError as e:
        print(f"  ❌ FAILED: {e}")

print("\n" + "=" * 60)
print("Analysis:")
print("-" * 60)
print("The troposphere library's title validation uses regex: ^[a-zA-Z0-9]+$")
print("This regex only accepts ASCII letters and digits.")
print("However, Python's str.isalnum() and Unicode category 'L' includes")
print("many more valid letter characters from various languages.")
print("\nThis creates an inconsistency where valid Unicode letters are rejected.")