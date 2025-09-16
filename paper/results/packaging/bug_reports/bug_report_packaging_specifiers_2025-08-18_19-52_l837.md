# Bug Report: packaging.specifiers Filter/Contains Inconsistency for Prereleases

**Target**: `packaging.specifiers.Specifier`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `contains()` and `filter()` methods of `Specifier` return inconsistent results for prerelease versions when using the `!=` operator.

## Property-Based Test

```python
@given(
    spec_str=specifier_string_strategy(),
    versions=st.lists(version_strategy(), min_size=1, max_size=20)
)
def test_filter_contains_consistency(spec_str, versions):
    """Property: v in spec.filter([v]) iff v in spec"""
    spec = Specifier(spec_str)
    
    for v in versions:
        version_obj = Version(v)
        is_contained = version_obj in spec
        filtered = list(spec.filter([v]))
        is_in_filtered = v in filtered
        
        assert is_contained == is_in_filtered
```

**Failing input**: `spec_str='!=0', versions=['0a1']`

## Reproducing the Bug

```python
from packaging.specifiers import Specifier
from packaging.version import Version

spec = Specifier('!=0')
version = '0a1'
version_obj = Version(version)

contains_result = version_obj in spec
filter_result = list(spec.filter([version]))

print(f"contains() says {version} in spec: {contains_result}")  # False
print(f"filter() returns: {filter_result}")  # ['0a1']

assert contains_result == (version in filter_result)  # AssertionError
```

## Why This Is A Bug

The `contains()` method and `filter()` method should be consistent - if a version is contained according to `contains()`, it should appear in the filtered results, and vice versa. The documentation implies these methods should behave consistently, just with different interfaces (single item vs. iterable).

The inconsistency occurs because `contains()` excludes the prerelease `0a1` by default (treating it as not matching `!=0`), while `filter()` includes it. This violates the expected equivalence: `v in spec` should equal `v in list(spec.filter([v]))`.

## Fix

The issue appears to be in how prereleases are handled differently between the two methods. Both methods should apply the same prerelease logic. A potential fix would ensure that default prerelease handling is consistent between `contains()` and `filter()` methods.