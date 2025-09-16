# Bug Report: sphinxcontrib.qthelp Regex Pattern Fails on Newline Characters

**Target**: `sphinxcontrib.qthelp.split_index_entry`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `split_index_entry` function fails to parse index entries containing newline characters in the title portion, returning the entire string instead of splitting it into title and ID components.

## Property-Based Test

```python
@given(
    title=st.text(min_size=1).filter(lambda x: '(' not in x and ')' not in x),
    id_part=st.from_regex(r'[a-zA-Z_][a-zA-Z0-9_.]*', fullmatch=True)
)
def test_split_index_entry_valid_patterns(title, id_part):
    """Test that valid index entries are split correctly."""
    entry = f"{title} ({id_part})"
    
    result_title, result_id = split_index_entry(entry)
    
    assert result_title == title, f"Title mismatch: expected '{title}', got '{result_title}'"
    assert result_id == id_part, f"ID mismatch: expected '{id_part}', got '{result_id}'"
```

**Failing input**: `title='\n', id_part='A'`

## Reproducing the Bug

```python
from sphinxcontrib.qthelp import split_index_entry

entry = "\n (A)"
result_title, result_id = split_index_entry(entry)

print(f"Input: {repr(entry)}")
print(f"Expected: title={repr('\n')}, id={repr('A')}")
print(f"Actual: title={repr(result_title)}, id={repr(result_id)}")

assert result_title == "\n", f"Expected title '\\n', got {repr(result_title)}"
assert result_id == "A", f"Expected id 'A', got {repr(result_id)}"
```

## Why This Is A Bug

The regex pattern `(?P<title>.+) \(((class in )?(?P<id>[\w\.]+)( (?P<descr>\w+))?\))$` uses `.+` which matches any character except newlines. When the title contains a newline, the pattern fails to match, causing the function to return the entire string unsplit instead of properly extracting the title and ID. This violates the function's contract to split entries in the format "title (id)".

## Fix

```diff
--- a/sphinxcontrib/qthelp/__init__.py
+++ b/sphinxcontrib/qthelp/__init__.py
@@ -33,7 +33,7 @@
 __ = get_translation(__name__, 'console')
 
 _idpattern = re.compile(
-    r'(?P<title>.+) \(((class in )?(?P<id>[\w\.]+)( (?P<descr>\w+))?\))$')
+    r'(?P<title>.+) \(((class in )?(?P<id>[\w\.]+)( (?P<descr>\w+))?\))$', re.DOTALL)
 
 section_template = '<section title="%(title)s" ref="%(ref)s"/>'
```