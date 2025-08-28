import os
import sys
import tempfile
from pathlib import Path

import pytest
from hypothesis import assume, given, settings, strategies as st

sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.path import (
    AssetResolver,
    DottedNameResolver,
    FSAssetDescriptor,
    PkgResourcesAssetDescriptor,
    package_name,
    package_of,
)


# Strategy for valid package names
valid_package_names = st.sampled_from([
    'xml', 'xml.dom', 'os', 'sys', 'json', 'collections',
    'importlib', 'importlib.machinery', 'urllib', 'urllib.parse'
])

# Strategy for valid relative paths
relative_paths = st.text(
    alphabet=st.characters(whitelist_categories=['Ll', 'Lu', 'Nd'], min_codepoint=33),
    min_size=1,
    max_size=30
).filter(lambda x: not x.startswith('/') and ':' not in x and '..' not in x)


class TestAssetResolver:
    
    @given(st.text(min_size=1, max_size=100))
    def test_absolute_path_resolution_consistency(self, path):
        """Absolute paths should always resolve to FSAssetDescriptor"""
        assume(path.startswith('/'))
        assume(':' not in path)
        
        resolver = AssetResolver(package=None)
        descriptor = resolver.resolve(path)
        
        assert isinstance(descriptor, FSAssetDescriptor)
        assert descriptor.abspath() == os.path.abspath(path)
    
    @given(
        valid_package_names,
        relative_paths
    )
    def test_relative_spec_resolution(self, package_name, rel_path):
        """Relative specs should resolve to PkgResourcesAssetDescriptor with correct package"""
        resolver = AssetResolver(package=package_name)
        descriptor = resolver.resolve(rel_path)
        
        assert isinstance(descriptor, PkgResourcesAssetDescriptor)
        assert descriptor.pkg_name == package_name
        assert descriptor.path == rel_path
        assert descriptor.absspec() == f"{package_name}:{rel_path}"
    
    @given(
        valid_package_names,
        relative_paths
    )
    def test_absolute_spec_format(self, package_name, path):
        """Absolute asset specs with colon should parse correctly"""
        spec = f"{package_name}:{path}"
        resolver = AssetResolver(package=None)
        descriptor = resolver.resolve(spec)
        
        assert isinstance(descriptor, PkgResourcesAssetDescriptor)
        assert descriptor.pkg_name == package_name
        assert descriptor.path == path
        assert descriptor.absspec() == spec


class TestDottedNameResolver:
    
    @given(valid_package_names)
    def test_resolve_valid_modules(self, module_name):
        """Valid module names should resolve to actual modules"""
        resolver = DottedNameResolver()
        result = resolver.resolve(module_name)
        
        assert result is not None
        assert hasattr(result, '__name__') or callable(result) or isinstance(result, type)
    
    @given(valid_package_names)
    def test_maybe_resolve_preserves_non_strings(self, module_name):
        """maybe_resolve should return non-string objects unchanged"""
        __import__(module_name)
        module = sys.modules[module_name]
        
        resolver = DottedNameResolver()
        result = resolver.maybe_resolve(module)
        
        assert result is module
    
    @given(valid_package_names)
    def test_maybe_resolve_resolves_strings(self, module_name):
        """maybe_resolve should resolve string module names"""
        resolver = DottedNameResolver()
        result = resolver.maybe_resolve(module_name)
        
        assert result is not None
        assert result.__name__ == module_name or hasattr(result, '__module__')
    
    @given(st.sampled_from(['os.path', 'sys.path', 'json.dumps', 'urllib.parse.quote']))
    def test_dotted_attribute_resolution(self, dotted_name):
        """Should resolve module attributes using dotted notation"""
        resolver = DottedNameResolver()
        
        # Test zope.dottedname style
        result_dot = resolver.resolve(dotted_name)
        
        # Test pkg_resources style
        parts = dotted_name.rsplit('.', 1)
        if len(parts) == 2:
            colon_name = f"{parts[0]}:{parts[1]}"
            result_colon = resolver.resolve(colon_name)
            
            # Both styles should resolve to the same object
            assert result_dot is result_colon


