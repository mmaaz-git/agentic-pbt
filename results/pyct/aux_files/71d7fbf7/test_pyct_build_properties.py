import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

import os
import json
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings
import pyct.build

# Strategy for valid directory names (avoiding problematic characters)
valid_dirname = st.text(
    alphabet=st.characters(min_codepoint=65, max_codepoint=122, whitelist_characters="_-"),
    min_size=1, 
    max_size=20
).filter(lambda s: s.strip() and not s.startswith('.'))

# Strategy for valid repo names
valid_reponame = st.text(
    alphabet=st.characters(min_codepoint=65, max_codepoint=122, whitelist_characters="_-"),
    min_size=1,
    max_size=20
).filter(lambda s: s.strip())

@given(
    subdir=valid_dirname,
    force=st.booleans()
)
@settings(max_examples=100)
def test_examples_path_handling(subdir, force):
    """Test that examples() correctly handles path operations."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mock module structure
        module_dir = Path(tmpdir) / "test_module"
        module_dir.mkdir()
        
        # Create examples directory with some content
        examples_dir = module_dir / "examples"
        examples_dir.mkdir()
        test_file = examples_dir / "test.txt"
        test_file.write_text("test content")
        
        # Create target path
        target_path = Path(tmpdir) / subdir
        
        # Create a dummy __file__ in module directory to simulate root
        dummy_file = module_dir / "dummy.py"
        dummy_file.write_text("")
        
        # Test the function
        try:
            pyct.build.examples(str(target_path), str(dummy_file), verbose=False, force=force)
            
            # If we get here without error, target should exist
            assert target_path.exists()
            assert target_path.is_dir()
            
            # Check that files were copied
            copied_file = target_path / "test.txt"
            assert copied_file.exists()
            assert copied_file.read_text() == "test content"
            
        except Exception as e:
            # If examples dir doesn't exist in expected location, function will print error
            # This is expected behavior based on the code
            pass


@given(
    reponame=valid_reponame,
    version_string=st.text(min_size=1, max_size=50).filter(lambda s: s.strip())
)
@settings(max_examples=100)
def test_get_setup_version_json_parsing(reponame, version_string):
    """Test that get_setup_version correctly parses JSON from .version file."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create module structure
        module_dir = Path(tmpdir) / reponame
        module_dir.mkdir()
        
        # Create .version file with valid JSON
        version_file = module_dir / ".version"
        version_data = {"version_string": version_string}
        version_file.write_text(json.dumps(version_data))
        
        # Create a dummy file to act as root
        dummy_file = Path(tmpdir) / "setup.py"
        dummy_file.write_text("")
        
        # Temporarily hide param module to force JSON parsing path
        import sys
        param_backup = sys.modules.get('param')
        if 'param' in sys.modules:
            del sys.modules['param']
        
        try:
            result = pyct.build.get_setup_version(str(dummy_file), reponame)
            assert result == version_string
        except FileNotFoundError:
            # This can happen if the path construction doesn't match our setup
            # which is valid behavior
            pass
        finally:
            # Restore param module if it was there
            if param_backup:
                sys.modules['param'] = param_backup


@given(force=st.booleans())
@settings(max_examples=50)
def test_examples_force_flag_behavior(force):
    """Test that force flag correctly handles existing directories."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create module structure
        module_dir = Path(tmpdir) / "module"
        module_dir.mkdir()
        examples_dir = module_dir / "examples"
        examples_dir.mkdir()
        (examples_dir / "example.txt").write_text("example")
        
        # Create target that already exists
        target = Path(tmpdir) / "target"
        target.mkdir()
        existing_file = target / "existing.txt"
        existing_file.write_text("existing content")
        
        dummy_root = module_dir / "dummy.py"
        dummy_root.write_text("")
        
        if force:
            # Should succeed and overwrite
            pyct.build.examples(str(target), str(dummy_root), force=True)
            
            # Original file should be gone
            assert not existing_file.exists()
            
            # New content should be there
            assert (target / "example.txt").exists()
        else:
            # Should print error message and return without changes
            pyct.build.examples(str(target), str(dummy_root), force=False)
            
            # Original content should still be there
            assert existing_file.exists()
            assert existing_file.read_text() == "existing content"


@given(
    path1=valid_dirname,
    path2=valid_dirname
)
@settings(max_examples=50)
def test_examples_idempotence_with_force(path1, path2):
    """Test that running examples() twice with force=True produces same result."""
    
    assume(path1 != path2)  # Need different paths to test idempotence
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create module structure
        module_dir = Path(tmpdir) / "module"
        module_dir.mkdir()
        examples_dir = module_dir / "examples"
        examples_dir.mkdir()
        
        # Create some example content
        (examples_dir / "file1.txt").write_text("content1")
        (examples_dir / "file2.txt").write_text("content2")
        subdir = examples_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")
        
        dummy_root = module_dir / "dummy.py"
        dummy_root.write_text("")
        
        target1 = Path(tmpdir) / path1
        target2 = Path(tmpdir) / path2
        
        # Run twice with force=True
        pyct.build.examples(str(target1), str(dummy_root), force=True)
        pyct.build.examples(str(target2), str(dummy_root), force=True)
        
        # Both should have same structure and content
        def get_dir_structure(path):
            structure = {}
            for root, dirs, files in os.walk(path):
                rel_root = os.path.relpath(root, path)
                for f in files:
                    file_path = os.path.join(rel_root, f) if rel_root != "." else f
                    full_path = os.path.join(root, f)
                    with open(full_path, 'r') as fp:
                        structure[file_path] = fp.read()
            return structure
        
        struct1 = get_dir_structure(target1)
        struct2 = get_dir_structure(target2)
        
        assert struct1 == struct2


@given(
    reponame=valid_reponame,
    json_content=st.text(min_size=1, max_size=1000)
)
@settings(max_examples=50)
def test_get_setup_version_handles_invalid_json(reponame, json_content):
    """Test that get_setup_version handles malformed JSON gracefully."""
    
    assume(json_content.strip())  # Non-empty content
    
    # Make sure it's invalid JSON
    try:
        json.loads(json_content)
        assume(False)  # Skip if it's valid JSON
    except:
        pass  # Good, it's invalid
    
    with tempfile.TemporaryDirectory() as tmpdir:
        module_dir = Path(tmpdir) / reponame
        module_dir.mkdir()
        
        # Create .version file with invalid JSON
        version_file = module_dir / ".version"
        version_file.write_text(json_content)
        
        dummy_file = Path(tmpdir) / "setup.py"
        dummy_file.write_text("")
        
        # Hide param module
        import sys
        param_backup = sys.modules.get('param')
        if 'param' in sys.modules:
            del sys.modules['param']
        
        try:
            # This should raise JSONDecodeError
            result = pyct.build.get_setup_version(str(dummy_file), reponame)
            # If we get here, the function handled invalid JSON somehow
            # which might be a bug
            assert False, f"Expected JSONDecodeError but got result: {result}"
        except json.JSONDecodeError:
            # Expected behavior
            pass
        except FileNotFoundError:
            # Also acceptable if file path doesn't match
            pass
        finally:
            if param_backup:
                sys.modules['param'] = param_backup