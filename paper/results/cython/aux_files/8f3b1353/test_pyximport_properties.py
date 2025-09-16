import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest
from hypothesis import given, strategies as st, assume, settings

# Import the module under test
import pyximport.pyximport as pyx


# Test 1: install/uninstall round-trip property
@given(
    pyximport=st.booleans(),
    pyimport=st.booleans(), 
    build_in_temp=st.booleans(),
    inplace=st.booleans(),
    language_level=st.one_of(st.none(), st.sampled_from([2, 3])),
    reload_support=st.booleans(),
    load_py_module_on_import_failure=st.booleans()
)
def test_install_uninstall_roundtrip(pyximport, pyimport, build_in_temp, inplace, 
                                    language_level, reload_support, 
                                    load_py_module_on_import_failure):
    """Test that install/uninstall maintains sys.meta_path state"""
    
    # Skip if both are False (no importers to install)
    assume(pyximport or pyimport)
    
    # Save initial state
    initial_meta_path = sys.meta_path.copy()
    initial_importers = [type(imp).__name__ for imp in initial_meta_path]
    
    # Install hooks
    py_imp, pyx_imp = pyx.install(
        pyximport=pyximport,
        pyimport=pyimport,
        build_in_temp=build_in_temp,
        inplace=inplace,
        language_level=language_level,
        reload_support=reload_support,
        load_py_module_on_import_failure=load_py_module_on_import_failure
    )
    
    # Verify hooks were added
    after_install = sys.meta_path.copy()
    if pyimport:
        assert py_imp is not None
        assert py_imp in sys.meta_path
    if pyximport:
        assert pyx_imp is not None
        assert pyx_imp in sys.meta_path
    
    # Uninstall hooks
    pyx.uninstall(py_imp, pyx_imp)
    
    # Verify we're back to initial state
    final_meta_path = sys.meta_path.copy()
    final_importers = [type(imp).__name__ for imp in final_meta_path]
    
    # Property: after install/uninstall, meta_path types should match initial
    assert initial_importers == final_importers


# Test 2: handle_special_build assertions
@given(
    modname=st.text(min_size=1, max_size=50).filter(lambda x: x.isidentifier()),
    has_make_ext=st.booleans(),
    has_make_setup_args=st.booleans(),
    ext_has_sources=st.booleans(),
    setup_args_is_dict=st.booleans()
)
@settings(max_examples=500)
def test_handle_special_build_assertions(modname, has_make_ext, has_make_setup_args,
                                        ext_has_sources, setup_args_is_dict):
    """Test that handle_special_build's assertions are correct"""
    
    # Create a temporary .pyx and .pyxbld file
    with tempfile.TemporaryDirectory() as tmpdir:
        pyxfile = os.path.join(tmpdir, f"{modname}.pyx")
        pyxbldfile = os.path.join(tmpdir, f"{modname}.pyxbld")
        
        # Write minimal .pyx file
        with open(pyxfile, 'w') as f:
            f.write("# Cython file\n")
        
        # Create .pyxbld content based on parameters
        pyxbld_content = []
        
        if has_make_ext:
            if ext_has_sources:
                pyxbld_content.append("""
def make_ext(modname, pyxfilename):
    from distutils.extension import Extension
    return Extension(name=modname, sources=[pyxfilename])
""")
            else:
                pyxbld_content.append("""
def make_ext(modname, pyxfilename):
    from distutils.extension import Extension
    ext = Extension(name=modname, sources=[])
    ext.sources = []  # Empty sources
    return ext
""")
        
        if has_make_setup_args:
            if setup_args_is_dict:
                pyxbld_content.append("""
def make_setup_args():
    return {'script_args': ['--quiet']}
""")
            else:
                pyxbld_content.append("""
def make_setup_args():
    return "not a dict"  # Should fail assertion
""")
        
        # Write .pyxbld file
        with open(pyxbldfile, 'w') as f:
            f.write('\n'.join(pyxbld_content))
        
        # Test the function
        try:
            ext, setup_args = pyx.handle_special_build(modname, pyxfile)
            
            # If we get here, assertions passed
            # Verify the contract from line 129-130
            assert ext or setup_args, "neither make_ext nor make_setup_args returned valid values"
            
            if ext:
                # From line 123: ext should have sources
                assert hasattr(ext, 'sources'), "Extension should have sources attribute"
                # Note: the assertion on line 123 checks ext.sources is truthy
                # but line 131-132 then modifies ext.sources, so empty is allowed
            
            if setup_args:
                # From line 127-128: setup_args must be dict
                assert isinstance(setup_args, dict), "setup_args should be a dict"
                
        except AssertionError as e:
            # Check if the assertion was expected
            if not has_make_ext and not has_make_setup_args:
                # Should fail with "neither make_ext nor make_setup_args"
                assert "neither make_ext nor make_setup_args" in str(e)
            elif has_make_ext and not ext_has_sources and not has_make_setup_args:
                # Should fail with "make_ext...did not return Extension" 
                assert "did not return Extension" in str(e) or "neither make_ext" in str(e)
            elif has_make_setup_args and not setup_args_is_dict:
                # Should fail with "did not return a dict"
                assert "did not return a dict" in str(e)
            else:
                # Unexpected assertion
                raise


