# Bug Report: jurigged.codetools Unicode Handling Bug in Info.get_segment

**Target**: `jurigged.codetools.Info.get_segment`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `Info.get_segment` method crashes with a UnicodeDecodeError when extracting segments from lines containing multi-byte UTF-8 characters at certain column positions.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
from jurigged.codetools import Info, Extent, use_info

@given(
    st.lists(st.text(min_size=1), min_size=5, max_size=20),
    st.integers(min_value=0, max_value=4),
    st.integers(min_value=0, max_value=10),
    st.integers(min_value=0, max_value=10)
)
def test_info_get_segment_single_line(lines, line_idx, start_col, length):
    assume(line_idx < len(lines))
    assume(start_col <= len(lines[line_idx]))
    
    end_col = min(start_col + length, len(lines[line_idx]))
    
    info = Info(
        filename="test.py",
        module_name="test",
        source="\n".join(lines),
        lines=lines
    )
    
    with use_info(
        filename="test.py",
        module_name="test",
        source="\n".join(lines),
        lines=lines
    ):
        ext = Extent(
            lineno=line_idx + 1,
            col_offset=start_col,
            end_lineno=line_idx + 1,
            end_col_offset=end_col
        )
        
        result = info.get_segment(ext)
        expected = lines[line_idx].encode()[start_col:end_col].decode()
        assert result == expected
```

**Failing input**: `lines=['0', '\x80', '0', '0', '0'], line_idx=1, start_col=0, length=1`

## Reproducing the Bug

```python
from jurigged.codetools import Info, Extent, use_info

lines = ['def hello():', '    print("Hello 🦄 World")', '    return True']
info = Info(
    filename="test.py",
    module_name="test",
    source="\n".join(lines),
    lines=lines
)

with use_info(
    filename="test.py",
    module_name="test",
    source="\n".join(lines),
    lines=lines
):
    ext = Extent(
        lineno=2,
        col_offset=18,
        end_lineno=2,
        end_col_offset=20
    )
    
    result = info.get_segment(ext)
```

## Why This Is A Bug

The `get_segment` method incorrectly treats column offsets as byte positions rather than character positions. When extracting segments from single lines, it encodes the string to bytes, slices at the provided column offsets, and then decodes. This fails when the slice boundaries fall in the middle of a multi-byte UTF-8 character, causing a UnicodeDecodeError. This affects any Python code containing emojis, accented characters, or other non-ASCII Unicode characters.

## Fix

```diff
--- a/jurigged/codetools.py
+++ b/jurigged/codetools.py
@@ -99,10 +99,10 @@ class Info:
 
         lines = self.lines
         if end_lineno == lineno:
-            return lines[lineno].encode()[col_offset:end_col_offset].decode()
+            return lines[lineno][col_offset:end_col_offset]
 
-        first = lines[lineno].encode()[col_offset:].decode()
-        last = lines[end_lineno].encode()[:end_col_offset].decode()
+        first = lines[lineno][col_offset:]
+        last = lines[end_lineno][:end_col_offset]
         lines = lines[lineno + 1 : end_lineno]
 
         lines.insert(0, first)
```