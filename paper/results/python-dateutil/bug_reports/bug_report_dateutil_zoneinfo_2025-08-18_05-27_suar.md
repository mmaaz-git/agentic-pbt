# Bug Report: dateutil.zoneinfo Unhandled Exceptions in Metadata Parsing

**Target**: `dateutil.zoneinfo.ZoneInfoFile`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

`ZoneInfoFile.__init__` crashes with unhandled `JSONDecodeError` or `UnicodeDecodeError` when the METADATA file in a tarball contains invalid JSON or non-UTF-8 data.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import json
from io import BytesIO
from tarfile import TarFile, TarInfo
import dateutil.zoneinfo

@given(st.binary())
def test_metadata_parsing_robustness(metadata_content):
    """ZoneInfoFile should handle any binary content in METADATA file without crashing"""
    tar_bytes = BytesIO()
    with TarFile.open(mode='w:gz', fileobj=tar_bytes) as tf:
        meta_info = TarInfo(name='METADATA')
        meta_info.size = len(metadata_content)
        tf.addfile(meta_info, BytesIO(metadata_content))
    tar_bytes.seek(0)
    
    # This should not crash with unhandled exceptions
    zif = dateutil.zoneinfo.ZoneInfoFile(zonefile_stream=tar_bytes)
```

**Failing input**: `b''` (empty bytes) and `b'\x80'` (invalid UTF-8)

## Reproducing the Bug

```python
import json
from io import BytesIO
from tarfile import TarFile, TarInfo
import dateutil.zoneinfo

# Case 1: Empty METADATA file
tar_bytes = BytesIO()
with TarFile.open(mode='w:gz', fileobj=tar_bytes) as tf:
    meta_info = TarInfo(name='METADATA')
    meta_info.size = 0
    tf.addfile(meta_info, BytesIO(b''))
tar_bytes.seek(0)

zif = dateutil.zoneinfo.ZoneInfoFile(zonefile_stream=tar_bytes)
# Raises: json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

# Case 2: Invalid UTF-8 in METADATA
tar_bytes2 = BytesIO()
with TarFile.open(mode='w:gz', fileobj=tar_bytes2) as tf:
    meta_info = TarInfo(name='METADATA')
    meta_info.size = 1
    tf.addfile(meta_info, BytesIO(b'\x80'))
tar_bytes2.seek(0)

zif2 = dateutil.zoneinfo.ZoneInfoFile(zonefile_stream=tar_bytes2)
# Raises: UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 0
```

## Why This Is A Bug

The `ZoneInfoFile` class should gracefully handle malformed metadata files in tarballs. Since the metadata is optional (the code already handles missing METADATA files by setting `self.metadata = None`), it should similarly handle corrupted or invalid metadata rather than crashing. This could occur with corrupted tarball downloads or manually created zone files.

## Fix

```diff
--- a/dateutil/zoneinfo/__init__.py
+++ b/dateutil/zoneinfo/__init__.py
@@ -42,10 +42,15 @@ class ZoneInfoFile(object):
                 self.zones.update(links)
                 try:
                     metadata_json = tf.extractfile(tf.getmember(METADATA_FN))
-                    metadata_str = metadata_json.read().decode('UTF-8')
-                    self.metadata = json.loads(metadata_str)
+                    try:
+                        metadata_str = metadata_json.read().decode('UTF-8')
+                        self.metadata = json.loads(metadata_str)
+                    except (UnicodeDecodeError, json.JSONDecodeError):
+                        # Invalid metadata file - treat as if no metadata exists
+                        self.metadata = None
                 except KeyError:
                     # no metadata in tar file
                     self.metadata = None
         else:
             self.zones = {}
             self.metadata = None
```