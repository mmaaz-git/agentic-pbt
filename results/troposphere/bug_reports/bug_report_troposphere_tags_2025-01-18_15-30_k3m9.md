# Bug Report: Troposphere Tags Concatenation Creates Duplicate Keys

**Target**: `troposphere.Tags`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-01-18

## Summary

The Tags concatenation operator (+) creates duplicate tag keys when combining Tags objects with overlapping keys, resulting in invalid CloudFormation templates.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere import Tags

@given(
    tags1=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=10
    ),
    tags2=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=10
    )
)
def test_tags_concatenation(tags1, tags2):
    t1 = Tags(**tags1)
    t2 = Tags(**tags2)
    combined = t1 + t2
    combined_dict = combined.to_dict()
    
    # Check for duplicates
    keys = [tag['Key'] for tag in combined_dict]
    assert len(keys) == len(set(keys)), "Duplicate keys found"
```

**Failing input**: `tags1={'A': '0'}, tags2={'A': '0'}`

## Reproducing the Bug

```python
from troposphere import Tags

tags1 = Tags(Environment="Production")
tags2 = Tags(Environment="Development")

combined = tags1 + tags2
print(combined.to_dict())
```

Output:
```
[{'Key': 'Environment', 'Value': 'Production'}, {'Key': 'Environment', 'Value': 'Development'}]
```

## Why This Is A Bug

AWS CloudFormation does not allow duplicate tag keys on resources. When a Tags object with duplicate keys is used in a CloudFormation template, it will be rejected by AWS. The concatenation operator should either merge tags with the same key (keeping one value) or raise an error when duplicate keys are detected.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -742,7 +742,14 @@ class Tags(AWSHelperFn):
 
     # allow concatenation of the Tags object via '+' operator
     def __add__(self, newtags: Tags) -> Tags:
-        newtags.tags = self.tags + newtags.tags
+        # Merge tags, avoiding duplicates
+        existing_keys = {tag.get('Key') if isinstance(tag, dict) else tag.data.get('Key') 
+                         for tag in self.tags}
+        merged_tags = self.tags.copy()
+        for tag in newtags.tags:
+            key = tag.get('Key') if isinstance(tag, dict) else tag.data.get('Key')
+            if key not in existing_keys:
+                merged_tags.append(tag)
+        newtags.tags = merged_tags
         return newtags
```