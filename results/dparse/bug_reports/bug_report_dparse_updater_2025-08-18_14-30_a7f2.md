# Bug Report: dparse.updater Whitespace Preservation Issues

**Target**: `dparse.updater.RequirementsTXTUpdater`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

RequirementsTXTUpdater has two whitespace preservation bugs: (1) it reverses the order of mixed whitespace characters before comments, and (2) it strips trailing spaces from environment markers.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from dparse.updater import RequirementsTXTUpdater
from dparse.dependencies import Dependency

package_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_.'),
    min_size=1,
    max_size=50
).filter(lambda x: x[0].isalpha() and not x.startswith('-'))

version_strategy = st.text(
    alphabet='0123456789.',
    min_size=1,
    max_size=20
).filter(lambda v: v[0].isdigit() and v[-1].isdigit() and '..' not in v)

@given(
    name=package_name_strategy,
    old_version=version_strategy,
    new_version=version_strategy,
    comment=st.text(alphabet=st.characters(blacklist_characters='\n\r'), min_size=0, max_size=100),
    whitespace=st.text(alphabet=' \t', min_size=0, max_size=10)
)
def test_requirements_txt_preserves_comments(name, old_version, new_version, comment, whitespace):
    """Test that RequirementsTXTUpdater preserves comments exactly."""
    line = f"{name}=={old_version}{whitespace}# {comment}"
    content = line
    
    dep = Dependency(name=name, specs=f"=={old_version}", line=line, extras=[])
    result = RequirementsTXTUpdater.update(content, dep, new_version)
    
    expected_comment_part = f"{whitespace}# {comment}"
    assert expected_comment_part in result, f"Comment not preserved. Result: {result}"
```

**Failing input**: `name='A', old_version='0', new_version='0', comment='', whitespace=' \t'`

## Reproducing the Bug

```python
from dparse.updater import RequirementsTXTUpdater
from dparse.dependencies import Dependency

# Bug 1: Whitespace reversal
line1 = "A==0 \t# "
dep1 = Dependency(name="A", specs="==0", line=line1, extras=[])
result1 = RequirementsTXTUpdater.update(line1, dep1, "0")
print(f"Input:  {repr(line1)}")
print(f"Output: {repr(result1)}")
# Output shows ' \t' becomes '\t '

# Bug 2: Trailing space loss  
line2 = "A==0;  "
dep2 = Dependency(name="A", specs="==0", line=line2, extras=[])
result2 = RequirementsTXTUpdater.update(line2, dep2, "0")
print(f"Input:  {repr(line2)}")
print(f"Output: {repr(result2)}")
# Output shows trailing space after semicolon is lost
```

## Why This Is A Bug

These bugs violate the principle of preserving formatting when updating dependency files. While they don't affect functionality, they cause unnecessary diff noise in version control and can break formatting conventions that teams rely on.

## Fix

```diff
--- a/dparse/updater.py
+++ b/dparse/updater.py
@@ -30,7 +30,7 @@ class RequirementsTXTUpdater:
             # and --hashes
             new_line += ";" + \
                         dependency.line.splitlines()[0].split(";", 1)[1] \
-                            .split("#")[0].split("--hash")[0].rstrip()
+                            .split("#")[0].split("--hash")[0]
         # add the comment
         if "#" in dependency.line:
             # split the line into parts: requirement and comment
@@ -39,11 +39,12 @@ class RequirementsTXTUpdater:
             # find all whitespaces between the requirement and the comment
             whitespaces = (hex(ord('\t')), hex(ord(' ')))
             trailing_whitespace = ''
+            # Iterate forward to preserve whitespace order
             for c in requirement[::-1]:
                 if hex(ord(c)) in whitespaces:
-                    trailing_whitespace += c
+                    trailing_whitespace = c + trailing_whitespace
                 else:
                     break
             appendix += trailing_whitespace + "#" + comment
```