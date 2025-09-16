# Bug Report: sphinxcontrib.applehelp Control Character Crash

**Target**: `sphinxcontrib.applehelp.AppleHelpBuilder.build_info_plist`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The AppleHelpBuilder crashes when configuration values (title, bundle_id, etc.) contain control characters because plistlib.dump() cannot serialize them.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import plistlib
from io import BytesIO

@given(
    st.text(min_size=1),  # bundle_id
    st.text(min_size=1),  # dev_region
    st.text(min_size=1),  # release
    st.text(min_size=1),  # bundle_version
    st.text(min_size=1),  # title
)
def test_plist_round_trip(bundle_id, dev_region, release, bundle_version, title):
    info_plist = {
        'CFBundleDevelopmentRegion': dev_region,
        'CFBundleIdentifier': bundle_id,
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundlePackageType': 'BNDL',
        'CFBundleShortVersionString': release,
        'CFBundleSignature': 'hbwr',
        'CFBundleVersion': bundle_version,
        'HPDBookAccessPath': '_access.html',
        'HPDBookIndexPath': 'search.helpindex',
        'HPDBookTitle': title,
        'HPDBookType': '3',
        'HPDBookUsesExternalViewer': False,
    }
    
    buffer = BytesIO()
    plistlib.dump(info_plist, buffer)
    buffer.seek(0)
    loaded = plistlib.load(buffer)
    assert loaded == info_plist
```

**Failing input**: `title='\x1f'`

## Reproducing the Bug

```python
import plistlib
import tempfile

info_plist = {
    'CFBundleDevelopmentRegion': 'en-us',
    'CFBundleIdentifier': 'com.example.test',
    'CFBundleInfoDictionaryVersion': '6.0',
    'CFBundlePackageType': 'BNDL',
    'CFBundleShortVersionString': '1.0',
    'CFBundleSignature': 'hbwr',
    'CFBundleVersion': '1',
    'HPDBookAccessPath': '_access.html',
    'HPDBookIndexPath': 'search.helpindex',
    'HPDBookTitle': 'Test\x1fTitle',
    'HPDBookType': '3',
    'HPDBookUsesExternalViewer': False,
}

with tempfile.NamedTemporaryFile(suffix='.plist') as f:
    plistlib.dump(info_plist, f)
```

## Why This Is A Bug

This violates expected behavior because users may accidentally include control characters in their Sphinx configuration (e.g., from copy-pasting terminal output with ANSI codes), causing the entire documentation build to fail with an unhelpful error message. The builder should either sanitize inputs or provide clearer error messages.

## Fix

```diff
--- a/sphinxcontrib/applehelp/__init__.py
+++ b/sphinxcontrib/applehelp/__init__.py
@@ -3,6 +3,7 @@
 from __future__ import annotations
 
 import plistlib
+import re
 import shlex
 import subprocess
 from os import environ, path
@@ -126,10 +127,20 @@ class AppleHelpBuilder(StandaloneHTMLBuilder):
         if self.config.applehelp_codesign_identity:
             self.do_codesign()
 
+    def _sanitize_plist_string(self, value: str) -> str:
+        """Remove control characters that plistlib cannot handle."""
+        # Remove control characters except tab, newline, carriage return
+        return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', value)
+
     @progress_message(__('writing Info.plist'))
     def build_info_plist(self, contents_dir: str) -> None:
         """Construct the Info.plist file."""
+        # Sanitize string values to prevent plistlib errors
+        bundle_id = self._sanitize_plist_string(self.config.applehelp_bundle_id)
+        title = self._sanitize_plist_string(self.config.applehelp_title)
+        release = self._sanitize_plist_string(self.config.release)
+        bundle_version = self._sanitize_plist_string(self.config.applehelp_bundle_version)
+        
         info_plist = {
             'CFBundleDevelopmentRegion': self.config.applehelp_dev_region,
-            'CFBundleIdentifier': self.config.applehelp_bundle_id,
+            'CFBundleIdentifier': bundle_id,
             'CFBundleInfoDictionaryVersion': '6.0',
             'CFBundlePackageType': 'BNDL',
-            'CFBundleShortVersionString': self.config.release,
+            'CFBundleShortVersionString': release,
             'CFBundleSignature': 'hbwr',
-            'CFBundleVersion': self.config.applehelp_bundle_version,
+            'CFBundleVersion': bundle_version,
             'HPDBookAccessPath': '_access.html',
             'HPDBookIndexPath': 'search.helpindex',
-            'HPDBookTitle': self.config.applehelp_title,
+            'HPDBookTitle': title,
             'HPDBookType': '3',
             'HPDBookUsesExternalViewer': False,
         }
```