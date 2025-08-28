# Bug Report: spacy_wordnet.wordnet_domains Crashes on Malformed Input Files

**Target**: `spacy_wordnet.wordnet_domains.load_wordnet_domains`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `load_wordnet_domains()` function crashes with a `ValueError` when the input file contains empty lines or lines without tab separators, making it vulnerable to file corruption or malformed custom data files.

## Property-Based Test

```python
@given(
    st.lists(
        st.tuples(
            st.text(alphabet='0123456789', min_size=8, max_size=8),
            st.sampled_from(['n', 'v', 'a', 'r']),
            st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3)
        ),
        min_size=0,
        max_size=10
    )
)
def test_load_wordnet_domains_parsing(domain_data):
    wd.__WN_DOMAINS_BY_SSID.clear()
    
    lines = []
    expected = {}
    for offset, pos, domains in domain_data:
        ssid = f"{offset}-{pos}"
        domain_str = " ".join(domains)
        lines.append(f"{ssid}\t{domain_str}")
        expected[ssid] = domains
    
    mock_content = "\n".join(lines)
    
    with patch('builtins.open', return_value=mock_content.split('\n')):
        wd.load_wordnet_domains()
        
        assert dict(wd.__WN_DOMAINS_BY_SSID) == expected
```

**Failing input**: Empty list `[]` which creates a file with just an empty line

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/spacy-wordnet_env/lib/python3.13/site-packages')

import spacy_wordnet.wordnet_domains as wd
from unittest.mock import mock_open, patch

wd.__WN_DOMAINS_BY_SSID.clear()

test_file_with_empty_line = """12345678-n\tdomain1 domain2

87654321-v\tdomain3"""

with patch('builtins.open', mock_open(read_data=test_file_with_empty_line)):
    wd.load_wordnet_domains()
```

## Why This Is A Bug

The function assumes every line in the file will have exactly one tab character separating the SSID from the domains. This assumption fails when:
1. The file contains empty lines (common in text files)
2. The file contains corrupted lines without tab separators
3. Users provide custom domain files with different formatting

The function should be robust to handle these edge cases gracefully rather than crashing.

## Fix

```diff
--- a/spacy_wordnet/wordnet_domains.py
+++ b/spacy_wordnet/wordnet_domains.py
@@ -19,6 +19,9 @@ def load_wordnet_domains(path: Optional[str] = wordnet_domains_path()):
         return
 
     for line in open(path, "r"):
+        line = line.strip()
+        if not line or '\t' not in line:
+            continue
         ssid, domains = line.strip().split("\t")
         __WN_DOMAINS_BY_SSID[ssid] = domains.split(" ")
```