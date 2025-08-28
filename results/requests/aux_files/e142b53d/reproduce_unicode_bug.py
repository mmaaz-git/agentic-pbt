"""Reproduce CaseInsensitiveDict Unicode case-folding bug."""

from requests.structures import CaseInsensitiveDict

# Test the German sharp s character
print("Testing German sharp s (ß):")
cid = CaseInsensitiveDict()
cid['ß'] = 'value1'

print(f"cid['ß'] = {cid.get('ß')}")        # Works: 'value1'
print(f"cid['ss'] = {cid.get('ss')}")      # Returns: None (expected 'value1')
print(f"cid['SS'] = {cid.get('SS')}")      # Returns: None (expected 'value1') 
print(f"'ß'.upper() = {'ß'.upper()}")      # Returns: 'SS'
print(f"'ß'.lower() = {'ß'.lower()}")      # Returns: 'ß'

print("\nUnderlying issue:")
print(f"'ß'.lower() == 'SS'.lower(): {'ß'.lower() == 'SS'.lower()}")  # False!

print("\nMore Unicode case-folding issues:")
# Turkish I problem
cid2 = CaseInsensitiveDict()
cid2['İ'] = 'turkish_i'  # Turkish capital I with dot
print(f"cid2['İ'] = {cid2.get('İ')}")      # Works
print(f"cid2['i'] = {cid2.get('i')}")      # Returns: None (might be expected depending on locale)

# The issue is that CaseInsensitiveDict uses .lower() for case-insensitive comparison,
# but Unicode case folding is more complex than simple .lower()

print("\nRoot cause:")
print("CaseInsensitiveDict stores keys using key.lower() as the internal key")
print("But Unicode case relationships are not always bidirectional:")
print(f"  'ß'.lower() = {'ß'.lower()}")
print(f"  'SS'.lower() = {'SS'.lower()}")
print(f"  'ß'.upper() = {'ß'.upper()}")
print("So 'ß' and 'SS' don't map to the same internal key even though 'ß'.upper() == 'SS'")