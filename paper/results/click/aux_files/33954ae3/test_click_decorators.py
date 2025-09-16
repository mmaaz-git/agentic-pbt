import string
import random
from datetime import datetime
from hypothesis import given, strategies as st, assume, settings
import click.decorators as decorators
from click import Context


def transform_command_name(name):
    """Reproduce the command name transformation logic from click.decorators"""
    cmd_name = name.lower().replace("_", "-")
    cmd_left, sep, suffix = cmd_name.rpartition("-")
    if sep and suffix in {"command", "cmd", "group", "grp"}:
        cmd_name = cmd_left
    return cmd_name


@given(st.text(min_size=1, alphabet=string.ascii_letters + string.digits + "_"))
def test_command_name_transformation_idempotent(name):
    """Test that command name transformation is idempotent"""
    first = transform_command_name(name)
    second = transform_command_name(first.replace("-", "_"))
    assert first == second


@given(st.text(min_size=1, alphabet=string.ascii_letters + string.digits + "_"))
def test_command_suffix_stripping_property(base_name):
    """Test that suffix stripping only affects the end of the name"""
    assume(not base_name.endswith("_"))
    
    suffixes = ["command", "cmd", "group", "grp"]
    
    for suffix in suffixes:
        name_with_suffix = f"{base_name}_{suffix}"
        transformed = transform_command_name(name_with_suffix)
        expected = base_name.lower().replace("_", "-")
        assert transformed == expected
        
        name_with_middle_suffix = f"{suffix}_{base_name}"
        transformed_middle = transform_command_name(name_with_middle_suffix)
        expected_middle = f"{suffix}-{base_name}".lower().replace("_", "-")
        assert transformed_middle == expected_middle


@given(st.text(min_size=1, alphabet=string.ascii_letters + string.digits + "_"))
def test_edge_case_suffix_only_names(name):
    """Test names that are only the suffix keywords"""
    suffixes = ["command", "cmd", "group", "grp"]
    
    for suffix in suffixes:
        result = transform_command_name(suffix)
        assert result == suffix
        
        double_suffix = f"{suffix}_{suffix}"
        result_double = transform_command_name(double_suffix)
        assert result_double == suffix


@given(st.text(min_size=1, alphabet=string.ascii_letters + string.digits + "_"))
def test_command_decorator_name_consistency(func_name):
    """Test that command decorator creates commands with expected names"""
    assume(func_name.isidentifier())
    
    def dummy_func():
        pass
    dummy_func.__name__ = func_name
    
    cmd = decorators.command()(dummy_func)
    expected_name = transform_command_name(func_name)
    assert cmd.name == expected_name


@given(st.text(min_size=1, alphabet=string.ascii_letters))
def test_explicit_name_overrides_function_name(explicit_name):
    """Test that explicit names override function names"""
    assume(not any(c in explicit_name for c in "(){}[]"))
    
    def test_function():
        pass
    
    cmd = decorators.command(name=explicit_name)(test_function)
    assert cmd.name == explicit_name


@given(st.text(min_size=1).filter(lambda x: x.isidentifier()))
def test_pass_decorator_preserves_metadata(func_name):
    """Test that pass_context preserves function metadata"""
    
    def original_func(ctx):
        """Test docstring"""
        return 42
    
    original_func.__name__ = func_name
    decorated = decorators.pass_context(original_func)
    
    assert decorated.__name__ == func_name
    assert decorated.__doc__ == "Test docstring"


@given(st.text(min_size=1, alphabet=string.ascii_letters + "_"))
def test_command_decorator_with_multiple_suffixes(base_name):
    """Test command names with multiple suffix keywords"""
    assume(base_name and not base_name.endswith("_"))
    
    multi_suffix_names = [
        f"{base_name}_command_cmd",
        f"{base_name}_cmd_command",
        f"{base_name}_group_grp",
        f"{base_name}_grp_group",
    ]
    
    for name in multi_suffix_names:
        result = transform_command_name(name)
        if name.endswith("_cmd"):
            expected = transform_command_name(name[:-4])
        elif name.endswith("_command"):
            expected = transform_command_name(name[:-8])
        elif name.endswith("_grp"):
            expected = transform_command_name(name[:-4])
        elif name.endswith("_group"):
            expected = transform_command_name(name[:-6])
        else:
            expected = name.lower().replace("_", "-")
        assert result == expected


@given(st.text(min_size=1, alphabet=string.ascii_letters + string.digits + "_"))
def test_command_chaining_suffix_removal(base_name):
    """Test that suffix removal works correctly when there are chains"""
    assume(not base_name.endswith("_") and base_name)
    
    name_chain = f"{base_name}_cmd_cmd"
    result = transform_command_name(name_chain)
    
    expected = f"{base_name}-cmd".lower().replace("_", "-")
    assert result == expected


@given(st.integers(min_value=0, max_value=10))
def test_underscore_preservation_in_transform(underscore_count):
    """Test how multiple underscores are handled"""
    name = "test" + "_" * underscore_count + "name"
    result = transform_command_name(name)
    expected_dashes = "-" * underscore_count if underscore_count else ""
    expected = f"test{expected_dashes}name" if underscore_count else "testname"
    assert result == expected