# Bug Report: copier.settings Prefix Trust Matching Failure

**Target**: `copier.settings.Settings.is_trusted`
**Severity**: Medium  
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `is_trusted` method fails to correctly match repositories against trusted prefixes when the trust pattern ends with "/", causing repositories that should be trusted to be incorrectly rejected.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from copier.settings import Settings

@given(
    repo=st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._:/", min_size=1, max_size=100),
    prefix_len=st.integers(min_value=1, max_value=50)
)
def test_is_trusted_substring_consistency(repo, prefix_len):
    """Test that prefix trust relationships are consistent."""
    assume(prefix_len < len(repo))
    
    prefix = repo[:prefix_len]
    
    # If we trust a prefix, we should trust anything starting with it
    settings_with_prefix = Settings(trust={prefix + "/"})
    
    # Property: prefix trust should trust the full repo if it starts with prefix
    if repo.startswith(prefix):
        assert settings_with_prefix.is_trusted(repo), f"Prefix trust {prefix}/ should trust {repo}"
```

**Failing input**: `repo='00', prefix_len=1`

## Reproducing the Bug

```python
from copier.settings import Settings

# Case 1: Simple prefix matching failure
settings = Settings(trust={'0/'})
result = settings.is_trusted('00')
print(f"Trust: {{'0/'}}, Repository: '00'")
print(f"Expected: True (prefix match)")
print(f"Got: {result}")

# Case 2: More realistic example
settings2 = Settings(trust={'github.com/myorg/'})
result2 = settings2.is_trusted('github.com/myorg')
print(f"\nTrust: {{'github.com/myorg/'}}, Repository: 'github.com/myorg'")
print(f"Expected: True (prefix match)")
print(f"Got: {result2}")
```

## Why This Is A Bug

The `trust` field is documented as "List of trusted repositories or prefixes". When a trust entry ends with "/", it's intended to act as a prefix matcher. However, the current implementation checks if the repository starts with the trusted string INCLUDING the trailing slash. This means:

- `trust={'test/'}` will NOT trust repository `'test'` (it only trusts `'test/...'`)
- `trust={'github.com/org/'}` will NOT trust `'github.com/org'` (only `'github.com/org/...'`)

This violates the expected prefix matching behavior where a prefix `'test/'` should trust both `'test'` itself and anything starting with `'test/'`.

## Fix

```diff
--- a/copier/settings.py
+++ b/copier/settings.py
@@ -65,7 +65,7 @@ class Settings(BaseModel):
     def is_trusted(self, repository: str) -> bool:
         """Check if a repository is trusted."""
         return any(
-            repository.startswith(self.normalize(trusted))
+            repository.startswith(self.normalize(trusted[:-1])) or repository == self.normalize(trusted[:-1])
             if trusted.endswith("/")
             else repository == self.normalize(trusted)
             for trusted in self.trust
```

Alternatively, a cleaner fix:

```diff
--- a/copier/settings.py
+++ b/copier/settings.py
@@ -65,7 +65,8 @@ class Settings(BaseModel):
     def is_trusted(self, repository: str) -> bool:
         """Check if a repository is trusted."""
         return any(
-            repository.startswith(self.normalize(trusted))
+            # For prefix matching, check against the prefix without trailing slash
+            repository.startswith(self.normalize(trusted[:-1]))
             if trusted.endswith("/")
             else repository == self.normalize(trusted)
             for trusted in self.trust
```