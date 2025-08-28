# Bug Report: pdfkit.configuration Incorrect Exception Type for Null Bytes

**Target**: `pdfkit.configuration.Configuration`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Configuration raises ValueError instead of IOError when given binary paths containing null bytes, violating the API contract.

## Property-Based Test

```python
@given(
    wkhtmltopdf_path=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=200),
        st.binary(min_size=1, max_size=200)
    )
)
def test_invalid_path_raises_ioerror(wkhtmltopdf_path):
    """Test that invalid paths raise IOError with appropriate message"""
    
    # Skip if the path accidentally points to a real file
    if wkhtmltopdf_path:
        try:
            path_str = wkhtmltopdf_path.decode('utf-8') if isinstance(wkhtmltopdf_path, bytes) else wkhtmltopdf_path
            if os.path.exists(path_str):
                assume(False)
        except:
            pass
    
    # Property: Invalid paths should raise IOError
    with pytest.raises(IOError) as exc_info:
        Configuration(wkhtmltopdf=wkhtmltopdf_path)
    
    assert 'No wkhtmltopdf executable found' in str(exc_info.value)
```

**Failing input**: `b'\x00'`

## Reproducing the Bug

```python
from pdfkit.configuration import Configuration

config = Configuration(wkhtmltopdf=b'\x00')
```

## Why This Is A Bug

The Configuration class is designed to raise IOError for all invalid path scenarios (lines 37-42 in configuration.py). However, when a binary path contains null bytes, Python's `open()` function raises ValueError, which is not caught and re-raised as IOError. This breaks the API contract where all path validation errors should be IOError.

## Fix

```diff
--- a/pdfkit/configuration.py
+++ b/pdfkit/configuration.py
@@ -34,7 +34,7 @@ class Configuration(object):
 
             with open(self.wkhtmltopdf) as f:
                 pass
-        except (IOError, FileNotFoundError) as e:
+        except (IOError, FileNotFoundError, ValueError) as e:
             raise IOError('No wkhtmltopdf executable found: "%s"\n'
                           'If this file exists please check that this process can '
                           'read it or you can pass path to it manually in method call, '
```