# Test 3: PyxArgs setup_args property - should always be a dict and gets copied
@given(
    setup_args_input=st.one_of(
        st.none(),
        st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(st.text(), st.integers(), st.booleans()),
            max_size=5
        )
    )
)
def test_pyxargs_setup_args_copy(setup_args_input):
    """Test that setup_args is properly copied in install()"""
    
    # Save initial state
    initial_meta_path = sys.meta_path.copy()
    
    try:
        # Install with the given setup_args
        py_imp, pyx_imp = pyx.install(
            pyximport=True,
            pyimport=False,
            setup_args=setup_args_input
        )
        
        # Check pyxargs was created and setup_args is a dict
        assert hasattr(pyx, 'pyxargs')
        assert hasattr(pyx.pyxargs, 'setup_args')
        assert isinstance(pyx.pyxargs.setup_args, dict)
        
        # If input was None, should be empty dict
        if setup_args_input is None:
            assert pyx.pyxargs.setup_args == {}
        else:
            # Should be a copy, not the same object
            assert pyx.pyxargs.setup_args is not setup_args_input
            assert pyx.pyxargs.setup_args == setup_args_input
            
            # Verify it's a real copy by modifying original
            if setup_args_input:
                key = list(setup_args_input.keys())[0]
                original_value = setup_args_input[key]
                setup_args_input[key] = "modified"
                assert pyx.pyxargs.setup_args[key] == original_value
                
    finally:
        # Clean up
        if 'py_imp' in locals() or 'pyx_imp' in locals():
            pyx.uninstall(py_imp if 'py_imp' in locals() else None,
                         pyx_imp if 'pyx_imp' in locals() else None)
        sys.meta_path[:] = initial_meta_path


# Test 4: Multiple install calls behavior
@given(
    first_params=st.fixed_dictionaries({
        'pyximport': st.booleans(),
        'pyimport': st.booleans(),
        'language_level': st.one_of(st.none(), st.sampled_from([2, 3]))
    }),
    second_params=st.fixed_dictionaries({
        'pyximport': st.booleans(), 
        'pyimport': st.booleans(),
        'language_level': st.one_of(st.none(), st.sampled_from([2, 3]))
    })
)
def test_multiple_install_idempotence(first_params, second_params):
    """Test that multiple install calls don't duplicate importers"""
    
    # Save initial state
    initial_meta_path = sys.meta_path.copy()
    
    try:
        # First install
        py_imp1, pyx_imp1 = pyx.install(**first_params)
        meta_path_after_first = sys.meta_path.copy()
        
        # Count importers after first install
        pyx_importers_count1 = sum(1 for imp in sys.meta_path 
                                  if type(imp).__name__ == 'PyxImportMetaFinder')
        py_importers_count1 = sum(1 for imp in sys.meta_path 
                                 if type(imp).__name__ == 'PyImportMetaFinder')
        
        # Second install with same parameters
        py_imp2, pyx_imp2 = pyx.install(**second_params)
        
        # Count importers after second install
        pyx_importers_count2 = sum(1 for imp in sys.meta_path 
                                  if type(imp).__name__ == 'PyxImportMetaFinder')
        py_importers_count2 = sum(1 for imp in sys.meta_path 
                                 if type(imp).__name__ == 'PyImportMetaFinder')
        
        # Property: Should not have duplicates
        if first_params['pyximport'] and second_params['pyximport']:
            assert pyx_importers_count2 == 1, "Should not duplicate PyxImportMetaFinder"
            assert pyx_imp2 is None, "Second install should return None for existing importer"
            
        if first_params['pyimport'] and second_params['pyimport']:
            assert py_importers_count2 == 1, "Should not duplicate PyImportMetaFinder"
            assert py_imp2 is None, "Second install should return None for existing importer"
            
    finally:
        # Clean up all importers
        for imp in sys.meta_path[:]:
            if type(imp).__name__ in ['PyxImportMetaFinder', 'PyImportMetaFinder']:
                sys.meta_path.remove(imp)
        sys.meta_path[:] = initial_meta_path


# Test 5: Path normalization in build_module
@given(
    path_components=st.lists(
        st.text(min_size=1, max_size=10).filter(
            lambda x: x.isidentifier() and not x.startswith('_')
        ),
        min_size=1,
        max_size=5
    )
)
def test_build_module_path_assertions(path_components):
    """Test that build_module properly handles path assertions"""
    
    # Create a path from components
    test_filename = '_'.join(path_components) + '.pyx'
    
    with tempfile.TemporaryDirectory() as tmpdir:
        pyxfile = os.path.join(tmpdir, test_filename)
        
        # Test assertion on line 176: file must exist
        try:
            pyx.build_module("test_module", pyxfile, pyxbuild_dir=tmpdir)
            # Should not get here
            assert False, "build_module should fail for non-existent file"
        except AssertionError as e:
            assert "Path does not exist" in str(e)
        
        # Create the file and try again
        with open(pyxfile, 'w') as f:
            f.write("# Test Cython file\n")
            f.write("def test_func():\n")
            f.write("    return 42\n")
        
        # This will likely fail at build time but we're testing the assertion
        # The second assertion (line 206) requires successful build
        # which needs proper Cython setup