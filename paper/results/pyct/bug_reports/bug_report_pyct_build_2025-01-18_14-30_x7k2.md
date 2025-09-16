# Bug Report: pyct.build.get_setup_version Returns String "None" Instead of Version

**Target**: `pyct.build.get_setup_version`
**Severity**: High  
**Bug Type**: Logic
**Date**: 2025-01-18

## Summary

The `get_setup_version()` function returns the string `"None"` instead of the actual version when called, even when a valid `.version` file exists.

## Property-Based Test

```python
@given(
    reponame=valid_reponame,
    version_string=st.text(min_size=1, max_size=50).filter(lambda s: s.strip())
)
@settings(max_examples=100)
def test_get_setup_version_json_parsing(reponame, version_string):
    """Test that get_setup_version correctly parses JSON from .version file."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        module_dir = Path(tmpdir) / reponame
        module_dir.mkdir()
        
        version_file = module_dir / ".version"
        version_data = {"version_string": version_string}
        version_file.write_text(json.dumps(version_data))
        
        dummy_file = Path(tmpdir) / "setup.py"
        dummy_file.write_text("")
        
        param_backup = sys.modules.get('param')
        if 'param' in sys.modules:
            del sys.modules['param']
        
        try:
            result = pyct.build.get_setup_version(str(dummy_file), reponame)
            assert result == version_string
        finally:
            if param_backup:
                sys.modules['param'] = param_backup
```

**Failing input**: `reponame='A', version_string='0'`

## Reproducing the Bug

```python
import os
import tempfile
from pathlib import Path
import pyct.build

with tempfile.TemporaryDirectory() as tmpdir:
    dummy_file = Path(tmpdir) / "setup.py"
    dummy_file.write_text("")
    
    filepath = os.path.abspath(os.path.dirname(str(dummy_file)))
    reponame = "testpackage"
    
    result = pyct.build.get_setup_version(str(dummy_file), reponame)
    print(f"Result: {result}")
    assert result != "None", "Function returns string 'None' instead of version"
```

## Why This Is A Bug

The function is supposed to return a version string for use in setup.py files. Instead, it returns the string `"None"` because `param.version.Version.setup_version()` returns this string when it fails to determine the version, rather than raising an exception or returning a proper default. This breaks any setup.py that relies on this function to provide the package version.

## Fix

The issue is that when `param.version.Version.setup_version()` fails, it returns the string `"None"`. The pyct.build module should handle this case properly. Here's a potential fix:

```diff
--- a/pyct/build.py
+++ b/pyct/build.py
@@ -40,7 +40,11 @@ def get_setup_version(root, reponame):
     except:
         version = None
     if version is not None:
-        return version.Version.setup_version(filepath, reponame, archive_commit="$Format:%h$")
+        result = version.Version.setup_version(filepath, reponame, archive_commit="$Format:%h$")
+        if result == "None":
+            # Fallback to .version file if param returns "None"
+            return json.load(open(version_file_path, 'r'))['version_string'] if os.path.exists(version_file_path) else None
+        return result
     else:
         print("WARNING: param>=1.6.0 unavailable. If you are installing a package, this warning can safely be ignored. If you are creating a package or otherwise operating in a git repository, you should install param>=1.6.0.")
         return json.load(open(version_file_path, 'r'))['version_string']
```