"""Minimal reproduction of title validation bug in troposphere"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.codepipeline as cp

# The character 'µ' (micro sign, U+00B5) is a Unicode letter
# Python's str.isalnum() returns True for it
test_char = 'µ'
print(f"Is '{test_char}' alphanumeric according to Python? {test_char.isalnum()}")

# But troposphere rejects it as "not alphanumeric"
try:
    artifact = cp.ArtifactDetails(
        title=test_char,
        MaximumCount=1,
        MinimumCount=0
    )
    print(f"SUCCESS: Created ArtifactDetails with title '{test_char}'")
except ValueError as e:
    print(f"FAILURE: {e}")
    
# Other Unicode letters that Python considers alphanumeric but troposphere rejects:
unicode_alphanumeric_chars = ['µ', 'π', 'Ω', 'α', 'β', '²', '³', 'ñ', 'é', 'ü', 'ß']

print("\nTesting various Unicode alphanumeric characters:")
for char in unicode_alphanumeric_chars:
    print(f"  '{char}': Python says isalnum()={char.isalnum()}", end=" | ")
    try:
        cp.ArtifactDetails(title=char, MaximumCount=1, MinimumCount=0)
        print("troposphere: ACCEPTED")
    except ValueError:
        print("troposphere: REJECTED")