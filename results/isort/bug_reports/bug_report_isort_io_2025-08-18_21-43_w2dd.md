# Bug Report: isort.io UTF-16 Encoding Detection Failure

**Target**: `isort.io.File.detect_encoding`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `File.detect_encoding` method fails to detect UTF-16 encoded files even when they have a valid encoding declaration, raising an `UnsupportedEncoding` exception instead.

## Property-Based Test

```python
@given(
    encoding=st.sampled_from(['utf-8', 'utf-16', 'ascii', 'latin-1', 'cp1252', 'iso-8859-1']),
    content=st.text(min_size=0, max_size=1000)
)
def test_detect_encoding_with_explicit_declaration(encoding, content):
    encoding_line = f"# -*- coding: {encoding} -*-\n"
    
    try:
        full_content = (encoding_line + content).encode(encoding)
    except (UnicodeEncodeError, LookupError):
        assume(False)
    
    buffer = BytesIO(full_content)
    detected = File.detect_encoding("test.py", buffer.readline)
    
    try:
        full_content.decode(detected)
    except (UnicodeDecodeError, LookupError):
        assert False, f"Detected encoding {detected} cannot decode content with declared encoding {encoding}"
```

**Failing input**: `encoding='utf-16', content=''`

## Reproducing the Bug

```python
from io import BytesIO
from isort.io import File

encoding_line = "# -*- coding: utf-16 -*-\n"
content = encoding_line
full_content = content.encode('utf-16')

buffer = BytesIO(full_content)
detected = File.detect_encoding("test.py", buffer.readline)
```

## Why This Is A Bug

UTF-16 is a valid Python encoding that Python itself supports. Files with UTF-16 encoding and proper encoding declarations should be handled correctly by isort, as it processes Python source files which may use various encodings as specified in PEP 263.

## Fix

The issue is that `tokenize.detect_encoding` cannot handle UTF-16 BOM markers properly. The fix requires special handling for UTF-16/UTF-32 encodings:

```diff
@staticmethod
def detect_encoding(filename: Union[str, Path], readline: Callable[[], bytes]) -> str:
    try:
+       # Check for BOM markers first
+       first_line = readline()
+       if first_line.startswith(b'\xff\xfe'):
+           return 'utf-16-le'
+       elif first_line.startswith(b'\xfe\xff'):
+           return 'utf-16-be'
+       # Reset for tokenize
+       import io
+       if hasattr(readline, '__self__') and hasattr(readline.__self__, 'seek'):
+           readline.__self__.seek(0)
        return tokenize.detect_encoding(readline)[0]
    except Exception:
        raise UnsupportedEncoding(filename)
```