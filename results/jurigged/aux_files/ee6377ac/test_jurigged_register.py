import sys
import os
import types
import tempfile
from pathlib import Path

sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import pytest
from jurigged.register import Registry, ImportSniffer


@composite
def python_module_with_file(draw):
    """Strategy to generate Python modules that have a __file__ attribute."""
    # List of common stdlib modules that have files
    modules_with_files = [
        'json', 'os', 'pathlib', 'tempfile', 'collections', 'functools',
        'itertools', 'datetime', 'random', 'string', 'unittest', 'urllib',
        'email', 'html', 'http', 'xml', 'csv', 'configparser', 'logging'
    ]
    module_name = draw(st.sampled_from(modules_with_files))
    module = __import__(module_name)
    # Ensure the module has a __file__ attribute
    assume(hasattr(module, '__file__') and module.__file__ is not None)
    assume(os.path.exists(module.__file__))
    return module


@given(python_module_with_file())
@settings(max_examples=50)
def test_prepare_idempotence(module):
    """Test that prepare() is idempotent - calling it multiple times yields the same result."""
    reg = Registry()
    
    # First prepare
    module_name1, filename1 = reg.prepare(module.__name__)
    precache_state1 = filename1 in reg.precache
    
    # Second prepare
    module_name2, filename2 = reg.prepare(module.__name__)
    precache_state2 = filename2 in reg.precache
    
    # Properties to check
    assert module_name1 == module_name2, f"Module names differ: {module_name1} != {module_name2}"
    assert filename1 == filename2, f"Filenames differ: {filename1} != {filename2}"
    assert precache_state1 == precache_state2, "Precache state changed after second prepare"
    
    # The precache entry should remain the same
    if filename1 in reg.precache:
        entry1 = reg.precache[filename1]
        module_name3, filename3 = reg.prepare(module.__name__)
        entry2 = reg.precache[filename1]
        assert entry1[0] == entry2[0], "Module name in precache changed"
        assert entry1[1] == entry2[1], "Source code in precache changed"


@given(python_module_with_file())
@settings(max_examples=30)
def test_cache_consistency_after_get(module):
    """Test that after calling get(), the file is properly cached."""
    reg = Registry()
    
    # Prepare the module
    module_name, filename = reg.prepare(module.__name__)
    
    # Verify it's in precache
    assert filename in reg.precache, "File not in precache after prepare()"
    
    # Get the CodeFile
    cf = reg.get(filename)
    
    if cf is not None:
        # After get(), it should be in cache
        assert filename in reg.cache, "File not in cache after get()"
        
        # Getting again should return the same object
        cf2 = reg.get(filename)
        assert cf is cf2, "get() doesn't return the same cached object"


@given(python_module_with_file())
@settings(max_examples=30)
def test_find_module_round_trip(module):
    """Test that find(module) returns a valid CodeFile and root."""
    reg = Registry()
    
    cf, root = reg.find(module)
    
    # Properties to check
    assert cf is not None, f"CodeFile is None for module {module.__name__}"
    assert root is not None, f"Root is None for module {module.__name__}"
    
    # The CodeFile should have the correct filename
    assert cf.filename == module.__file__, f"CodeFile filename mismatch: {cf.filename} != {module.__file__}"
    
    # The CodeFile should be cached
    assert module.__file__ in reg.cache, "Module file not in cache after find()"
    
    # Calling find again should return the same objects
    cf2, root2 = reg.find(module)
    assert cf is cf2, "find() doesn't return the same CodeFile on second call"
    assert root is root2, "find() doesn't return the same root on second call"


@given(python_module_with_file())
@settings(max_examples=30)
def test_filename_to_module_mapping(module):
    """Test that filename_to_module correctly maps files to module names."""
    reg = Registry()
    
    # When we prepare with only a filename, it should populate filename_to_module
    module_name, filename = reg.prepare(filename=module.__file__)
    
    # The mapping should be correct
    assert module_name == module.__name__, f"Module name mismatch: {module_name} != {module.__name__}"
    
    # The filename_to_module should contain this mapping
    assert filename in reg.filename_to_module, "Filename not in filename_to_module"
    assert reg.filename_to_module[filename] == module.__name__, "Incorrect mapping in filename_to_module"


@given(st.text(min_size=1, max_size=100).filter(lambda x: '/' not in x and '\\' not in x))
@settings(max_examples=30)
def test_prepare_with_nonexistent_module(module_name):
    """Test that prepare() raises an exception for non-existent modules."""
    assume(module_name not in sys.modules)
    
    reg = Registry()
    
    with pytest.raises(KeyError):
        reg.prepare(module_name)


@given(st.text(min_size=1))
@settings(max_examples=30)
def test_prepare_with_nonexistent_file(filename):
    """Test behavior when preparing with a non-existent file."""
    assume(not os.path.exists(filename))
    assume(filename not in [getattr(m, '__file__', None) for m in sys.modules.values()])
    
    reg = Registry()
    
    # Should raise an exception when it can't find the module
    with pytest.raises(Exception, match="Cannot find module that corresponds to"):
        reg.prepare(filename=filename)


@given(python_module_with_file())
@settings(max_examples=20)
def test_get_at_with_invalid_lineno(module):
    """Test get_at() with invalid line numbers."""
    reg = Registry()
    
    # Prepare and get the CodeFile
    reg.prepare(module.__name__)
    cf = reg.get(module.__file__)
    
    if cf is not None:
        # Test with negative line number
        cf_result, entry = reg.get_at(module.__file__, -1)
        assert cf_result is cf, "get_at should return the CodeFile even with invalid lineno"
        assert entry is None, "get_at should return None entry for invalid lineno"
        
        # Test with very large line number
        cf_result, entry = reg.get_at(module.__file__, 999999)
        assert cf_result is cf, "get_at should return the CodeFile even with large lineno"
        assert entry is None, "get_at should return None entry for non-existent lineno"


@given(python_module_with_file(), python_module_with_file())
@settings(max_examples=20)
def test_registry_isolation(module1, module2):
    """Test that Registry instances are properly isolated from each other."""
    assume(module1.__name__ != module2.__name__)
    
    reg1 = Registry()
    reg2 = Registry()
    
    # Prepare module1 in reg1
    reg1.prepare(module1.__name__)
    
    # reg2 should not have module1 cached
    assert module1.__file__ not in reg2.precache, "Registry instances share precache"
    assert module1.__file__ not in reg2.cache, "Registry instances share cache"
    
    # Prepare module2 in reg2
    reg2.prepare(module2.__name__)
    
    # reg1 should not have module2
    assert module2.__file__ not in reg1.precache, "Registry instances share precache"
    
    # Each registry should only have its own module
    assert module1.__file__ in reg1.precache
    assert module2.__file__ in reg2.precache