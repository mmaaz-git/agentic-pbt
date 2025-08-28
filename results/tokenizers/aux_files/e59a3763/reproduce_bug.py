#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

from tokenizers.tools import Annotation, EncodingVisualizer

# Minimal reproduction of the HSL format bug
annotations = [Annotation(0, 5, "label1"), Annotation(10, 15, "label2")]
colors = EncodingVisualizer.calculate_label_colors(annotations)

print("Bug demonstration:")
print("Generated colors:")
for label, color in colors.items():
    print(f"  {label}: '{color}'")
    print(f"    Missing closing parenthesis: {not color.endswith(')')}")

# This would fail if used in CSS
print("\nImpact: These malformed HSL values would cause CSS parsing errors")