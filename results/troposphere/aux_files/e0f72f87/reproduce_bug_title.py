#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.pinpointemail as pe

# Test various characters that are alphanumeric in Unicode but rejected
test_titles = [
    'µ',  # Greek letter mu
    'π',  # Greek letter pi
    'α',  # Greek letter alpha  
    'Ω',  # Greek letter Omega
    '测试',  # Chinese characters
    'тест',  # Cyrillic characters
    'café',  # Accented Latin characters (the é)
]

print("Testing title validation with Unicode alphanumeric characters:")
print("=" * 60)

for title in test_titles:
    print(f"\nTitle: '{title}'")
    print(f"  Python isalnum(): {title.isalnum()}")
    
    try:
        obj = pe.ConfigurationSet(title=title, Name="TestConfig")
        print(f"  Result: Accepted (no error)")
    except ValueError as e:
        print(f"  Result: Rejected - {e}")
        if title.isalnum():
            print(f"  BUG: This is alphanumeric according to Python but rejected!")

print("\n" + "=" * 60)
print("Issue: The regex ^[a-zA-Z0-9]+$ only accepts ASCII letters and digits,")
print("but many valid Unicode letters are alphanumeric and should be accepted.")
print("This is inconsistent with Python's definition of alphanumeric.")