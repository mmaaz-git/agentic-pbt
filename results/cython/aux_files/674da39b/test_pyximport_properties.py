"""
Property-based tests for pyximport module using Hypothesis.
"""
import sys
import os
import tempfile
import shutil
from hypothesis import given, strategies as st, assume, settings
import pyximport
from pyximport import pyximport as pyx_module


# Test 1: Install/uninstall round-trip property
@given(
    pyximport_flag=st.booleans(),
    pyimport_flag=st.booleans(),
    build_in_temp=st.booleans(),
    reload_support=st.booleans(),
    load_py_module_on_import_failure=st.booleans(),
    inplace=st.booleans(),
    language_level=st.one_of(st.none(), st.sampled_from([2, 3]))
)
def test_install_uninstall_round_trip(
    pyximport_flag,
    pyimport_flag,
    build_in_temp,
    reload_support,
    load_py_module_on_import_failure,
    inplace,
    language_level
):
    """Test that install/uninstall maintains sys.meta_path state correctly."""
    # Skip if neither import type is enabled
    assume(pyximport_flag or pyimport_flag)
    
    # Save initial state
    initial_meta_path = sys.meta_path.copy()
    initial_count = len(sys.meta_path)
    
    # Install the import hooks
    with tempfile.TemporaryDirectory() as build_dir:
        py_importer, pyx_importer = pyximport.install(
            pyximport=pyximport_flag,
            pyimport=pyimport_flag,
            build_dir=build_dir,
            build_in_temp=build_in_temp,
            reload_support=reload_support,
            load_py_module_on_import_failure=load_py_module_on_import_failure,
            inplace=inplace,
            language_level=language_level
        )
        
        # Check that importers were added to sys.meta_path
        if pyximport_flag:
            assert pyx_importer is not None
            assert pyx_importer in sys.meta_path
        else:
            assert pyx_importer is None
            
        if pyimport_flag:
            assert py_importer is not None
            assert py_importer in sys.meta_path
        else:
            assert py_importer is None
        
        # Uninstall the hooks
        pyximport.uninstall(py_importer, pyx_importer)
        
        # Check that sys.meta_path is restored
        # The uninstall should remove the importers
        if py_importer:
            assert py_importer not in sys.meta_path
        if pyx_importer:
            assert pyx_importer not in sys.meta_path


# Test 2: PyImportMetaFinder blocked_modules list management
@given(
    module_names=st.lists(
        st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=20),
        min_size=1,
        max_size=5
    )
)
def test_blocked_modules_list_management(module_names):
    """Test that blocked_modules list is properly managed during find_spec."""
    with tempfile.TemporaryDirectory() as build_dir:
        finder = pyx_module.PyImportMetaFinder(
            pyxbuild_dir=build_dir,
            inplace=False,
            language_level=None
        )
        
        initial_blocked = finder.blocked_modules.copy()
        initial_length = len(finder.blocked_modules)
        
        # Call find_spec with non-existent modules
        for module_name in module_names:
            # Ensure module doesn't exist in sys.modules
            if module_name not in sys.modules:
                result = finder.find_spec(module_name, None)
                # Should return None for non-existent modules
                assert result is None
        
        # After all calls, blocked_modules should be back to initial state
        # This tests that the pop() in finally block works correctly
        assert len(finder.blocked_modules) == initial_length
        assert finder.blocked_modules == initial_blocked


# Test 3: find_spec returns None for unfindable modules
@given(
    module_name=st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=30
    ),
    extension=st.sampled_from([".pyx", ".py"])
)
def test_find_spec_returns_none_for_unfindable(module_name, extension):
    """Test that find_spec returns None when it can't find a module."""
    # Skip if module name might conflict with real modules
    assume(not module_name.startswith("_"))
    assume(module_name not in sys.modules)
    assume(not any(module_name.startswith(pkg) for pkg in ["Cython", "distutils", "sys", "os"]))
    
    with tempfile.TemporaryDirectory() as temp_dir:
        if extension == ".pyx":
            finder = pyx_module.PyxImportMetaFinder(
                extension=extension,
                pyxbuild_dir=temp_dir,
                inplace=False,
                language_level=None
            )
        else:
            finder = pyx_module.PyImportMetaFinder(
                extension=extension,
                pyxbuild_dir=temp_dir,
                inplace=False,
                language_level=None
            )
        
        # Try to find a non-existent module
        result = finder.find_spec(module_name, [temp_dir])
        
        # Should return None as documented in the code
        assert result is None


# Test 4: PyxArgs maintains its attributes correctly
@given(
    build_dir_flag=st.booleans(),
    build_in_temp_flag=st.booleans(),
    setup_args_dict=st.dictionaries(
        keys=st.text(min_size=1, max_size=10),
        values=st.text(min_size=0, max_size=10),
        max_size=3
    )
)
def test_pyxargs_state(build_dir_flag, build_in_temp_flag, setup_args_dict):
    """Test that PyxArgs maintains its state correctly."""
    args = pyx_module.PyxArgs()
    
    # Check initial state
    assert args.build_dir == True
    assert args.build_in_temp == True
    assert isinstance(args.setup_args, dict)
    assert len(args.setup_args) == 0
    
    # Modify state
    args.build_dir = build_dir_flag
    args.build_in_temp = build_in_temp_flag
    args.setup_args = setup_args_dict.copy()
    
    # Check modified state
    assert args.build_dir == build_dir_flag
    assert args.build_in_temp == build_in_temp_flag
    assert args.setup_args == setup_args_dict


# Test 5: Multiple install calls behavior
@given(
    first_pyximport=st.booleans(),
    first_pyimport=st.booleans(),
    second_pyximport=st.booleans(),
    second_pyimport=st.booleans()
)
def test_multiple_install_calls(first_pyximport, first_pyimport, second_pyximport, second_pyimport):
    """Test behavior of multiple install calls without uninstall."""
    # Need at least one type enabled for each call
    assume(first_pyximport or first_pyimport)
    assume(second_pyximport or second_pyimport)
    
    initial_meta_path = sys.meta_path.copy()
    
    with tempfile.TemporaryDirectory() as build_dir1:
        with tempfile.TemporaryDirectory() as build_dir2:
            # First install
            py1, pyx1 = pyximport.install(
                pyximport=first_pyximport,
                pyimport=first_pyimport,
                build_dir=build_dir1
            )
            
            meta_path_after_first = sys.meta_path.copy()
            
            # Second install - should not add duplicate importers
            py2, pyx2 = pyximport.install(
                pyximport=second_pyximport,
                pyimport=second_pyimport,
                build_dir=build_dir2
            )
            
            # If the same type was already installed, should return None
            if first_pyximport and second_pyximport:
                assert pyx2 is None
            if first_pyimport and second_pyimport:
                assert py2 is None
                
            # Clean up
            pyximport.uninstall(py1, pyx1)
            pyximport.uninstall(py2, pyx2)
            
            # Ensure all importers are removed
            for importer in sys.meta_path:
                assert not isinstance(importer, pyx_module.PyxImportMetaFinder)
                assert not isinstance(importer, pyx_module.PyImportMetaFinder)


if __name__ == "__main__":
    # Run with pytest
    import pytest
    pytest.main([__file__, "-v"])