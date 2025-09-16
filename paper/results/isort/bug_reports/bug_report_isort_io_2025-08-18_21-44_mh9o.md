# Bug Report: isort.io Null Character in Filename Crash

**Target**: `isort.io.File.from_contents`
**Severity**: Low
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `File.from_contents` method crashes with a `ValueError` when given a filename containing null characters, instead of handling the invalid input gracefully.

## Property-Based Test

```python
@given(
    content=st.text(min_size=0, max_size=1000),
    filename=st.text(min_size=1, max_size=100).filter(lambda x: '/' not in x and '\\' not in x and x.strip())
)
def test_from_contents_preserves_content(content, filename):
    assume('\x00' not in content)
    
    file_obj = File.from_contents(content, filename)
    
    file_obj.stream.seek(0)
    read_content = file_obj.stream.read()
    
    assert read_content == content
    assert file_obj.path == Path(filename).resolve()
    assert file_obj.encoding is not None
```

**Failing input**: `content='', filename='\x00'`

## Reproducing the Bug

```python
from isort.io import File

filename_with_null = "test\x00.py"
content = "print('hello')"

file_obj = File.from_contents(content, filename_with_null)
```

## Why This Is A Bug

While null characters in filenames are invalid on most filesystems, the `from_contents` method should validate its inputs and provide a clear error message rather than crashing with a low-level `ValueError` from the path resolution code. This is especially important since `from_contents` is designed to work with in-memory content where the filename might come from untrusted sources.

## Fix

```diff
@staticmethod
def from_contents(contents: str, filename: str) -> "File":
+   # Validate filename doesn't contain null characters
+   if '\x00' in filename:
+       raise ValueError(f"Filename cannot contain null characters: {filename!r}")
    encoding = File.detect_encoding(filename, BytesIO(contents.encode("utf-8")).readline)
    return File(stream=StringIO(contents), path=Path(filename).resolve(), encoding=encoding)
```