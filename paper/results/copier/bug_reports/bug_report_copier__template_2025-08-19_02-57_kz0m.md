# Bug Report: copier._template.Template Type Contract Violation in subdirectory Property

**Target**: `copier._template.Template.subdirectory`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `Template.subdirectory` property violates its type annotation by returning `None` instead of a string when the YAML configuration contains an empty or null value for `_subdirectory`.

## Property-Based Test

```python
@given(
    st.one_of(
        st.text(min_size=0, max_size=50),
        st.none(),
    )
)
def test_template_subdirectory_type(subdir_value):
    """Test that Template.subdirectory is always a string."""
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir) / "template"
        template_dir.mkdir()
        
        config_file = template_dir / "copier.yml"
        if subdir_value is not None:
            config_file.write_text(f"_subdirectory: {subdir_value}")
        else:
            config_file.write_text("")
        
        template = Template(url=str(template_dir))
        
        # subdirectory should always be a string
        assert isinstance(template.subdirectory, str)
```

**Failing input**: `subdir_value=""` (empty string in YAML)

## Reproducing the Bug

```python
import tempfile
from pathlib import Path
from copier._template import Template

with tempfile.TemporaryDirectory() as tmpdir:
    template_dir = Path(tmpdir) / "template"
    template_dir.mkdir()
    
    # Create copier.yml with empty subdirectory
    config_file = template_dir / "copier.yml"
    config_file.write_text("_subdirectory: ")  # Empty value
    
    template = Template(url=str(template_dir))
    
    print(f"subdirectory value: {repr(template.subdirectory)}")
    print(f"subdirectory type: {type(template.subdirectory)}")
    
    # This assertion fails
    assert isinstance(template.subdirectory, str)
```

## Why This Is A Bug

1. **Type annotation violation**: The method signature declares `def subdirectory(self) -> str:` but returns `None` in certain cases
2. **Inconsistent behavior**: The `templates_suffix` property correctly handles `None` values by checking and returning a default, while `subdirectory` does not
3. **Documentation mismatch**: The docstring states it returns "the subdirectory as specified in the template" with a default of empty string, but it can return `None`

## Fix

The bug occurs because `dict.get(key, default)` only returns the default when the key is missing, not when the value is `None`. The fix is to explicitly check for `None` like the `templates_suffix` property does:

```diff
@cached_property
def subdirectory(self) -> str:
    """Get the subdirectory as specified in the template.
    
    The subdirectory points to the real template code, allowing the
    templater to separate it from other template assets, such as docs,
    tests, etc.
    
    See [subdirectory][].
    """
-   return self.config_data.get("subdirectory", "")
+   result = self.config_data.get("subdirectory", "")
+   if result is None:
+       return ""
+   return result
```