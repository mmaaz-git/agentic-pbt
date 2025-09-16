# Bug Report: bs4.element Tag.__contains__ Uses Value Equality Instead of Identity

**Target**: `bs4.element.Tag.__contains__`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Tag.__contains__ uses value equality (==) instead of identity (is) when checking if an element is in a tag's contents, causing false positives for elements with the same value but different identities.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from bs4.element import Tag, NavigableString

@st.composite
def tag_strategy(draw):
    name = draw(st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=10))
    return Tag(name=name)

@st.composite
def navigable_string_strategy(draw):
    content = draw(st.text(min_size=0, max_size=100))
    return NavigableString(content)

@given(
    tag=tag_strategy(),
    elements=st.lists(navigable_string_strategy(), min_size=3, max_size=5)
)
def test_extract_insert_roundtrip(tag, elements):
    for element in elements:
        tag.append(element)
    
    extract_index = len(tag.contents) // 2
    extracted = tag.contents[extract_index]
    
    extracted.extract()
    
    # BUG: This assertion fails when elements have identical values
    assert extracted not in tag.contents  # Fails for identical strings
```

**Failing input**: `tag=Tag(name='a'), elements=[NavigableString(''), NavigableString(''), NavigableString('')]`

## Reproducing the Bug

```python
from bs4.element import Tag, NavigableString

# Create a tag and add a NavigableString
tag = Tag(name="p")
string1 = NavigableString("Hello")
tag.append(string1)

# Create another NavigableString with same value
string2 = NavigableString("Hello")

# Bug: string2 appears to be in tag.contents even though never added
print(f"string2 in tag.contents: {string2 in tag.contents}")  # True (wrong!)
print(f"string2.parent: {string2.parent}")  # None (correct)

# Same issue with Tags
parent = Tag(name="div")
child1 = Tag(name="span")
parent.append(child1)

child2 = Tag(name="span")  # Identical but separate tag
print(f"child2 in parent.contents: {child2 in parent.contents}")  # True (wrong!)
```

## Why This Is A Bug

The `in` operator should check object identity for mutable container membership, not value equality. This violates the principle that only elements explicitly added to a tag should be considered "in" that tag's contents. It causes issues with extraction operations and any code relying on membership testing.

## Fix

```diff
--- a/bs4/element.py
+++ b/bs4/element.py
@@ -2224,7 +2224,7 @@ class Tag(PageElement):
         return len(self.contents)
 
     def __contains__(self, x: Any) -> bool:
-        return x in self.contents
+        return any(elem is x for elem in self.contents)
 
     def __bool__(self) -> bool:
         "A tag is non-None even if it has no contents."
```