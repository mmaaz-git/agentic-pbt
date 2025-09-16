# Bug Report: troposphere.opensearchservice Engine Version Validation Regex Bug

**Target**: `troposphere.validators.opensearchservice.validate_search_service_engine_version`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The regex pattern in `validate_search_service_engine_version` incorrectly accepts any character as a separator between major and minor version numbers, not just a literal dot, due to an unescaped dot in the regex pattern.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import re
from troposphere.validators.opensearchservice import validate_search_service_engine_version

@given(
    prefix=st.sampled_from(["OpenSearch_", "Elasticsearch_"]),
    major=st.integers(min_value=0, max_value=99999),
    separator=st.sampled_from(["X", "#", "!", "@", "A", " ", "-", "+"]),
    minor=st.integers(min_value=0, max_value=99999)
)
def test_invalid_separator_should_be_rejected(prefix, major, separator, minor):
    version_string = f"{prefix}{major}{separator}{minor}"
    
    try:
        result = validate_search_service_engine_version(version_string)
        assert False, f"Invalid version accepted: {version_string}"
    except ValueError:
        pass
```

**Failing input**: `OpenSearch_0X0`

## Reproducing the Bug

```python
from troposphere.validators.opensearchservice import validate_search_service_engine_version

invalid_versions = [
    "OpenSearch_1X2",
    "Elasticsearch_3#4",
    "OpenSearch_5A6",
    "Elasticsearch_7!8"
]

for version in invalid_versions:
    result = validate_search_service_engine_version(version)
    print(f"Accepted invalid version: {version}")
```

## Why This Is A Bug

The function is intended to validate OpenSearch/Elasticsearch version strings in the format "OpenSearch_X.Y" or "Elasticsearch_X.Y" where X and Y are version numbers separated by a dot. However, the regex pattern `r"^(OpenSearch_|Elasticsearch_)\d{1,5}.\d{1,5}"` uses an unescaped dot (`.`) which matches ANY character in regex, not just a literal period. This allows invalid version strings like "OpenSearch_1X2" to pass validation when they should be rejected.

## Fix

```diff
--- a/troposphere/validators/opensearchservice.py
+++ b/troposphere/validators/opensearchservice.py
@@ -13,7 +13,7 @@ def validate_search_service_engine_version(engine_version):
     Property: Domain.EngineVersion
     """
 
-    engine_version_check = re.compile(r"^(OpenSearch_|Elasticsearch_)\d{1,5}.\d{1,5}")
+    engine_version_check = re.compile(r"^(OpenSearch_|Elasticsearch_)\d{1,5}\.\d{1,5}")
     if engine_version_check.match(engine_version) is None:
         raise ValueError(
             "OpenSearch EngineVersion must be in the format OpenSearch_X.Y or Elasticsearch_X.Y"
```