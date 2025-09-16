# Bug Report: yq decode_docs Function Skips Characters Between JSON Documents

**Target**: `yq.decode_docs`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `decode_docs` function in yq incorrectly advances the parsing position by `pos + 1` instead of `pos`, causing it to skip a character between JSON documents and potentially miss valid JSON when documents are back-to-back.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import json
from yq import decode_docs

@given(
    st.lists(
        st.dictionaries(
            st.text(min_size=1, max_size=5),
            st.integers()
        ),
        min_size=2,
        max_size=5
    )
)
def test_decode_docs_back_to_back(docs):
    # Create back-to-back JSON without separators
    jq_output = "".join(json.dumps(doc) for doc in docs)
    
    decoder = json.JSONDecoder()
    decoded = list(decode_docs(jq_output, decoder))
    
    # This will fail - decode_docs skips characters
    assert len(decoded) == len(docs)
```

**Failing input**: `[{"a": 1}, {"b": 2}]` produces input string `{"a":1}{"b":2}`

## Reproducing the Bug

```python
import json

def decode_docs(jq_output, json_decoder):
    while jq_output:
        doc, pos = json_decoder.raw_decode(jq_output)
        jq_output = jq_output[pos + 1 :]  # BUG HERE
        yield doc

decoder = json.JSONDecoder()
jq_output = '{"a":1}{"b":2}'

result = list(decode_docs(jq_output, decoder))
print(f"Input: {jq_output}")
print(f"Expected: [{'a': 1}, {'b': 2}]")
print(f"Actual: {result}")

# First document parses correctly
# raw_decode('{"a":1}{"b":2}') returns ({'a': 1}, 6)
# Then jq_output[7:] = '"b":2}' - skipped the '{'!
# Parsing '"b":2}' fails with JSONDecodeError
```

## Why This Is A Bug

The function assumes documents are separated by at least one character (newline or space), but jq can output back-to-back JSON documents. When `raw_decode` returns position `pos` (the index of the last character consumed), slicing from `pos + 1` skips the next character. If that character is the start of the next JSON document (like `{`), the function will fail to parse it correctly.

## Fix

```diff
--- a/yq/__init__.py
+++ b/yq/__init__.py
@@ -38,7 +38,10 @@
 def decode_docs(jq_output, json_decoder):
     while jq_output:
         doc, pos = json_decoder.raw_decode(jq_output)
-        jq_output = jq_output[pos + 1 :]
+        # Skip whitespace after the document
+        while pos < len(jq_output) and jq_output[pos] in ' \t\n\r':
+            pos += 1
+        jq_output = jq_output[pos:]
         yield doc
```