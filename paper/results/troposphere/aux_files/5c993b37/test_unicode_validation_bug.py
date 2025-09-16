#!/usr/bin/env python3
"""Test for Unicode validation inconsistency in troposphere"""

import sys
import unicodedata
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.acmpca import CertificateAuthority, Subject

# Test characters that Python considers alphanumeric but the regex rejects
test_chars = [
    '¹',  # Superscript 1
    '²',  # Superscript 2  
    '³',  # Superscript 3
    'α',  # Greek alpha
    'β',  # Greek beta
    'А',  # Cyrillic A (looks like Latin A)
    'В',  # Cyrillic V (looks like Latin B)
    'Ⅰ',  # Roman numeral 1
    'Ⅱ',  # Roman numeral 2
    '①',  # Circled 1
    '②',  # Circled 2
    '𝟏',  # Mathematical Bold Digit One
    '𝐀',  # Mathematical Bold Capital A
]

print("Testing Unicode characters that Python considers alphanumeric:")
print("-" * 60)

for char in test_chars:
    print(f"\nCharacter: '{char}' (U+{ord(char):04X})")
    print(f"  Unicode name: {unicodedata.name(char, 'UNKNOWN')}")
    print(f"  Unicode category: {unicodedata.category(char)}")
    print(f"  Python isalnum(): {char.isalnum()}")
    
    try:
        ca = CertificateAuthority(
            title=char,
            KeyAlgorithm='RSA_2048',
            SigningAlgorithm='SHA256WITHRSA',
            Type='ROOT',
            Subject=Subject(CommonName='test')
        )
        print(f"  Troposphere validation: ✓ ACCEPTED")
    except ValueError as e:
        if "not alphanumeric" in str(e):
            print(f"  Troposphere validation: ✗ REJECTED (claims 'not alphanumeric')")
        else:
            print(f"  Troposphere validation: ✗ REJECTED ({e})")

print("\n" + "="*60)
print("FINDING: Troposphere's error message 'not alphanumeric' is misleading.")
print("The validation actually only accepts ASCII [a-zA-Z0-9], not all")
print("alphanumeric Unicode characters that Python's isalnum() accepts.")