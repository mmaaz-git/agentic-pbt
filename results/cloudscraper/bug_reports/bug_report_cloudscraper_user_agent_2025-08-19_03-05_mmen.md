# Bug Report: cloudscraper.user_agent Empty String Validation Bypass

**Target**: `cloudscraper.user_agent.User_Agent`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Empty strings bypass browser and platform name validation in User_Agent class, allowing invalid empty values to be silently accepted instead of raising RuntimeError as documented.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from cloudscraper.user_agent import User_Agent
import pytest

@given(
    browser=st.sampled_from(['', ' ', '\t', '\n']),
    platform=st.sampled_from(['linux', 'windows'])
)
def test_empty_browser_validation(browser, platform):
    """Empty/whitespace browser names should raise RuntimeError"""
    with pytest.raises(RuntimeError, match="browser is not valid"):
        User_Agent(browser={'browser': browser, 'platform': platform})

@given(
    platform=st.sampled_from(['', ' ', '\t', '\n']),
    browser=st.sampled_from(['chrome', 'firefox'])
)
def test_empty_platform_validation(platform, browser):
    """Empty/whitespace platform names should raise RuntimeError"""
    with pytest.raises(RuntimeError, match="platform .* is not valid"):
        User_Agent(browser={'platform': platform, 'browser': browser})
```

**Failing input**: `browser=''` and `platform=''`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')
from cloudscraper.user_agent import User_Agent

# Empty browser string bypasses validation
ua1 = User_Agent(browser={'browser': '', 'platform': 'windows'})
print(f"Empty browser accepted: {ua1.headers['User-Agent']}")

# Empty platform string bypasses validation  
ua2 = User_Agent(browser={'platform': '', 'browser': 'chrome'})
print(f"Empty platform accepted: {ua2.headers['User-Agent']}")

# Both empty strings bypass validation
ua3 = User_Agent(browser={'browser': '', 'platform': ''})
print(f"Both empty accepted: {ua3.headers['User-Agent']}")
```

## Why This Is A Bug

The code intends to validate browser and platform names against allowed lists (lines 94-96 and 101-103 in `__init__.py`). However, empty strings evaluate to `False` in Python, causing the validation conditions `if self.browser` and `if self.platform` to fail, bypassing validation entirely. This violates the documented contract that invalid browser/platform names should raise RuntimeError.

## Fix

```diff
--- a/cloudscraper/user_agent/__init__.py
+++ b/cloudscraper/user_agent/__init__.py
@@ -91,7 +91,7 @@ class User_Agent():
                     ('Accept-Encoding', 'gzip, deflate, br')
                 ])
         else:
-            if self.browser and self.browser not in self.browsers:
+            if self.browser is not None and self.browser not in self.browsers:
                 sys.tracebacklimit = 0
                 raise RuntimeError(f'Sorry "{self.browser}" browser is not valid, valid browsers are [{", ".join(self.browsers)}].')
 
@@ -98,7 +98,7 @@ class User_Agent():
             if not self.platform:
                 self.platform = random.SystemRandom().choice(self.platforms)
 
-            if self.platform not in self.platforms:
+            if self.platform is not None and self.platform not in self.platforms:
                 sys.tracebacklimit = 0
                 raise RuntimeError(f'Sorry the platform "{self.platform}" is not valid, valid platforms are [{", ".join(self.platforms)}]')
```