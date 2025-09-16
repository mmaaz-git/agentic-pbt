# Bug Report: dparse.regex Incorrectly Matches Pipe Separator in Hash Specifications

**Target**: `dparse.regex.HASH_REGEX` and `dparse.parser.Parser.parse_hashes`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The regex pattern `HASH_REGEX = r"--hash[=| ]\w+:\w+"` incorrectly matches pipe `|` as a separator between `--hash` and the algorithm name, which is not a valid format according to pip's specification.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from dparse.regex import HASH_REGEX
import re

@given(
    algo=st.sampled_from(['sha256', 'sha384', 'sha512']),
    hash_value=st.text(alphabet='0123456789abcdef', min_size=32, max_size=64),
    separator=st.sampled_from(['=', ' ', '|'])
)
def test_hash_regex_separator_validity(algo, hash_value, separator):
    """Test that HASH_REGEX only matches valid pip hash formats."""
    hash_string = f"--hash{separator}{algo}:{hash_value}"
    match = re.search(HASH_REGEX, hash_string)
    
    # Only '=' and ' ' should be valid separators, not '|'
    if separator in ['=', ' ']:
        assert match is not None
    elif separator == '|':
        assert match is None  # This assertion FAILS - bug!
```

**Failing input**: `separator='|', algo='sha256', hash_value='abc123'`

## Reproducing the Bug

```python
import re
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from dparse.regex import HASH_REGEX
from dparse.parser import Parser

# Test 1: Regex incorrectly matches pipe separator
invalid_hash = "--hash|sha256:abc123"
match = re.search(HASH_REGEX, invalid_hash)
print(f"Testing: {invalid_hash}")
print(f"Match found: {match is not None}")  # True (incorrect!)
print(f"Matched text: {match.group() if match else 'None'}")

# Test 2: Parser extracts invalid hash format
line = "package==1.0.0 --hash|sha256:abcdef123456"
cleaned, hashes = Parser.parse_hashes(line)
print(f"\nOriginal line: {line}")
print(f"Cleaned line: {cleaned}")
print(f"Extracted hashes: {hashes}")  # Incorrectly extracts ['--hash|sha256:abcdef123456']
```

## Why This Is A Bug

The character class `[=| ]` in the regex pattern matches any of three characters: `=`, `|`, or space. However, pip only uses two valid formats for hash specifications:
- `--hash=algorithm:hash_value` (with equals sign)
- `--hash algorithm:hash_value` (with space)

The pipe character `|` is never used as a separator in pip's hash format. This appears to be a typo where the author intended to write `[= ]` (matching equals or space) but accidentally included the pipe character, possibly confusing regex alternation syntax `(?:=| )` with character class syntax `[=| ]`.

## Fix

```diff
--- a/dparse/regex.py
+++ b/dparse/regex.py
@@ -1 +1 @@
-HASH_REGEX = r"--hash[=| ]\w+:\w+"
+HASH_REGEX = r"--hash[= ]\w+:\w+"
```