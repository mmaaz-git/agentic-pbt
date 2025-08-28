# Bug Report: packaging.metadata Inconsistent Whitespace Handling

**Target**: `packaging.metadata.parse_email`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `parse_email` function preserves trailing whitespace in field values instead of trimming it, leading to inconsistent behavior and potential comparison issues.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import packaging.metadata

@given(st.sampled_from(["Name", "Version", "Summary", "Author"]),
       st.text(min_size=1, max_size=100).filter(lambda x: '\n' not in x and '\r' not in x))
def test_whitespace_handling(field_name, value):
    values_to_test = [
        value,
        f" {value}",
        f"{value} ",
        f"  {value}  ",
        f"\t{value}\t"
    ]
    
    results = []
    for test_value in values_to_test:
        metadata_str = f"Metadata-Version: 2.1\nName: test\nVersion: 1.0.0\n{field_name}: {test_value}"
        raw_metadata, _ = packaging.metadata.parse_email(metadata_str)
        
        field_key = field_name.lower().replace('-', '_')
        if field_key in raw_metadata:
            results.append(raw_metadata[field_key])
    
    assert all(r == results[0] for r in results), f"Inconsistent whitespace handling: {results}"
```

**Failing input**: Field "Summary" with values like "test", "test ", "  test  " produce different results

## Reproducing the Bug

```python
import packaging.metadata

test_cases = [
    'Summary: test',
    'Summary: test ',
    'Summary:  test  ',
    'Summary: test\t'
]

for case in test_cases:
    metadata_str = f'Metadata-Version: 2.1\nName: pkg\nVersion: 1.0.0\n{case}'
    raw_metadata, _ = packaging.metadata.parse_email(metadata_str)
    summary = raw_metadata.get('summary', 'NONE')
    print(f'Input: {repr(case):30} -> Summary: {repr(summary)}')
```

Output:
```
Input: 'Summary: test'                -> Summary: 'test'
Input: 'Summary: test '               -> Summary: 'test '
Input: 'Summary:  test  '             -> Summary: 'test  '
Input: 'Summary: test\t'              -> Summary: 'test\t'
```

## Why This Is A Bug

Metadata field values should have consistent whitespace handling. The current behavior preserves trailing whitespace, which can lead to:
- Unexpected comparison failures (e.g., "test" != "test ")
- Data inconsistency when the same logical value has different representations
- Issues when metadata is serialized/deserialized through different systems

Most metadata parsers trim whitespace from field values for consistency.

## Fix

```diff
# In the parse_email function or field value processing:
- field_value = raw_value  # Current behavior
+ field_value = raw_value.strip()  # Trim leading/trailing whitespace
```

The fix should strip leading and trailing whitespace from all field values during parsing to ensure consistent behavior.