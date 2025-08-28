import string
import random
from datetime import datetime
from hypothesis import given, strategies as st, assume, settings, example
import click.decorators as decorators
from click import Context, Command, Option, Argument
from unittest.mock import Mock, patch


@given(st.text(min_size=1))
@example("_cmd")
@example("_command") 
@example("_grp")
@example("_group")
def test_empty_command_name_creation(func_name):
    """Test that certain function names create commands with empty names"""
    
    def dummy():
        pass
    dummy.__name__ = func_name
    
    cmd = decorators.command()(dummy)
    
    if func_name in ["_cmd", "_command", "_grp", "_group"]:
        assert cmd.name == ""


@given(st.text(alphabet=string.ascii_letters + "_", min_size=1))
def test_command_name_stripping_not_recursive(base):
    """Test that suffix stripping is not recursive"""
    assume(base and not base.endswith("_"))
    
    # Build a name with nested suffixes
    name = f"{base}_command_cmd"
    
    def dummy():
        pass
    dummy.__name__ = name
    
    cmd = decorators.command()(dummy)
    
    # Should only strip the last suffix
    expected = f"{base}-command".lower()
    assert cmd.name == expected


@given(st.lists(st.sampled_from(["option", "argument"]), min_size=1, max_size=10))
def test_decorator_params_reversed_order(decorator_types):
    """Test that params are added in reversed order to maintain decoration order"""
    
    def base():
        pass
    
    func = base
    param_names = []
    
    for i, dtype in enumerate(decorator_types):
        if dtype == "option":
            param_name = f"--opt{i}"
            func = decorators.option(param_name)(func)
        else:
            param_name = f"arg{i}"
            func = decorators.argument(param_name)(func)
        param_names.append((dtype, param_name))
    
    cmd = decorators.command()(func)
    
    # Params should be in the same order as decoration (reversed internally)
    assert len(cmd.params) == len(param_names)
    
    for i, param in enumerate(cmd.params):
        dtype, expected_name = param_names[i]
        if dtype == "option":
            assert isinstance(param, Option)
        else:
            assert isinstance(param, Argument)


@given(st.text(min_size=1))
def test_version_option_missing_version_error(package_name):
    """Test version_option behavior when version cannot be determined"""
    
    def dummy():
        pass
    
    # Test with a non-existent package
    decorator = decorators.version_option(package_name="nonexistent_package_12345")
    decorated = decorator(dummy)
    
    # Create a mock context
    ctx = Mock(spec=Context)
    ctx.resilient_parsing = False
    ctx.color = False
    ctx.find_root = Mock(return_value=Mock(info_name="test"))
    
    param = Mock()
    
    # This should raise a RuntimeError
    try:
        decorated.__click_params__[-1].callback(ctx, param, True)
        assert False, "Should have raised RuntimeError"
    except RuntimeError as e:
        assert "is not installed" in str(e)


@given(st.text(alphabet=string.ascii_letters, min_size=1).filter(lambda x: x.isidentifier()))
def test_pass_obj_with_none_context_obj(func_name):
    """Test pass_obj when context.obj is None"""
    
    def original(obj, x):
        return obj, x
    
    original.__name__ = func_name
    decorated = decorators.pass_obj(original)
    
    with patch('click.decorators.get_current_context') as mock_get_ctx:
        mock_ctx = Mock(spec=Context)
        mock_ctx.obj = None
        mock_get_ctx.return_value = mock_ctx
        
        result = decorated(42)
        assert result == (None, 42)


@given(st.text(min_size=1))
def test_pass_meta_key_missing_key_runtime_error(key):
    """Test pass_meta_key raises KeyError when key is missing"""
    assume(key)
    
    decorator = decorators.pass_meta_key(key)
    
    def test_func(value, x):
        return value, x
    
    decorated = decorator(test_func)
    
    with patch('click.decorators.get_current_context') as mock_get_ctx:
        mock_ctx = Mock(spec=Context)
        mock_ctx.meta = {}
        mock_ctx.invoke = lambda f, *args, **kwargs: f(*args, **kwargs)
        mock_get_ctx.return_value = mock_ctx
        
        try:
            result = decorated(42)
            assert False, "Should have raised KeyError"
        except KeyError:
            pass


@given(st.text(min_size=2))
def test_double_underscore_produces_double_dash(text):
    """Test that consecutive underscores become consecutive dashes"""
    assume("_" in text)
    
    name = text.replace("-", "_")  # Ensure we only have underscores
    
    def dummy():
        pass
    dummy.__name__ = name
    
    cmd = decorators.command()(dummy)
    
    # Count consecutive underscores and dashes
    max_underscores = 0
    current_underscores = 0
    for char in name:
        if char == "_":
            current_underscores += 1
            max_underscores = max(max_underscores, current_underscores)
        else:
            current_underscores = 0
    
    max_dashes = 0
    current_dashes = 0
    for char in cmd.name:
        if char == "-":
            current_dashes += 1
            max_dashes = max(max_dashes, current_dashes)
        else:
            current_dashes = 0
    
    # Unless it's a suffix that gets stripped
    if not name.endswith(("_cmd", "_command", "_grp", "_group")):
        if max_underscores > 0:
            assert max_dashes == max_underscores


@given(st.text(alphabet=string.ascii_letters + "_", min_size=1).filter(lambda x: x.isidentifier()))
def test_make_pass_decorator_without_object_raises(class_name):
    """Test make_pass_decorator raises RuntimeError when object not found"""
    
    class TestClass:
        pass
    
    TestClass.__name__ = class_name
    
    pass_test = decorators.make_pass_decorator(TestClass, ensure=False)
    
    def dummy(obj):
        return obj
    
    decorated = pass_test(dummy)
    
    with patch('click.decorators.get_current_context') as mock_get_ctx:
        mock_ctx = Mock(spec=Context)
        mock_ctx.find_object = Mock(return_value=None)
        mock_ctx.invoke = lambda f, *args, **kwargs: f(*args, **kwargs)
        mock_get_ctx.return_value = mock_ctx
        
        try:
            result = decorated()
            assert False, f"Should have raised RuntimeError"
        except RuntimeError as e:
            assert "without a context object" in str(e)
            assert class_name in str(e)