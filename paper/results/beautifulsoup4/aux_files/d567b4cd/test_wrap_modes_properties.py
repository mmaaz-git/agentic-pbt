import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

import re
from hypothesis import given, strategies as st, assume, settings
import isort.wrap_modes as wrap_modes


@given(st.lists(st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cs", "Cc", "Cn"]))))
def test_non_emptiness_invariant(imports_list):
    """Test that wrap mode functions return empty string iff imports is empty."""
    interface = {
        "statement": "from module import ",
        "imports": imports_list.copy(),
        "white_space": "    ",
        "indent": "    ",
        "line_length": 80,
        "comments": [],
        "line_separator": "\n",
        "comment_prefix": " #",
        "include_trailing_comma": False,
        "remove_comments": False,
    }
    
    for formatter_name in wrap_modes._wrap_modes:
        if formatter_name == "VERTICAL_GRID_GROUPED_NO_COMMA":
            continue
        formatter = wrap_modes._wrap_modes[formatter_name]
        result = formatter(**interface.copy())
        
        if not imports_list:
            assert result == "", f"{formatter_name} should return empty string for empty imports"
        else:
            assert len(result) > 0, f"{formatter_name} should return non-empty string for non-empty imports"


@given(st.integers(0, 12))
def test_from_string_with_integers(mode_int):
    """Test from_string works with integer strings."""
    mode = wrap_modes.from_string(str(mode_int))
    assert mode.value == mode_int


@given(st.sampled_from(list(wrap_modes._wrap_modes.keys())))
def test_from_string_with_mode_names(mode_name):
    """Test from_string works with mode names."""
    if mode_name == "VERTICAL_GRID_GROUPED_NO_COMMA":
        return
    mode = wrap_modes.from_string(mode_name)
    assert mode.name == mode_name


@given(st.text())
def test_formatter_from_string_always_returns_callable(name):
    """Test that formatter_from_string always returns a callable."""
    formatter = wrap_modes.formatter_from_string(name)
    assert callable(formatter)
    
    if name.upper() in wrap_modes._wrap_modes and name.upper() != "VERTICAL_GRID_GROUPED_NO_COMMA":
        assert formatter == wrap_modes._wrap_modes[name.upper()]
    else:
        assert formatter == wrap_modes.grid


@given(
    st.lists(
        st.text(min_size=1, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters="\n\r")),
        min_size=1,
        max_size=10
    )
)
def test_no_data_loss_in_formatting(imports_list):
    """Test that all import names appear in the formatted output."""
    interface = {
        "statement": "from module import ",
        "imports": imports_list.copy(),
        "white_space": "    ",
        "indent": "    ",
        "line_length": 80,
        "comments": [],
        "line_separator": "\n",
        "comment_prefix": " #",
        "include_trailing_comma": False,
        "remove_comments": False,
    }
    
    for formatter_name in wrap_modes._wrap_modes:
        if formatter_name == "VERTICAL_GRID_GROUPED_NO_COMMA":
            continue
        formatter = wrap_modes._wrap_modes[formatter_name]
        result = formatter(**interface.copy())
        
        for import_name in imports_list:
            escaped_name = re.escape(import_name)
            assert re.search(escaped_name, result), f"{formatter_name} lost import '{import_name}'"


@given(
    st.lists(
        st.text(min_size=1, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters="\n\r()")),
        min_size=1,
        max_size=10
    )
)
def test_balanced_parentheses(imports_list):
    """Test that formatters produce balanced parentheses."""
    interface = {
        "statement": "from module import ",
        "imports": imports_list.copy(),
        "white_space": "    ",
        "indent": "    ",
        "line_length": 80,
        "comments": [],
        "line_separator": "\n",
        "comment_prefix": " #",
        "include_trailing_comma": False,
        "remove_comments": False,
    }
    
    for formatter_name in wrap_modes._wrap_modes:
        if formatter_name == "VERTICAL_GRID_GROUPED_NO_COMMA":
            continue
        formatter = wrap_modes._wrap_modes[formatter_name]
        result = formatter(**interface.copy())
        
        open_count = result.count('(')
        close_count = result.count(')')
        assert open_count == close_count, f"{formatter_name} has unbalanced parentheses: {open_count} open, {close_count} close"


@given(
    st.lists(st.text(min_size=1, max_size=100, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters="\n\r")), min_size=1, max_size=20),
    st.integers(min_value=10, max_value=200),
    st.booleans()
)
@settings(max_examples=100)
def test_formatters_dont_crash(imports_list, line_length, include_trailing_comma):
    """Test that formatters don't crash on various inputs."""
    interface = {
        "statement": "from module import ",
        "imports": imports_list.copy(),
        "white_space": "    ",
        "indent": "    ",
        "line_length": line_length,
        "comments": [],
        "line_separator": "\n",
        "comment_prefix": " #",
        "include_trailing_comma": include_trailing_comma,
        "remove_comments": False,
    }
    
    for formatter_name in wrap_modes._wrap_modes:
        if formatter_name == "VERTICAL_GRID_GROUPED_NO_COMMA":
            continue
        formatter = wrap_modes._wrap_modes[formatter_name]
        try:
            result = formatter(**interface.copy())
            assert isinstance(result, str)
        except Exception as e:
            raise AssertionError(f"{formatter_name} crashed with {e}")


@given(
    st.lists(st.text(min_size=1, alphabet="abcdefghijklmnopqrstuvwxyz_"), min_size=1, max_size=5),
    st.lists(st.text(min_size=1, max_size=30, alphabet=st.characters(min_codepoint=32, max_codepoint=126, blacklist_characters="\n\r")), max_size=3)
)
def test_comments_preserved(imports_list, comments_list):
    """Test that comments are preserved in output when not removed."""
    interface = {
        "statement": "from module import ",
        "imports": imports_list.copy(),
        "white_space": "    ",
        "indent": "    ",
        "line_length": 80,
        "comments": comments_list.copy(),
        "line_separator": "\n",
        "comment_prefix": " #",
        "include_trailing_comma": False,
        "remove_comments": False,
    }
    
    for formatter_name in ["GRID", "VERTICAL", "HANGING_INDENT", "NOQA"]:
        formatter = wrap_modes._wrap_modes[formatter_name]
        result = formatter(**interface.copy())
        
        if comments_list and not interface["remove_comments"]:
            for comment in comments_list:
                if comment:
                    assert comment in result or "NOQA" in result, f"{formatter_name} should preserve comment '{comment}' or add NOQA"