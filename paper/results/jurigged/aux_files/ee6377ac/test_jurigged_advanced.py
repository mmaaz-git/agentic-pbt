import sys
import os
import tempfile
from pathlib import Path
import importlib.util
import uuid
from types import ModuleType

sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, note
from hypothesis.strategies import composite
import pytest
from jurigged.register import Registry, ImportSniffer, add_sniffer, _sniffer_callbacks
from jurigged.utils import glob_filter


@composite
def valid_glob_pattern(draw):
    """Generate valid glob patterns."""
    patterns = [
        "./*.py",
        "**/*.py", 
        "*.txt",
        "**/test_*.py",
        "src/**/*.py",
        "[!_]*.py",
        "test_[0-9]*.py"
    ]
    return draw(st.sampled_from(patterns))


@given(valid_glob_pattern())
@settings(max_examples=20)
def test_auto_register_with_filters(pattern):
    """Test auto_register with different glob filters."""
    reg = Registry()
    
    # Create filter
    filter_func = glob_filter(pattern)
    
    # Run auto_register
    sniffer = reg.auto_register(filter=filter_func)
    
    # Verify sniffer was added
    assert sniffer in _sniffer_callbacks, "Sniffer not added to callbacks"
    
    # Clean up
    sniffer.uninstall()
    assert sniffer not in _sniffer_callbacks, "Sniffer not removed after uninstall"


@given(st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=5))
@settings(max_examples=20)
def test_import_sniffer_multiple_callbacks(callback_ids):
    """Test ImportSniffer with multiple callbacks."""
    reg = Registry()
    callbacks_called = []
    
    def make_callback(id):
        def callback(module_name, filename):
            callbacks_called.append((id, module_name, filename))
        return callback
    
    # Add multiple callbacks
    sniffers = []
    for id in callback_ids:
        cb = make_callback(id)
        sniffer = add_sniffer(cb)
        sniffers.append(sniffer)
    
    # Create a test module spec
    spec = importlib.util.spec_from_file_location(
        "test_module",
        __file__  # Use this test file as the module file
    )
    
    # The sniffer should not do anything if not working
    import_sniffer = ImportSniffer()
    result = import_sniffer.find_spec("test_module", None)
    assert result is None, "ImportSniffer should return None"
    
    # Clean up
    for sniffer in sniffers:
        sniffer.uninstall()


@given(st.dictionaries(
    st.text(min_size=1, max_size=20),  # module names
    st.text(min_size=1, max_size=100),  # filenames
    min_size=0,
    max_size=10
))
@settings(max_examples=20)
def test_filename_to_module_cache_consistency(mappings):
    """Test that filename_to_module cache remains consistent."""
    reg = Registry()
    
    # Manually populate filename_to_module
    for module_name, filename in mappings.items():
        reg.filename_to_module[filename] = module_name
    
    # Verify all mappings are preserved
    for filename, module_name in reg.filename_to_module.items():
        assert isinstance(module_name, str), "Module name should be a string"
        assert isinstance(filename, str), "Filename should be a string"
    
    # Test that prepare with filename uses the cache
    for filename, expected_module in mappings.items():
        # Mock the module in sys.modules
        if expected_module not in sys.modules:
            # Create a minimal module
            module = type(sys)('test_module')
            module.__file__ = filename
            module.__name__ = expected_module
            sys.modules[expected_module] = module
            
            try:
                # Only test if file exists
                if os.path.exists(filename):
                    module_name, result_filename = reg.prepare(filename=filename)
                    assert module_name == expected_module, f"Module name mismatch: {module_name} != {expected_module}"
            finally:
                # Clean up
                del sys.modules[expected_module]


@given(st.integers(min_value=-1000, max_value=1000))
@settings(max_examples=30)
def test_get_at_with_various_line_numbers(lineno):
    """Test get_at() with various line numbers including edge cases."""
    reg = Registry()
    
    # Use this test file itself
    test_file = __file__
    
    # First, ensure the file is prepared
    reg.prepare(filename=test_file)
    
    # Call get_at with various line numbers
    cf, entry = reg.get_at(test_file, lineno)
    
    # Properties to verify:
    # 1. Should always return a tuple
    assert isinstance(cf, (type(None), object)), "First element should be CodeFile or None"
    assert isinstance(entry, (type(None), object)), "Second element should be entry or None"
    
    # 2. If cf is None, entry should also be None
    if cf is None:
        assert entry is None, "If CodeFile is None, entry should also be None"
    
    # 3. For negative line numbers, should not crash
    if lineno < 0:
        # Should handle gracefully
        assert entry is None, "Negative line numbers should return None entry"


@given(st.sampled_from([ModuleType, type, str, list, dict, int]))
@settings(max_examples=20)
def test_find_with_unsupported_types(obj_type):
    """Test find() with types that are not supported."""
    reg = Registry()
    
    # Create an instance of the type
    if obj_type == ModuleType:
        # Skip ModuleType as it's supported
        return
    elif obj_type == type:
        # Skip type as it's supported 
        return
    else:
        obj = obj_type()
    
    # find() should raise an error for unsupported types
    with pytest.raises(Exception):
        reg.find(obj)


@given(st.booleans(), st.booleans())
@settings(max_examples=10)
def test_registry_state_transitions(use_prepare, use_get):
    """Test state transitions in Registry between precache and cache."""
    reg = Registry()
    
    # Use a known module
    import json
    filename = json.__file__
    
    # Initial state
    assert filename not in reg.precache
    assert filename not in reg.cache
    
    if use_prepare:
        # After prepare
        reg.prepare('json')
        assert filename in reg.precache
        assert filename not in reg.cache
        
        if use_get:
            # After get
            cf = reg.get(filename)
            if cf is not None:
                assert filename in reg.cache
                # Note: file remains in precache too
                assert filename in reg.precache


def test_concurrent_registry_access():
    """Test that multiple Registry instances don't interfere."""
    reg1 = Registry()
    reg2 = Registry()
    reg3 = Registry()
    
    import json
    
    # Each registry should maintain its own state
    reg1.prepare('json')
    assert json.__file__ in reg1.precache
    assert json.__file__ not in reg2.precache
    assert json.__file__ not in reg3.precache
    
    reg2.prepare('json')
    cf2 = reg2.get(json.__file__)
    assert json.__file__ in reg2.cache
    assert json.__file__ not in reg1.cache
    assert json.__file__ not in reg3.cache


def test_registry_with_deleted_file():
    """Test Registry behavior when a file is deleted after caching."""
    reg = Registry()
    
    # Create a temporary Python file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("# Test module\nx = 42\n")
        temp_file = f.name
    
    try:
        # Create a module for this file
        module = type(sys)('temp_module')
        module.__file__ = temp_file
        module.__name__ = 'temp_module'
        sys.modules['temp_module'] = module
        
        # Prepare the module
        reg.prepare('temp_module')
        assert temp_file in reg.precache
        
        # Delete the file
        os.unlink(temp_file)
        
        # get() should still work with cached data
        cf = reg.get(temp_file)
        assert cf is not None, "Should return CodeFile from precache even if file deleted"
        
    finally:
        # Clean up
        if 'temp_module' in sys.modules:
            del sys.modules['temp_module']
        if os.path.exists(temp_file):
            os.unlink(temp_file)