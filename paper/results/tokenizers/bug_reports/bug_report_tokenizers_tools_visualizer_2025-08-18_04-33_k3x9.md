# Bug Report: tokenizers.tools.visualizer Missing Closing Parenthesis in HSL Color Format

**Target**: `tokenizers.tools.visualizer.EncodingVisualizer.calculate_label_colors`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `calculate_label_colors` method generates malformed HSL color strings missing a closing parenthesis, causing CSS parsing errors when used in HTML visualization.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import re
from tokenizers.tools import Annotation, EncodingVisualizer

@given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10))
def test_calculate_label_colors_valid_hsl_format(labels):
    annotations = [Annotation(i*10, i*10+5, label) for i, label in enumerate(labels)]
    colors = EncodingVisualizer.calculate_label_colors(annotations)
    
    hsl_pattern = re.compile(r'^hsl\(\d+,\d+%,\d+%\)$')  # Correct HSL format with closing paren
    for label, color in colors.items():
        assert hsl_pattern.match(color), f"Invalid HSL format: '{color}'"
```

**Failing input**: Any non-empty list of annotations, e.g., `['label1']`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')
from tokenizers.tools import Annotation, EncodingVisualizer

annotations = [Annotation(0, 5, "test_label")]
colors = EncodingVisualizer.calculate_label_colors(annotations)
color = colors["test_label"]

print(f"Generated color: '{color}'")
assert color.endswith(')'), f"Missing closing parenthesis in HSL: {color}"
```

## Why This Is A Bug

The HSL color format in CSS requires the format `hsl(hue, saturation%, lightness%)` with balanced parentheses. The current implementation produces `hsl(10,32%,64%` without the closing parenthesis, which will cause CSS parsing errors when these colors are used in the HTML visualization. This violates the expected HSL format contract and will break the visualization feature.

## Fix

```diff
--- a/tokenizers/tools/visualizer.py
+++ b/tokenizers/tools/visualizer.py
@@ -175,7 +175,7 @@ class EncodingVisualizer:
         colors = {}
 
         for label in sorted(labels):  # sort so we always get the same colors for a given set of labels
-            colors[label] = f"hsl({h},{s}%,{l}%"
+            colors[label] = f"hsl({h},{s}%,{l}%)"
             h += h_step
         return colors
```