class TestPackageFunctions:
    
    @given(valid_package_names)
    def test_package_name_idempotence(self, pkg_name):
        """package_name should be idempotent for packages"""
        __import__(pkg_name)
        module = sys.modules[pkg_name]
        
        name1 = package_name(module)
        
        # Re-import and get name again
        __import__(name1)
        module2 = sys.modules[name1]
        name2 = package_name(module2)
        
        # For packages, applying package_name twice should give same result
        assert name1 == name2 or name1.startswith(name2) or name2.startswith(name1)
    
    @given(valid_package_names)
    def test_package_of_returns_package(self, pkg_name):
        """package_of should return a valid package module"""
        __import__(pkg_name)
        module = sys.modules[pkg_name]
        
        package = package_of(module)
        
        assert package is not None
        assert hasattr(package, '__name__')
        assert package.__name__ in sys.modules


class TestAssetDescriptors:
    
    @given(st.text(min_size=1, max_size=100))
    def test_fs_descriptor_abspath_absolute(self, path):
        """FSAssetDescriptor should always return absolute paths"""
        descriptor = FSAssetDescriptor(path)
        result = descriptor.abspath()
        
        assert os.path.isabs(result)
        assert descriptor.path == result
    
    @given(st.text(min_size=1, max_size=100))
    def test_fs_descriptor_methods_dont_crash(self, path):
        """FSAssetDescriptor methods shouldn't crash on any input"""
        descriptor = FSAssetDescriptor(path)
        
        # These should not crash
        _ = descriptor.abspath()
        _ = descriptor.exists()
        _ = descriptor.isdir()
        
        # listdir might fail but shouldn't crash the process
        try:
            _ = descriptor.listdir()
        except (OSError, IOError):
            pass  # Expected for non-directories
    
    def test_fs_descriptor_real_file(self):
        """FSAssetDescriptor should correctly identify real files"""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            f.flush()
            path = f.name
        
        try:
            descriptor = FSAssetDescriptor(path)
            
            assert descriptor.exists() is True
            assert descriptor.isdir() is False
            assert descriptor.abspath() == os.path.abspath(path)
            
            # Should be able to open stream
            with descriptor.stream() as stream:
                content = stream.read()
                assert content == b"test content"
        finally:
            os.unlink(path)
    
    def test_fs_descriptor_real_directory(self):
        """FSAssetDescriptor should correctly identify real directories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file in the directory
            test_file = os.path.join(tmpdir, "test.txt")
            Path(test_file).write_text("content")
            
            descriptor = FSAssetDescriptor(tmpdir)
            
            assert descriptor.exists() is True
            assert descriptor.isdir() is True
            assert descriptor.abspath() == os.path.abspath(tmpdir)
            
            # Should list directory contents
            contents = descriptor.listdir()
            assert "test.txt" in contents


class TestErrorHandling:
    
    @given(st.text(min_size=1).filter(lambda x: ':' not in x and not x.startswith('/')))
    def test_resolver_without_package_raises_on_relative(self, spec):
        """AssetResolver with no package should raise on relative specs"""
        resolver = AssetResolver(package=None)
        
        with pytest.raises(ValueError, match="irresolveable without package"):
            resolver.resolve(spec)
    
    @given(st.one_of(st.integers(), st.lists(st.text()), st.dictionaries(st.text(), st.text())))
    def test_dotted_resolver_raises_on_non_string(self, non_string):
        """DottedNameResolver.resolve should raise ValueError for non-strings"""
        resolver = DottedNameResolver()
        
        with pytest.raises(ValueError, match="is not a string"):
            resolver.resolve(non_string)
    
    def test_dotted_resolver_relative_without_package(self):
        """DottedNameResolver should raise on relative names without package"""
        resolver = DottedNameResolver(package=None)
        
        with pytest.raises(ValueError, match="irresolveable without package"):
            resolver.resolve(".relative")
        
        with pytest.raises(ValueError, match="irresolveable without package"):
            resolver.resolve(":relative")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])