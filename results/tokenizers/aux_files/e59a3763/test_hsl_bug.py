#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

from tokenizers.tools import Annotation, EncodingVisualizer

# Test the HSL format bug
def test_hsl_format_bug():
    """Test that calculate_label_colors produces valid HSL format"""
    # Create a simple annotation
    annotations = [Annotation(0, 5, "test_label")]
    
    # Calculate colors
    colors = EncodingVisualizer.calculate_label_colors(annotations)
    
    print(f"Generated color for 'test_label': {colors['test_label']}")
    
    # Check if it's valid HSL - should have closing parenthesis
    color = colors['test_label']
    assert color.startswith('hsl('), f"Color should start with 'hsl(', got: {color}"
    assert color.endswith(')'), f"Color should end with ')', got: {color}"
    assert color.count('(') == color.count(')'), f"Parentheses not balanced in: {color}"

if __name__ == "__main__":
    test_hsl_format_bug()