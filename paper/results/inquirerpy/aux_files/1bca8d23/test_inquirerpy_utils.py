"""Property-based tests for InquirerPy.utils module."""

import math
import os
import shutil
from unittest.mock import patch

from hypothesis import assume, given, settings, strategies as st
from InquirerPy.exceptions import InvalidArgument
from InquirerPy.utils import InquirerPyStyle, calculate_height, get_style


@given(
    style=st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.text(min_size=0, max_size=50),
        min_size=0,
        max_size=10,
    )
)
def test_get_style_always_returns_inquirerpy_style(style):
    """get_style should always return an InquirerPyStyle instance."""
    result = get_style(style)
    assert isinstance(result, InquirerPyStyle)
    assert hasattr(result, "dict")
    assert isinstance(result.dict, dict)


@given(
    style=st.dictionaries(
        st.sampled_from(["fuzzy_border", "validator", "other_key"]),
        st.text(min_size=1, max_size=20),
        min_size=1,
        max_size=3,
    )
)
def test_get_style_key_renaming(style):
    """get_style should rename specific keys according to documented behavior."""
    result = get_style(style, style_override=True)
    
    # Check fuzzy_border -> frame.border renaming
    if "fuzzy_border" in style:
        assert "fuzzy_border" not in result.dict
        assert "frame.border" in result.dict
        assert result.dict["frame.border"] == style["fuzzy_border"]
    
    # Check validator -> validation-toolbar renaming
    if "validator" in style:
        assert "validator" not in result.dict
        assert "validation-toolbar" in result.dict
        assert result.dict["validation-toolbar"] == style["validator"]
    
    # bottom-toolbar should always be set
    assert result.dict["bottom-toolbar"] == "noreverse"


@given(
    base_style=st.dictionaries(
        st.sampled_from(["answer", "question", "input"]),
        st.text(min_size=1, max_size=20),
        min_size=1,
        max_size=3,
    ),
    override_style=st.dictionaries(
        st.sampled_from(["answer", "question", "input", "pointer"]),
        st.text(min_size=1, max_size=20),
        min_size=1,
        max_size=3,
    ),
)
def test_get_style_override_behavior(base_style, override_style):
    """Test style_override parameter merging vs overriding behavior."""
    # When style_override=False, styles should merge with defaults
    result_merge = get_style(override_style, style_override=False)
    
    # When style_override=True, only provided styles should be present (plus bottom-toolbar)
    result_override = get_style(override_style, style_override=True)
    
    # Merged result should have both default keys and provided keys
    for key in override_style:
        if key not in ["fuzzy_border", "validator"]:
            assert key in result_merge.dict
            assert result_merge.dict[key] == override_style[key]
    
    # Override result should have empty strings for non-provided standard keys
    standard_keys = ["questionmark", "answermark", "answer", "input", "question"]
    for key in standard_keys:
        if key not in override_style:
            assert result_override.dict[key] == ""


@given(
    height_percent=st.integers(min_value=1, max_value=200),
    max_height_percent=st.integers(min_value=1, max_value=200),
    term_lines=st.integers(min_value=10, max_value=1000),
)
def test_calculate_height_percentage_calculation(height_percent, max_height_percent, term_lines):
    """Test that percentage strings are correctly converted to line counts."""
    with patch("shutil.get_terminal_size") as mock_size:
        mock_size.return_value = (80, term_lines)
        
        height_str = f"{height_percent}%"
        max_height_str = f"{max_height_percent}%"
        
        result_height, result_max_height = calculate_height(
            height_str, max_height_str, height_offset=2
        )
        
        expected_height = math.floor(term_lines * (height_percent / 100)) - 2
        expected_max_height = math.floor(term_lines * (max_height_percent / 100)) - 2
        
        # Height should be clamped to max_height if greater
        if expected_height > expected_max_height:
            expected_height = expected_max_height
        
        # Heights should be at least 1
        if expected_height <= 0:
            expected_height = 1
        if expected_max_height <= 0:
            expected_max_height = 1
        
        assert result_height == expected_height
        assert result_max_height == expected_max_height


@given(
    height=st.one_of(
        st.integers(min_value=-100, max_value=500),
        st.text(min_size=1, max_size=5).filter(lambda x: x.replace("%", "").isdigit()),
    ),
    max_height=st.one_of(
        st.integers(min_value=-100, max_value=500),
        st.text(min_size=1, max_size=5).filter(lambda x: x.replace("%", "").isdigit()),
    ),
)
def test_calculate_height_clamping_invariants(height, max_height):
    """Test that calculate_height maintains clamping invariants."""
    with patch("shutil.get_terminal_size") as mock_size:
        mock_size.return_value = (80, 100)
        
        result_height, result_max_height = calculate_height(height, max_height)
        
        # Invariant 1: Heights should never be <= 0
        if result_height is not None:
            assert result_height >= 1
        assert result_max_height >= 1
        
        # Invariant 2: Height should never exceed max_height
        if result_height is not None:
            assert result_height <= result_max_height


@given(
    height=st.one_of(
        st.none(),
        st.integers(min_value=1, max_value=100),
        st.text(min_size=1, max_size=4).map(lambda x: f"{x}%"),
    ),
    max_height=st.none(),
)
def test_calculate_height_default_max_height(height):
    """Test default max_height behavior when not provided."""
    with patch("shutil.get_terminal_size") as mock_size:
        mock_size.return_value = (80, 100)
        
        result_height, result_max_height = calculate_height(height, max_height=None)
        
        # According to docstring: max_height defaults to 70% if height is None, else 100%
        if height is None:
            expected_max = math.floor(100 * 0.7) - 2
        else:
            expected_max = math.floor(100 * 1.0) - 2
        
        if expected_max <= 0:
            expected_max = 1
            
        assert result_max_height == expected_max


@given(
    invalid_height=st.text(min_size=1, max_size=10).filter(
        lambda x: not x.replace("%", "").replace("-", "").isdigit()
    )
)
def test_calculate_height_invalid_input_raises_exception(invalid_height):
    """Test that invalid height values raise InvalidArgument exception."""
    with patch("shutil.get_terminal_size") as mock_size:
        mock_size.return_value = (80, 100)
        
        try:
            calculate_height(invalid_height, None)
            assert False, "Should have raised InvalidArgument"
        except InvalidArgument as e:
            assert "height/max_height needs to be type of an int or str" in str(e)


@given(
    height_int=st.integers(min_value=1, max_value=50),
    max_height_int=st.integers(min_value=1, max_value=50),
)
def test_calculate_height_integer_input(height_int, max_height_int):
    """Test that integer inputs are handled correctly without percentage calculation."""
    with patch("shutil.get_terminal_size") as mock_size:
        mock_size.return_value = (80, 100)
        
        result_height, result_max_height = calculate_height(height_int, max_height_int)
        
        # When inputs are integers, they should be used directly (with clamping)
        expected_height = min(height_int, max_height_int)
        assert result_height == expected_height
        assert result_max_height == max_height_int