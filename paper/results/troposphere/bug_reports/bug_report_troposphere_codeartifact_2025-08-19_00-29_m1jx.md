# Bug Report: troposphere.codeartifact Empty String Validation Failure

**Target**: `troposphere.codeartifact`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Required string properties in troposphere.codeartifact accept empty strings, violating the validation contract and potentially causing CloudFormation deployment failures.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.codeartifact as codeartifact

valid_titles = st.text(alphabet=st.characters(min_codepoint=48, max_codepoint=122), min_size=1, max_size=20).filter(lambda s: s.isalnum())

@given(
    title=valid_titles,
    pattern=st.text(min_size=0, max_size=200)
)
def test_packagegroup_pattern_edge_cases(title, pattern):
    """Test PackageGroup with various pattern formats including empty"""
    if pattern == "":
        # Empty pattern should fail since it's required
        with pytest.raises(ValueError):
            pg = codeartifact.PackageGroup(
                title=title,
                DomainName="test-domain",
                Pattern=pattern
            )
            pg.to_dict()
```

**Failing input**: `pattern=""`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.codeartifact as codeartifact

# All these should fail validation but don't
domain = codeartifact.Domain(title="D1", DomainName="")
repository = codeartifact.Repository(title="R1", RepositoryName="", DomainName="")
package_group = codeartifact.PackageGroup(title="PG1", DomainName="", Pattern="")
restriction = codeartifact.RestrictionType(RestrictionMode="")

# All convert to dict successfully with empty required fields
for obj in [domain, repository, package_group, restriction]:
    print(f"{obj.__class__.__name__}: {obj.to_dict()}")
```

## Why This Is A Bug

The library marks these properties as required (True) in the props definition, but the validation in `BaseAWSObject._validate_props()` only checks if the property key exists in the properties dict, not if the value is meaningful. Empty strings are accepted for required string fields, which will likely cause CloudFormation deployment failures since these AWS resources require non-empty values for these fields.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -411,7 +411,10 @@ class BaseAWSObject:
     def _validate_props(self) -> None:
         for k, (_, required) in self.props.items():
             if required and k not in self.properties:
                 rtype = getattr(self, "resource_type", type(self))
                 title = getattr(self, "title")
                 msg = "Resource %s required in type %s" % (k, rtype)
                 if title:
                     msg += " (title: %s)" % title
                 raise ValueError(msg)
+            # Also validate that required string properties are not empty
+            if required and k in self.properties:
+                value = self.properties[k]
+                expected_type = self.props[k][0]
+                if expected_type == str and isinstance(value, str) and not value:
+                    rtype = getattr(self, "resource_type", type(self))
+                    title = getattr(self, "title")
+                    msg = "Resource %s cannot be empty in type %s" % (k, rtype)
+                    if title:
+                        msg += " (title: %s)" % title
+                    raise ValueError(msg)
```