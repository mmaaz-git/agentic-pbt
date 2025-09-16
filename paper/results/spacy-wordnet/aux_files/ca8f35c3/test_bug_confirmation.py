#!/usr/bin/env python3
import sys
import os
import tempfile

# Add the spacy_wordnet module to path
sys.path.insert(0, '/root/hypothesis-llm/envs/spacy-wordnet_env/lib/python3.13/site-packages')

# Test 1: Reproduce fetch_wordnet_lang issue with newline
print("Test 1: fetch_wordnet_lang with newline character")
from spacy_wordnet.__utils__ import fetch_wordnet_lang

try:
    result = fetch_wordnet_lang("\n")
    print(f"ERROR: Should have raised exception, got: {result}")
except Exception as e:
    error_msg = str(e)
    print(f"Exception message: {repr(error_msg)}")
    # Check if the regex pattern "Language .* not supported" would match
    import re
    pattern = r"Language .* not supported"
    if re.search(pattern, error_msg):
        print("Regex MATCHES - No bug")
    else:
        print("Regex DOES NOT MATCH - BUG CONFIRMED")
        print(f"The pattern '{pattern}' doesn't match '{error_msg}'")
        print("This is because . doesn't match newline by default in regex")

print("\n" + "="*50 + "\n")

# Test 2: Reproduce load_wordnet_domains duplicate ssid issue
print("Test 2: load_wordnet_domains with duplicate ssids")

# Create a test file with duplicate ssids
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
    f.write("12345678-n\tdomain1\n")
    f.write("12345678-n\tdomain2\n")  # Same ssid, different domain
    temp_path = f.name

print(f"Created test file with duplicate ssids: {temp_path}")

# Load it
import spacy_wordnet.wordnet_domains as wd

# Clear the global dictionary first
wd.__WN_DOMAINS_BY_SSID.clear()

# Load the domains
wd.load_wordnet_domains(temp_path)

# Check what was loaded
result = wd.__WN_DOMAINS_BY_SSID.get("12345678-n", [])
print(f"Loaded domains for ssid '12345678-n': {result}")

if result == ["domain1"]:
    print("BUG CONFIRMED: Second entry overwrote the first (only 'domain1' remains)")
elif result == ["domain2"]:
    print("BUG CONFIRMED: Second entry overwrote the first (only 'domain2' remains)")
elif set(result) == {"domain1", "domain2"}:
    print("No bug: Both domains were preserved")
else:
    print(f"Unexpected result: {result}")

# Clean up
os.unlink(temp_path)

print("\n" + "="*50 + "\n")

# Test 3: More comprehensive test of duplicate ssid handling
print("Test 3: Multiple duplicates test")

with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
    f.write("00000001-n\tdomainA domainB\n")  # Multiple domains on one line
    f.write("00000001-n\tdomainC\n")         # Same ssid, different domain
    f.write("00000002-v\tdomainX\n")         # Different ssid
    f.write("00000001-n\tdomainD domainE\n") # Same ssid again with multiple domains
    temp_path = f.name

# Clear and reload
wd.__WN_DOMAINS_BY_SSID.clear()
wd.load_wordnet_domains(temp_path)

result1 = wd.__WN_DOMAINS_BY_SSID.get("00000001-n", [])
result2 = wd.__WN_DOMAINS_BY_SSID.get("00000002-v", [])

print(f"Domains for '00000001-n': {result1}")
print(f"Domains for '00000002-v': {result2}")

# Expected behavior is unclear from the code - does it merge or overwrite?
# The code in line 23 does: __WN_DOMAINS_BY_SSID[ssid] = domains.split(" ")
# This uses assignment (=), not append or extend, so it OVERWRITES!

if result1 == ["domainD", "domainE"]:
    print("BUG CONFIRMED: Last entry overwrites all previous entries for same ssid")
    print("Expected all domains: ['domainA', 'domainB', 'domainC', 'domainD', 'domainE']")
    print("Got only last entry: ['domainD', 'domainE']")

os.unlink(temp_path)