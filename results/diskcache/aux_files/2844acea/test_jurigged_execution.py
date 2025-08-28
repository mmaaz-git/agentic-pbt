import sys
import os
import tempfile
import types
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import jurigged.runpy


# Test _run_code with different code types
def test_run_code_with_tuple_code():
    """Test _run_code when code is a tuple (before, after)."""
    code_before = compile("x = 1", "<test>", "exec")
    code_after = compile("y = 2", "<test>", "exec")
    
    run_globals = {}
    
    # Pass tuple of code objects
    result = jurigged.runpy._run_code(
        code=(code_before, code_after),
        run_globals=run_globals
    )
    
    assert result is run_globals
    assert 'x' in result
    assert 'y' in result
    assert result['x'] == 1
    assert result['y'] == 2


def test_run_code_with_prepare_callback():
    """Test _run_code with prepare callback."""
    code = compile("x = 1", "<test>", "exec")
    
    prepare_called = []
    
    def prepare(globals_dict):
        prepare_called.append(True)
        globals_dict['injected'] = 'from_prepare'
    
    run_globals = {}
    result = jurigged.runpy._run_code(
        code=code,
        run_globals=run_globals,
        prepare=prepare
    )
    
    assert prepare_called == [True]
    assert 'injected' in result
    assert result['injected'] == 'from_prepare'
    assert 'x' in result


def test_run_code_tuple_with_prepare():
    """Test _run_code with tuple code and prepare callback."""
    code_before = compile("x = 1", "<test>", "exec")
    code_after = compile("y = x + 1", "<test>", "exec")
    
    prepare_calls = []
    
    def prepare(globals_dict):
        prepare_calls.append(globals_dict.get('x'))
        globals_dict['z'] = 3
    
    run_globals = {}
    result = jurigged.runpy._run_code(
        code=(code_before, code_after),
        run_globals=run_globals,
        prepare=prepare
    )
    
    # Prepare should be called between before and after
    assert prepare_calls == [1]  # x should be 1 when prepare is called
    assert result['x'] == 1
    assert result['y'] == 2
    assert result['z'] == 3


# Test init_globals parameter
@given(st.dictionaries(
    st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=10),
    st.integers(),
    min_size=0,
    max_size=5
))
def test_run_code_init_globals(init_values):
    """Test that init_globals are properly merged."""
    code = compile("result = sum(globals().values()) if all(isinstance(v, int) for k, v in globals().items() if not k.startswith('__')) else 0", "<test>", "exec")
    
    run_globals = {}
    result = jurigged.runpy._run_code(
        code=code,
        run_globals=run_globals,
        init_globals=init_values
    )
    
    # All init values should be in result
    for key, value in init_values.items():
        assert key in result
        assert result[key] == value


# Test module metadata injection
def test_run_code_module_metadata():
    """Test that module metadata is properly injected."""
    code = compile("", "<test>", "exec")
    
    spec = types.SimpleNamespace(
        loader="test_loader",
        origin="/test/path.py",
        cached="/test/__pycache__/path.pyc",
        parent="test.package"
    )
    
    run_globals = {}
    result = jurigged.runpy._run_code(
        code=code,
        run_globals=run_globals,
        mod_name="test_module",
        mod_spec=spec,
        pkg_name="custom_package",
        script_name="/custom/script.py"
    )
    
    assert result['__name__'] == "test_module"
    assert result['__file__'] == "/test/path.py"  # From spec.origin
    assert result['__cached__'] == "/test/__pycache__/path.pyc"
    assert result['__loader__'] == "test_loader"
    assert result['__package__'] == "test.package"  # From spec.parent
    assert result['__spec__'] == spec


# Test error propagation
def test_run_code_error_propagation():
    """Test that errors in executed code are properly propagated."""
    code = compile("raise ValueError('test error')", "<test>", "exec")
    
    run_globals = {}
    
    try:
        jurigged.runpy._run_code(code, run_globals)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == "test error"


# Test complex code with imports
def test_run_code_with_imports():
    """Test _run_code with code that imports modules."""
    code = compile("""
import math
import json

data = {'pi': math.pi}
serialized = json.dumps(data)
""", "<test>", "exec")
    
    run_globals = {}
    result = jurigged.runpy._run_code(code, run_globals)
    
    assert 'math' in result
    assert 'json' in result
    assert 'data' in result
    assert 'serialized' in result
    
    import json
    deserialized = json.loads(result['serialized'])
    assert 'pi' in deserialized
    assert abs(deserialized['pi'] - 3.14159) < 0.001