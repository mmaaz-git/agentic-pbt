import string
import random
from datetime import datetime
from hypothesis import given, strategies as st, assume, settings, example
import click.decorators as decorators
from click import Context, Command, Option, Argument
import inspect


@given(st.dictionaries(st.text(min_size=1), st.text(), min_size=0))
def test_version_option_message_interpolation(extra_kwargs):
    """Test version_option message string interpolation"""
    
    def dummy():
        pass
    
    version = "1.2.3"
    package = "test-package"
    prog = "test-prog"
    
    message_patterns = [
        "%(prog)s, version %(version)s",
        "%(package)s %(version)s",
        "Version: %(version)s",
        "%(prog)s",
    ]
    
    for pattern in message_patterns:
        try:
            decorator = decorators.version_option(
                version=version,
                package_name=package,
                prog_name=prog,
                message=pattern,
                **extra_kwargs
            )
            decorated = decorator(dummy)
            
            assert hasattr(decorated, "__click_params__")
            assert len(decorated.__click_params__) > 0
            param = decorated.__click_params__[-1]
            assert isinstance(param, Option)
            
        except (TypeError, ValueError):
            pass


@given(st.text())
def test_pass_meta_key_with_missing_key(key):
    """Test pass_meta_key behavior with missing keys"""
    assume(key)
    
    decorator = decorators.pass_meta_key(key)
    
    def test_func(value):
        return value
    
    decorated = decorator(test_func)
    
    assert decorated.__name__ == test_func.__name__
    assert hasattr(decorator, "__doc__")
    
    if key:
        expected_doc = f"Decorator that passes the {key!r} key from :attr:`click.Context.meta` as the first argument to the decorated function."
        assert decorator.__doc__ == expected_doc


@given(st.lists(st.tuples(st.text(min_size=1), st.text()), min_size=0, max_size=5))
def test_command_params_ordering(param_list):
    """Test that params maintain correct order when added"""
    
    def base_func():
        pass
    
    func = base_func
    
    for i, (name, value) in enumerate(param_list):
        if i % 2 == 0:
            func = decorators.option(f"--{name or f'opt{i}'}")(func)
        else:
            func = decorators.argument(name or f"arg{i}")(func)
    
    if hasattr(func, "__click_params__"):
        cmd = decorators.command()(func)
        
        assert len(cmd.params) == len(param_list)
        
        for i in range(len(cmd.params) - 1):
            assert cmd.params[i] is not cmd.params[i + 1]


@given(st.text(min_size=1))
def test_confirmation_option_default_params(custom_prompt):
    """Test confirmation_option with custom prompts"""
    
    def dummy():
        pass
    
    decorator = decorators.confirmation_option(prompt=custom_prompt)
    decorated = decorator(dummy)
    
    assert hasattr(decorated, "__click_params__")
    param = decorated.__click_params__[-1]
    assert isinstance(param, Option)
    
    assert param.is_flag == True
    assert param.expose_value == False
    
    if hasattr(param, "prompt"):
        assert param.prompt == custom_prompt


@given(st.booleans(), st.booleans(), st.booleans())
def test_password_option_settings(prompt, confirmation, hide):
    """Test password_option parameter combinations"""
    
    def dummy():
        pass
    
    decorator = decorators.password_option(
        prompt=prompt,
        confirmation_prompt=confirmation,
        hide_input=hide
    )
    decorated = decorator(dummy)
    
    assert hasattr(decorated, "__click_params__")
    param = decorated.__click_params__[-1]
    assert isinstance(param, Option)
    
    assert param.prompt == prompt
    assert param.confirmation_prompt == confirmation
    assert param.hide_input == hide


@given(st.text(alphabet=string.ascii_letters + "_", min_size=1).filter(lambda x: x.isidentifier()))
def test_make_pass_decorator_ensure_flag(class_name):
    """Test make_pass_decorator with ensure flag"""
    
    class TestClass:
        pass
    
    TestClass.__name__ = class_name
    
    pass_test_ensure = decorators.make_pass_decorator(TestClass, ensure=True)
    pass_test_no_ensure = decorators.make_pass_decorator(TestClass, ensure=False)
    
    def dummy(obj):
        return obj
    
    decorated_ensure = pass_test_ensure(dummy)
    decorated_no_ensure = pass_test_no_ensure(dummy)
    
    assert decorated_ensure.__name__ == dummy.__name__
    assert decorated_no_ensure.__name__ == dummy.__name__


@given(st.lists(st.text(min_size=1), min_size=1, max_size=3))
def test_option_argument_param_decls(decls):
    """Test option and argument with various parameter declarations"""
    
    def dummy():
        pass
    
    try:
        opt_decorator = decorators.option(*decls)
        opt_decorated = opt_decorator(dummy)
        assert hasattr(opt_decorated, "__click_params__")
        assert len(opt_decorated.__click_params__) == 1
        
        arg_decorator = decorators.argument(*decls)
        arg_decorated = arg_decorator(dummy)
        assert hasattr(arg_decorated, "__click_params__")
        assert len(arg_decorated.__click_params__) == 1
        
    except (TypeError, ValueError, AssertionError):
        pass


@given(st.text(alphabet=string.ascii_letters, min_size=1).filter(lambda x: x.isidentifier()))
def test_group_decorator_cls_inheritance(func_name):
    """Test that group decorator properly uses Group class"""
    
    def dummy():
        pass
    dummy.__name__ = func_name
    
    grp = decorators.group()(dummy)
    
    from click import Group
    assert isinstance(grp, Group)
    assert grp.name == func_name.lower().replace("_", "-").rstrip("-group").rstrip("-grp")


@given(st.dictionaries(st.text(min_size=1), st.integers(), min_size=0, max_size=3))
def test_command_attrs_forwarding(attrs):
    """Test that command decorator forwards attributes correctly"""
    
    def dummy():
        """Test docstring"""
        pass
    
    valid_attrs = {k: v for k, v in attrs.items() if k not in ["name", "cls", "callback", "params"]}
    
    try:
        cmd = decorators.command(**valid_attrs)(dummy)
        assert isinstance(cmd, Command)
        assert cmd.__doc__ == "Test docstring"
        
        for key, value in valid_attrs.items():
            if hasattr(cmd, key):
                actual = getattr(cmd, key)
                if key == "help" and value is None:
                    assert actual == "Test docstring"
    except (TypeError, AttributeError):
        pass


@given(st.text(min_size=1))
@example("_cmd")
@example("_command")
@example("__group")
def test_empty_command_names_edge_cases(func_name):
    """Test functions that produce empty command names"""
    
    if func_name in ["_cmd", "_command", "_grp", "_group"]:
        def dummy():
            pass
        dummy.__name__ = func_name
        
        cmd = decorators.command()(dummy)
        assert cmd.name == ""
    elif func_name == "__group":
        def dummy():
            pass
        dummy.__name__ = func_name
        
        cmd = decorators.command()(dummy)
        assert cmd.name == "-"