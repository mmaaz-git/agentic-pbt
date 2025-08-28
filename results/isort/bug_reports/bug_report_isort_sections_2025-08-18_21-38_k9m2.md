# Bug Report: isort.sections Regex Metacharacter Handling

**Target**: `isort.settings.Config.known_patterns`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

Module names containing regex metacharacters cause regex compilation errors or incorrect section placement when configured in known_first_party, known_third_party, etc.

## Property-Based Test

```python
@given(
    st.lists(
        st.text(alphabet=st.characters(blacklist_categories=['Cc', 'Cs']), min_size=1, max_size=20),
        min_size=1,
        max_size=5,
        unique=True
    )
)
def test_module_placement_with_known_first_party(module_names):
    """Property test: Modules configured as first-party should be placed in FIRSTPARTY section."""
    config = Config(known_first_party=frozenset(module_names))
    
    for module_name in module_names:
        placement = module(module_name, config)
        assert placement == sections.FIRSTPARTY
```

**Failing input**: `module_names=['$']`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from isort.settings import Config
from isort.place import module

# Bug 1: Module '$' not recognized as first-party
config = Config(known_first_party=frozenset(['$']))
placement = module('$', config)
assert placement == 'FIRSTPARTY', f"Expected FIRSTPARTY, got {placement}"

# Bug 2: Module names with regex metacharacters cause crashes
config = Config(known_first_party=frozenset(['test(']))
placement = module('test(', config)  # Raises PatternError
```

## Why This Is A Bug

The code in `isort/settings.py` (lines 670-671) converts module names to regex patterns but only escapes `*` and `?` for glob patterns. It doesn't escape regex metacharacters like `$`, `(`, `)`, `[`, `]`, `+`, `{`, `}`, etc. This causes:

1. Silent failures where modules like `$` don't match their own pattern
2. Regex compilation errors for modules with unbalanced metacharacters like `(` or `)`

## Fix

```diff
--- a/isort/settings.py
+++ b/isort/settings.py
@@ -667,7 +667,8 @@ class Config(_Config):
                 for pattern in self._parse_known_pattern(known_pattern)
             ]
             for known_pattern in known_patterns:
-                regexp = "^" + known_pattern.replace("*", ".*").replace("?", ".?") + "$"
+                escaped = re.escape(known_pattern)
+                regexp = "^" + escaped.replace(r"\*", ".*").replace(r"\?", ".?") + "$"
                 self._known_patterns.append((re.compile(regexp), placement))
 
         return self._known_patterns
```