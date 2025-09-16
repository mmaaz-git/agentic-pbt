import string
import random
from datetime import datetime
from hypothesis import given, strategies as st, assume, settings, example
import click.decorators as decorators
from click import Context, Command
from functools import update_wrapper


def transform_command_name(name):
    """Reproduce the command name transformation logic from click.decorators"""
    cmd_name = name.lower().replace("_", "-")
    cmd_left, sep, suffix = cmd_name.rpartition("-")
    if sep and suffix in {"command", "cmd", "group", "grp"}:
        cmd_name = cmd_left
    return cmd_name


@given(st.text(min_size=1))
def test_empty_name_after_suffix_removal(text):
    """Test what happens when suffix removal leaves empty string"""
    suffixes = ["command", "cmd", "group", "grp"]
    
    for suffix in suffixes:
        if text == suffix:
            result = transform_command_name(suffix)
            assert result == suffix
        
        if text == f"_{suffix}":
            result = transform_command_name(text)
            assert result == ""


@given(st.text(alphabet=string.ascii_letters + "_", min_size=1))
def test_decorator_double_application(func_name):
    """Test that applying command decorator twice raises TypeError"""
    assume(func_name.isidentifier())
    
    def dummy():
        pass
    dummy.__name__ = func_name
    
    cmd1 = decorators.command()(dummy)
    assert isinstance(cmd1, Command)
    
    try:
        cmd2 = decorators.command()(cmd1)
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "Attempted to convert a callback into a command twice" in str(e)


@given(st.text())
def test_name_with_special_chars(name):
    """Test command name handling with various special characters"""
    result = transform_command_name(name)
    
    assert "-" not in result or all(c != "_" for c in result)
    assert "_" not in result or all(c != "-" for c in result)


@given(st.lists(st.sampled_from(["_", "command", "cmd", "group", "grp"]), min_size=1, max_size=5))
def test_pathological_suffix_combinations(parts):
    """Test edge cases with suffix keywords"""
    name = "".join(parts)
    result = transform_command_name(name)
    
    if name == "cmd" or name == "command" or name == "group" or name == "grp":
        assert result == name
    
    if name.endswith("_cmd"):
        assert not result.endswith("-cmd")
    if name.endswith("_command"):
        assert not result.endswith("-command")


@given(st.text(min_size=1))
@example("")
@example("_")
@example("__")
@example("cmd")
@example("_cmd")
@example("__cmd")
def test_edge_case_empty_base_names(name):
    """Test edge cases that might produce empty command names"""
    result = transform_command_name(name)
    
    if name in ["_cmd", "_command", "_grp", "_group"]:
        assert result == ""
    elif name in ["cmd", "command", "grp", "group"]:
        assert result == name
    elif name == "__cmd":
        assert result == "-"
    elif name == "__command":
        assert result == "-"


@given(st.integers(min_value=1, max_value=100))
def test_deeply_nested_underscores(depth):
    """Test names with many consecutive underscores"""
    name = "_" * depth + "test"
    result = transform_command_name(name)
    expected = "-" * depth + "test"
    assert result == expected
    
    name_with_suffix = "_" * depth + "cmd"
    result_suffix = transform_command_name(name_with_suffix)
    if depth == 1:
        assert result_suffix == ""
    else:
        assert result_suffix == "-" * (depth - 1)


@given(st.text(alphabet=string.ascii_letters + "_", min_size=1).filter(lambda x: x.isidentifier()))
def test_pass_context_wrapper_updates(func_name):
    """Test that pass_context properly uses update_wrapper"""
    def original(ctx):
        """Original doc"""
        return 42
    
    original.__name__ = func_name
    original.__module__ = "test_module"
    original.__qualname__ = f"TestClass.{func_name}"
    original.__annotations__ = {"ctx": Context, "return": int}
    
    decorated = decorators.pass_context(original)
    
    assert decorated.__name__ == func_name
    assert decorated.__doc__ == "Original doc"
    assert decorated.__module__ == "test_module"
    assert decorated.__qualname__ == f"TestClass.{func_name}"
    assert hasattr(decorated, "__wrapped__")
    assert decorated.__wrapped__ is original


@given(st.text(min_size=1, alphabet=string.printable))
def test_unicode_and_special_chars_in_names(text):
    """Test that transformation handles all characters gracefully"""
    try:
        result = transform_command_name(text)
        assert isinstance(result, str)
        
        for char in result:
            assert char != "_" or "-" not in result
            assert char != "-" or "_" not in result
    except Exception as e:
        assert False, f"Transformation failed on input {text!r}: {e}"


@given(st.text(alphabet=string.ascii_letters, min_size=1))
def test_option_and_argument_decorator_accumulation(base_name):
    """Test that multiple option/argument decorators accumulate correctly"""
    assume(base_name.isidentifier())
    
    def func():
        pass
    func.__name__ = base_name
    
    decorated = decorators.option("--opt1")(func)
    decorated = decorators.option("--opt2")(decorated)
    decorated = decorators.argument("arg1")(decorated)
    
    assert hasattr(decorated, "__click_params__")
    assert len(decorated.__click_params__) == 3
    
    cmd = decorators.command()(decorated)
    assert len(cmd.params) == 3


@given(st.text(min_size=1).filter(lambda x: x and not x.isspace()))
def test_command_name_never_empty_with_valid_input(func_name):
    """Test that valid function names never produce empty command names"""
    assume(func_name not in ["_cmd", "_command", "_grp", "_group"])
    
    result = transform_command_name(func_name)
    
    if func_name.strip("_") in ["cmd", "command", "grp", "group"] and func_name.startswith("_") and func_name.count("_") == 1:
        assert result == ""
    else:
        assert result or func_name in ["_cmd", "_command", "_grp", "_group"]