import sys
import importlib
from hypothesis import given, strategies as st, assume, settings
import pytest


def test_identity_preservation():
    """Test that requests.packages preserves module identity"""
    import requests.packages
    import urllib3
    import idna
    
    # Identity preservation for urllib3
    import requests.packages.urllib3
    assert urllib3 is requests.packages.urllib3, "urllib3 identity not preserved"
    
    # Identity preservation for idna
    import requests.packages.idna  
    assert idna is requests.packages.idna, "idna identity not preserved"


def test_submodule_hierarchy_preservation():
    """Test that all submodules are properly aliased"""
    import requests.packages
    import urllib3.exceptions
    import urllib3.util.retry
    import idna.core
    
    # Check urllib3 submodules
    import requests.packages.urllib3.exceptions
    assert urllib3.exceptions is requests.packages.urllib3.exceptions
    
    import requests.packages.urllib3.util.retry
    assert urllib3.util.retry is requests.packages.urllib3.util.retry
    
    # Check idna submodules
    import requests.packages.idna.core
    assert idna.core is requests.packages.idna.core


def test_dual_naming_chardet_charset_normalizer():
    """Test that both chardet and charset_normalizer names work"""
    import requests.packages
    
    # Both should point to the same module
    chardet_module = sys.modules.get('requests.packages.chardet')
    charset_module = sys.modules.get('requests.packages.charset_normalizer')
    
    assert chardet_module is not None, "requests.packages.chardet not found"
    assert charset_module is not None, "requests.packages.charset_normalizer not found"
    assert chardet_module is charset_module, "chardet and charset_normalizer are not the same"
    
    # Check submodules too
    chardet_api = sys.modules.get('requests.packages.chardet.api')
    charset_api = sys.modules.get('requests.packages.charset_normalizer.api')
    
    assert chardet_api is not None
    assert charset_api is not None
    assert chardet_api is charset_api


@given(st.sampled_from(['urllib3', 'idna']))
def test_sys_modules_registration(package_name):
    """Property: All aliased modules are properly registered in sys.modules"""
    import requests.packages
    
    # Get all modules that start with the package name
    original_modules = [m for m in sys.modules if m == package_name or m.startswith(f"{package_name}.")]
    aliased_modules = [m for m in sys.modules if m == f"requests.packages.{package_name}" 
                       or m.startswith(f"requests.packages.{package_name}.")]
    
    # For each original module, there should be a corresponding aliased module
    for orig_mod in original_modules:
        aliased_name = f"requests.packages.{orig_mod}"
        assert aliased_name in sys.modules, f"Module {aliased_name} not in sys.modules"
        
        # They should be the same object
        assert sys.modules[orig_mod] is sys.modules[aliased_name], \
            f"Module identity not preserved for {orig_mod}"


@given(st.sampled_from(['charset_normalizer', 'chardet']))
def test_chardet_charset_normalizer_aliasing_consistency(name_variant):
    """Property: Both chardet and charset_normalizer paths resolve to same modules"""
    import requests.packages
    import charset_normalizer
    
    # Get all charset_normalizer submodules
    charset_modules = [m for m in sys.modules 
                      if m == 'charset_normalizer' or m.startswith('charset_normalizer.')]
    
    for charset_mod in charset_modules:
        # Replace charset_normalizer with the name variant
        if name_variant == 'chardet':
            aliased_name = charset_mod.replace('charset_normalizer', 'chardet')
        else:
            aliased_name = charset_mod
        
        requests_aliased = f"requests.packages.{aliased_name}"
        
        # Check if the alias exists in sys.modules
        if requests_aliased in sys.modules:
            # They should point to the same module
            assert sys.modules[charset_mod] is sys.modules[requests_aliased], \
                f"Module {charset_mod} and {requests_aliased} are not the same object"


def test_import_order_independence():
    """Test that import order doesn't affect identity preservation"""
    # Clear relevant modules from sys.modules to test fresh import
    modules_to_clear = [m for m in list(sys.modules.keys()) 
                       if 'requests.packages' in m and m != 'requests.packages']
    for mod in modules_to_clear:
        del sys.modules[mod]
    
    # Import in different order
    import requests.packages.urllib3.exceptions
    import urllib3.exceptions
    
    assert urllib3.exceptions is requests.packages.urllib3.exceptions


@given(st.lists(st.sampled_from(['urllib3', 'idna', 'charset_normalizer']), 
                min_size=1, max_size=3, unique=True))
def test_multiple_package_import_consistency(packages):
    """Test that importing multiple packages maintains consistency"""
    import requests.packages
    
    for package in packages:
        if package == 'charset_normalizer':
            # This package might not have direct import
            continue
        
        # Import the original package
        orig_module = importlib.import_module(package)
        
        # Import via requests.packages
        aliased_module = importlib.import_module(f'requests.packages.{package}')
        
        # They should be the same
        assert orig_module is aliased_module, f"{package} identity not preserved"


def test_chardet_submodule_double_aliasing():
    """Test the double aliasing behavior for charset_normalizer submodules"""
    import requests.packages
    
    # Check that charset_normalizer submodules have both aliases
    charset_submodules = ['api', 'version', 'constant', 'utils', 'models']
    
    for submod in charset_submodules:
        chardet_path = f'requests.packages.chardet.{submod}'
        charset_path = f'requests.packages.charset_normalizer.{submod}'
        
        if chardet_path in sys.modules and charset_path in sys.modules:
            assert sys.modules[chardet_path] is sys.modules[charset_path], \
                f"Double aliasing failed for {submod}"


@given(st.sampled_from(['urllib3.util', 'urllib3.util.retry', 'idna.core']))
def test_deep_submodule_preservation(submodule_path):
    """Test that deeply nested submodules maintain identity"""
    import requests.packages
    
    # Import original
    orig = importlib.import_module(submodule_path)
    
    # Import aliased
    aliased = importlib.import_module(f'requests.packages.{submodule_path}')
    
    assert orig is aliased, f"Identity not preserved for {submodule_path}"