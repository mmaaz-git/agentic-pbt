# Bug Report: spacy_wordnet Duplicate SSID Overwrite in load_wordnet_domains

**Target**: `spacy_wordnet.wordnet_domains.load_wordnet_domains`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `load_wordnet_domains()` function overwrites domains for duplicate SSIDs instead of merging them, causing data loss when the same synset ID appears multiple times in the input file.

## Property-Based Test

```python
@given(
    st.lists(
        st.tuples(
            st.from_regex(r'[0-9]{8}-[nvra]', fullmatch=True),  # ssid format
            st.lists(st.from_regex(r'[a-z_]+', fullmatch=True), min_size=1)  # domain names
        ),
        min_size=0,
        max_size=100
    )
)
def test_load_wordnet_domains_parsing(domain_data):
    """Test that load_wordnet_domains correctly parses the expected file format"""
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        for ssid, domains in domain_data:
            f.write(f"{ssid}\t{' '.join(domains)}\n")
        temp_path = f.name
    
    try:
        import spacy_wordnet.wordnet_domains as wd
        wd.__WN_DOMAINS_BY_SSID.clear()
        
        load_wordnet_domains(temp_path)
        
        for ssid, expected_domains in domain_data:
            loaded_domains = wd.__WN_DOMAINS_BY_SSID.get(ssid, [])
            assert loaded_domains == expected_domains
    finally:
        os.unlink(temp_path)
```

**Failing input**: `domain_data=[('00000000-a', ['_']), ('00000000-a', ['__'])]`

## Reproducing the Bug

```python
import tempfile
import os
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/spacy-wordnet_env/lib/python3.13/site-packages')
import spacy_wordnet.wordnet_domains as wd

# Create a file with duplicate SSIDs
with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
    f.write("12345678-n\tdomainA domainB\n")
    f.write("12345678-n\tdomainC\n")  # Same SSID
    f.write("12345678-n\tdomainD domainE\n")  # Same SSID again
    temp_path = f.name

# Load the domains
wd.__WN_DOMAINS_BY_SSID.clear()
wd.load_wordnet_domains(temp_path)

# Check result
result = wd.__WN_DOMAINS_BY_SSID.get("12345678-n", [])
print(f"Loaded domains: {result}")
print(f"Expected: ['domainA', 'domainB', 'domainC', 'domainD', 'domainE']")
print(f"Actual: {result}")

os.unlink(temp_path)
```

## Why This Is A Bug

The function uses direct assignment (`__WN_DOMAINS_BY_SSID[ssid] = domains.split(" ")`) which overwrites any existing domains for that SSID. If the wordnet_domains.txt file contains duplicate SSIDs (either intentionally for organization or accidentally), only the last occurrence's domains are retained, causing silent data loss.

## Fix

```diff
--- a/spacy_wordnet/wordnet_domains.py
+++ b/spacy_wordnet/wordnet_domains.py
@@ -20,7 +20,7 @@ def load_wordnet_domains(path: Optional[str] = wordnet_domains_path()):
 
     for line in open(path, "r"):
         ssid, domains = line.strip().split("\t")
-        __WN_DOMAINS_BY_SSID[ssid] = domains.split(" ")
+        __WN_DOMAINS_BY_SSID[ssid].extend(domains.split(" "))
```