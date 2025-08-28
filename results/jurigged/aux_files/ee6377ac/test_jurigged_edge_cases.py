import sys
import os
import tempfile
from pathlib import Path
import types
import ast

sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, note
from hypothesis.strategies import composite
import pytest
from jurigged.register import Registry
from jurigged.codetools import CodeFile


@composite
def python_source_code(draw):
    """Generate valid Python source code."""
    templates = [
        "x = {value}",
        "def func():\n    return {value}",
        "class MyClass:\n    value = {value}",
        "import sys\nx = {value}",
        "# Comment\nx = {value}\ny = {value}",
        "if True:\n    x = {value}\nelse:\n    x = 0",
    ]
    template = draw(st.sampled_from(templates))
    value = draw(st.integers(min_value=-1000, max_value=1000))
    return template.format(value=value)


@given(python_source_code())
@settings(max_examples=30)
def test_registry_with_dynamic_modules(source_code):
    """Test Registry with dynamically created modules."""
    reg = Registry()
    
    # Create a temporary file with the source code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(source_code)
        temp_file = f.name
    
    try:
        # Create a dynamic module
        module_name = f"dynamic_module_{hash(source_code) % 10000}"
        module = types.ModuleType(module_name)
        module.__file__ = temp_file
        module.__name__ = module_name
        
        # Add to sys.modules
        sys.modules[module_name] = module
        
        try:
            # Test prepare
            result_name, result_file = reg.prepare(module_name)
            assert result_name == module_name
            assert result_file == temp_file
            assert temp_file in reg.precache
            
            # Test get
            cf = reg.get(temp_file)
            assert cf is not None
            assert isinstance(cf, CodeFile)
            assert cf.filename == temp_file
            
            # Test find
            cf2, root = reg.find(module)
            assert cf2 is cf  # Should be the same cached object
            assert root is not None
            
        finally:
            # Clean up sys.modules
            del sys.modules[module_name]
            
    finally:
        # Clean up temp file
        os.unlink(temp_file)


@given(st.text(min_size=1, max_size=100))
@settings(max_examples=20)
def test_registry_with_unicode_filenames(text):
    """Test Registry with files containing unicode characters."""
    # Create a safe filename with unicode
    safe_text = ''.join(c if c.isalnum() or c in '_-' else '_' for c in text)
    if not safe_text:
        safe_text = 'test'
    
    reg = Registry()
    
    # Create temp file with unicode in name
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix=f'_{safe_text}.py', 
        delete=False, 
        prefix='test_'
    ) as f:
        f.write("# Test file\nx = 42")
        temp_file = f.name
    
    try:
        # Create module
        module_name = f"unicode_module_{safe_text}"
        module = types.ModuleType(module_name)
        module.__file__ = temp_file
        module.__name__ = module_name
        sys.modules[module_name] = module
        
        try:
            # Test that unicode filenames work
            result_name, result_file = reg.prepare(module_name)
            assert result_name == module_name
            assert result_file == temp_file
            
        finally:
            del sys.modules[module_name]
            
    finally:
        os.unlink(temp_file)


@given(st.lists(st.tuples(
    st.text(min_size=1, max_size=20),  # module names
    st.text(min_size=1, max_size=50)   # file paths
), min_size=0, max_size=10))
@settings(max_examples=20)
def test_registry_filename_to_module_overwrite(mappings):
    """Test that filename_to_module handles overwrites correctly."""
    reg = Registry()
    
    for module_name, filepath in mappings:
        # Set the mapping
        reg.filename_to_module[filepath] = module_name
        
        # Verify it was set
        assert reg.filename_to_module[filepath] == module_name
        
        # Overwrite with a different module name
        new_module_name = module_name + "_new"
        reg.filename_to_module[filepath] = new_module_name
        
        # Verify the overwrite worked
        assert reg.filename_to_module[filepath] == new_module_name


def test_registry_with_binary_file():
    """Test Registry behavior with binary files."""
    reg = Registry()
    
    # Create a binary file
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pyc', delete=False) as f:
        f.write(b'\x00\x01\x02\x03')
        temp_file = f.name
    
    try:
        # Create a module pointing to binary file
        module = types.ModuleType('binary_module')
        module.__file__ = temp_file
        module.__name__ = 'binary_module'
        sys.modules['binary_module'] = module
        
        try:
            # prepare should handle binary files gracefully (likely skip them)
            result = reg.prepare('binary_module')
            # It should return something without crashing
            assert result is not None
            
            # The file should not be in precache (can't read binary as text)
            assert temp_file not in reg.precache
            
        finally:
            del sys.modules['binary_module']
            
    finally:
        os.unlink(temp_file)


def test_registry_with_very_large_file():
    """Test Registry with a very large source file."""
    reg = Registry()
    
    # Create a large source file
    large_source = "x = 1\n" * 10000  # 10,000 lines
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(large_source)
        temp_file = f.name
    
    try:
        module = types.ModuleType('large_module')
        module.__file__ = temp_file
        module.__name__ = 'large_module'
        sys.modules['large_module'] = module
        
        try:
            # Should handle large files
            module_name, filename = reg.prepare('large_module')
            assert temp_file in reg.precache
            
            # Check that the cached source matches
            cached_module, cached_source, mtime = reg.precache[temp_file]
            assert cached_source == large_source
            
        finally:
            del sys.modules['large_module']
            
    finally:
        os.unlink(temp_file)


@given(st.integers(min_value=0, max_value=100))
@settings(max_examples=20)
def test_registry_get_with_missing_module(seed):
    """Test get() when module is removed from sys.modules."""
    reg = Registry()
    
    # Create a temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(f"x = {seed}")
        temp_file = f.name
    
    try:
        module_name = f"missing_module_{seed}"
        module = types.ModuleType(module_name)
        module.__file__ = temp_file
        module.__name__ = module_name
        sys.modules[module_name] = module
        
        # Prepare the module
        reg.prepare(module_name)
        assert temp_file in reg.precache
        
        # Remove module from sys.modules
        del sys.modules[module_name]
        
        # get() should return None when module is not in sys.modules
        cf = reg.get(temp_file)
        assert cf is None, "get() should return None when module not in sys.modules"
        
    finally:
        # Clean up
        if module_name in sys.modules:
            del sys.modules[module_name]
        os.unlink(temp_file)


def test_registry_with_module_without_file():
    """Test Registry with built-in modules that have no __file__."""
    reg = Registry()
    
    # Built-in modules like 'sys' might not have __file__
    builtins = types.ModuleType('test_builtin')
    builtins.__name__ = 'test_builtin'
    # Explicitly no __file__ attribute
    
    sys.modules['test_builtin'] = builtins
    
    try:
        # prepare should handle modules without __file__
        with pytest.raises(AttributeError):
            reg.prepare('test_builtin')
            
    finally:
        del sys.modules['test_builtin']


@given(st.sampled_from(['', ' ', '\n', '\t', '   \n\t  ']))
@settings(max_examples=10)
def test_registry_with_empty_or_whitespace_files(content):
    """Test Registry with empty or whitespace-only files."""
    reg = Registry()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        temp_file = f.name
    
    try:
        module = types.ModuleType('empty_module')
        module.__file__ = temp_file
        module.__name__ = 'empty_module'
        sys.modules['empty_module'] = module
        
        try:
            # Should handle empty/whitespace files
            module_name, filename = reg.prepare('empty_module')
            assert temp_file in reg.precache
            
            # Get the CodeFile
            cf = reg.get(temp_file)
            assert cf is not None
            
        finally:
            del sys.modules['empty_module']
            
    finally:
        os.unlink(temp_file)