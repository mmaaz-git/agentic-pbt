#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import re
from hypothesis import given, strategies as st, assume, settings
import tokenizers
from tokenizers.tools import Annotation, EncodingVisualizer
from tokenizers.tools.visualizer import CharState


# Test 1: calculate_label_colors should be deterministic and produce unique colors
@given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10))
def test_calculate_label_colors_deterministic_and_unique(labels):
    """Test that calculate_label_colors produces deterministic and unique colors for each label"""
    # Create annotations with the given labels
    annotations = []
    for i, label in enumerate(labels):
        # Create non-overlapping annotations
        start = i * 10
        end = start + 5
        annotations.append(Annotation(start, end, label))
    
    # Calculate colors twice to check determinism
    colors1 = EncodingVisualizer.calculate_label_colors(annotations)
    colors2 = EncodingVisualizer.calculate_label_colors(annotations)
    
    # Property 1: Determinism - same input should produce same output
    assert colors1 == colors2, "calculate_label_colors is not deterministic"
    
    # Property 2: All unique labels should get a color
    unique_labels = set(labels)
    assert set(colors1.keys()) == unique_labels, "Not all labels got colors"
    
    # Property 3: All colors should be in HSL format
    hsl_pattern = re.compile(r'^hsl\(\d+,\d+%,\d+%$')
    for label, color in colors1.items():
        assert hsl_pattern.match(color), f"Color '{color}' for label '{label}' is not in HSL format"
    
    # Property 4: Different labels should get different colors (when possible)
    if len(unique_labels) <= 12:  # With h_step=20 minimum, we can have up to 12 distinct hues
        color_values = list(colors1.values())
        assert len(color_values) == len(set(color_values)), "Different labels got the same color"


# Test 2: Annotation slicing invariant - annotations are used to slice text
@given(
    st.integers(min_value=0, max_value=1000),
    st.integers(min_value=0, max_value=1000),
    st.text(min_size=1, max_size=20)
)
def test_annotation_slicing_invariant(start, end, label):
    """Test that annotations can be used for text slicing (start <= end required)"""
    # The code uses annotations to slice text (line 333: for i in range(a.start, a.end))
    # This requires start <= end
    
    # Create an annotation
    anno = Annotation(start, end, label)
    
    # If we use this annotation for slicing, Python's range requires start <= end
    # Let's verify this works without errors
    char_indices = list(range(anno.start, anno.end))
    
    # The length should be non-negative
    assert len(char_indices) >= 0
    
    # If start > end, the range should be empty (Python behavior)
    if anno.start > anno.end:
        assert len(char_indices) == 0


# Test 3: __make_anno_map correctness
@given(
    st.text(min_size=0, max_size=100),
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=100),
            st.integers(min_value=0, max_value=100),
            st.text(min_size=1, max_size=10)
        ),
        max_size=5
    )
)
def test_make_anno_map_correctness(text, anno_data):
    """Test that __make_anno_map correctly maps character indices to annotations"""
    # Filter annotations to be within text bounds
    annotations = []
    for start, end, label in anno_data:
        # Ensure annotations are within text bounds
        if len(text) > 0:
            start = min(start, len(text))
            end = min(end, len(text))
        else:
            start = 0
            end = 0
        
        # Ensure start <= end for valid range
        if start > end:
            start, end = end, start
            
        annotations.append(Annotation(start, end, label))
    
    # Call the private method
    anno_map = EncodingVisualizer._EncodingVisualizer__make_anno_map(text, annotations)
    
    # Property 1: The map should have the same length as the text
    assert len(anno_map) == len(text), f"Map length {len(anno_map)} != text length {len(text)}"
    
    # Property 2: Characters within annotation bounds should map to the correct annotation index
    for anno_ix, anno in enumerate(annotations):
        for char_ix in range(anno.start, min(anno.end, len(text))):
            # Later annotations can overwrite earlier ones (based on code logic)
            # So we only check if this annotation is the last one covering this position
            is_overwritten = False
            for later_ix in range(anno_ix + 1, len(annotations)):
                later_anno = annotations[later_ix]
                if later_anno.start <= char_ix < later_anno.end:
                    is_overwritten = True
                    break
            
            if not is_overwritten and char_ix < len(text):
                assert anno_map[char_ix] == anno_ix, \
                    f"Character {char_ix} should map to annotation {anno_ix}, got {anno_map[char_ix]}"
    
    # Property 3: Characters outside all annotations should be None
    covered_indices = set()
    for anno in annotations:
        for i in range(anno.start, min(anno.end, len(text))):
            covered_indices.add(i)
    
    for i, val in enumerate(anno_map):
        if i not in covered_indices:
            assert val is None, f"Character {i} should not be annotated, but got {val}"


# Test 4: EncodingVisualizer HTML generation robustness
@given(
    st.text(max_size=100),
    st.lists(
        st.tuples(
            st.integers(min_value=0, max_value=100),
            st.integers(min_value=0, max_value=100),
            st.text(min_size=1, max_size=10)
        ),
        max_size=3
    )
)
@settings(max_examples=50)  # Limit examples since this involves tokenizer
def test_encoding_visualizer_html_generation(text, anno_data):
    """Test that EncodingVisualizer can generate HTML without crashing"""
    # Create a simple BPE tokenizer for testing
    from tokenizers import Tokenizer
    from tokenizers.models import BPE
    
    tokenizer = Tokenizer(BPE())
    
    # Create the visualizer
    visualizer = EncodingVisualizer(tokenizer, default_to_notebook=False)
    
    # Create valid annotations within text bounds
    annotations = []
    for start, end, label in anno_data:
        if len(text) > 0:
            start = min(max(0, start), len(text))
            end = min(max(0, end), len(text))
            if start > end:
                start, end = end, start
            annotations.append(Annotation(start, end, label))
    
    # Property: Should return HTML string without crashing
    result = visualizer(text, annotations, default_to_notebook=False)
    
    # Should return a string (HTML)
    assert isinstance(result, str), f"Expected string, got {type(result)}"
    
    # Should contain HTML tags
    assert "<html>" in result.lower(), "Result should contain HTML"
    assert "</html>" in result.lower(), "Result should contain closing HTML tag"
    
    # If there's text, it should appear in the HTML (unless it's all whitespace)
    if text and text.strip():
        # The text might be modified by tokenization, but some part should appear
        # We'll just check that the HTML has some content
        assert len(result) > 200, "HTML seems too short for non-empty text"


# Test 5: CharState multitoken property
@given(st.lists(st.integers(min_value=0, max_value=100)))
def test_charstate_multitoken_property(token_indices):
    """Test CharState.is_multitoken property correctly identifies multiple tokens"""
    cs = CharState(0)
    
    # Add tokens
    cs.tokens = token_indices
    
    # Property: is_multitoken should be True iff there are more than one token
    assert cs.is_multitoken == (len(token_indices) > 1)
    
    # Property: token_ix should return the first token or None
    if len(token_indices) > 0:
        assert cs.token_ix == token_indices[0]
    else:
        assert cs.token_ix is None


# Test 6: Test empty annotations edge case
def test_empty_annotations():
    """Test that calculate_label_colors handles empty annotations correctly"""
    # From line 165-166: if len(annotations) == 0: return {}
    result = EncodingVisualizer.calculate_label_colors([])
    assert result == {}, "Empty annotations should return empty color dict"


if __name__ == "__main__":
    # Run the tests
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])