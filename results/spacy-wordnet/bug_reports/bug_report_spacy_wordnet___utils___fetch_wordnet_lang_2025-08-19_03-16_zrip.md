# Bug Report: spacy_wordnet.__utils__.fetch_wordnet_lang Improper Error Message Formatting

**Target**: `spacy_wordnet.__utils__.fetch_wordnet_lang`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `fetch_wordnet_lang` function includes unsanitized user input directly in error messages, causing malformed error messages when the input contains special characters like newlines, tabs, or carriage returns.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from spacy_wordnet.__utils__ import fetch_wordnet_lang
import pytest

@given(st.text(min_size=1, max_size=5))
def test_fetch_wordnet_lang_unsupported(lang_code):
    """Test that fetch_wordnet_lang raises exception for unsupported languages"""
    supported = ["es", "en", "fr", "it", "pt", "de", "sq", "ar", "bg", "ca", 
                 "zh", "da", "el", "eu", "fa", "fi", "he", "hr", "id", "ja", 
                 "nl", "pl", "sl", "sv", "th", "ml"]
    
    if lang_code not in supported:
        with pytest.raises(Exception, match="Language .* not supported"):
            fetch_wordnet_lang(lang_code)
```

**Failing input**: `'\n'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/spacy-wordnet_env/lib/python3.13/site-packages')

from spacy_wordnet.__utils__ import fetch_wordnet_lang

try:
    result = fetch_wordnet_lang("\n")
except Exception as e:
    print(f"Error message: {repr(str(e))}")
```

## Why This Is A Bug

Error messages should properly escape or sanitize user input to ensure they are readable and don't contain control characters. The current implementation directly formats unsanitized input into the error message, resulting in malformed messages that include literal newlines, tabs, and other control characters. This violates the principle that error messages should be clean, readable, and safe for logging systems.

## Fix

```diff
--- a/spacy_wordnet/__utils__.py
+++ b/spacy_wordnet/__utils__.py
@@ -73,7 +73,7 @@ def fetch_wordnet_lang(lang: Optional[str] = None) -> str:
     language = __WN_LANGUAGES_MAPPING.get(lang, None)
 
     if not language:
-        raise Exception("Language {} not supported".format(lang))
+        raise Exception("Language {} not supported".format(repr(lang)))
 
     return language
```