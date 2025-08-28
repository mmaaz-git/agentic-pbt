import urllib.robotparser

print("BUG 1: Double URL encoding in RuleLine")
print("="*50)
# When RuleLine is created with an already-encoded path,
# it encodes it again, leading to double-encoding
rule1 = urllib.robotparser.RuleLine('/test:', True)
print(f"Original path '/test:' becomes: {rule1.path}")

# If we create another RuleLine with the encoded path, it double-encodes
rule2 = urllib.robotparser.RuleLine(rule1.path, True)
print(f"Re-using encoded path '{rule1.path}' becomes: {rule2.path}")
print(f"These should be equal but aren't: {rule1.path} != {rule2.path}")

print("\nWhy this matters:")
print("If robots.txt rules are programmatically generated or processed")
print("multiple times, paths containing special characters will be")
print("incorrectly double-encoded, breaking path matching.")

print("\n" + "="*50)
print("\nBUG 2: Case-insensitive matching fails with Unicode edge cases")
print("="*50)

# The micro sign (µ) uppercases to Greek capital Mu (Μ)
# But the matching logic fails to handle this properly
entry = urllib.robotparser.Entry()
entry.useragents.append('µbot')  # lowercase micro sign

print(f"User-agent: µbot")
print(f"Testing with 'µbot': {entry.applies_to('µbot')}")  # True
print(f"Testing with 'ΜBOT': {entry.applies_to('ΜBOT')}")  # False (should be True!)
print(f"'µ'.upper() = '{chr(181).upper()}' (Greek Mu)")
print(f"'µ'.lower() = '{chr(181).lower()}'")

print("\nWhy this matters:")
print("The RFC states user-agent matching should be case-insensitive,")
print("but this fails for certain Unicode characters where upper/lower")
print("transformations cross character boundaries.")

print("\n" + "="*50)
print("\nBUG 3: Empty user-agent name causes incorrect matching")
print("="*50)

# User-agent with just "/" causes empty string after split
entry = urllib.robotparser.Entry()
entry.useragents.append('/')

print(f"User-agent: /")
print(f"After split('/')[0]: ''")
print(f"Testing 'SomeBot/1.0': {entry.applies_to('SomeBot/1.0')}")  # False
print(f"Testing '/1.0': {entry.applies_to('/1.0')}")  # False (probably should be True)

print("\nWhy this matters:")
print("A robots.txt with 'User-agent: /' won't match anything properly")
print("because split('/')[0] returns empty string.")