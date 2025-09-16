import json
import sys
import platform
from collections import OrderedDict
from hypothesis import given, strategies as st, settings, assume
import pytest

# Import from the virtual environment's site-packages
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')
import cloudscraper.help as help_module


def test_getPossibleCiphers_type_invariant():
    """getPossibleCiphers should return either a sorted list of strings or the error message string"""
    result = help_module.getPossibleCiphers()
    
    if isinstance(result, str):
        # Should be the specific error message
        assert result == 'get_ciphers() is unsupported'
    else:
        # Should be a list
        assert isinstance(result, list)
        # All elements should be strings
        assert all(isinstance(cipher, str) for cipher in result)
        # Should be sorted
        assert result == sorted(result)


def test_pythonVersion_structure_invariant():
    """_pythonVersion should always return dict with 'name' and 'version' string keys"""
    result = help_module._pythonVersion()
    
    # Should be a dictionary
    assert isinstance(result, dict)
    # Should have exactly these keys
    assert set(result.keys()) == {'name', 'version'}
    # Both values should be strings
    assert isinstance(result['name'], str)
    assert isinstance(result['version'], str)
    # Name should match platform implementation
    assert result['name'] == platform.python_implementation()


def test_systemInfo_structure_invariant():
    """systemInfo should return OrderedDict with expected structure"""
    result = help_module.systemInfo()
    
    # Should be an OrderedDict
    assert isinstance(result, OrderedDict)
    
    # Should have exactly these keys
    expected_keys = ['platform', 'interpreter', 'cloudscraper', 'requests', 'urllib3', 'OpenSSL']
    assert list(result.keys()) == expected_keys
    
    # Platform should be a dict with 'system' and 'release' keys
    assert isinstance(result['platform'], dict)
    assert set(result['platform'].keys()) == {'system', 'release'}
    
    # Interpreter should match _pythonVersion output
    assert result['interpreter'] == help_module._pythonVersion()
    
    # OpenSSL should be OrderedDict with 'version' and 'ciphers' keys
    assert isinstance(result['OpenSSL'], OrderedDict)
    assert list(result['OpenSSL'].keys()) == ['version', 'ciphers']


def test_systemInfo_json_serializable():
    """systemInfo output should be JSON serializable (as shown in __main__ block)"""
    result = help_module.systemInfo()
    
    # Should not raise an exception
    json_str = json.dumps(result, indent=4)
    assert isinstance(json_str, str)
    
    # Should be able to parse it back
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    
    # Keys should be preserved
    assert set(parsed.keys()) == set(result.keys())


@given(st.integers(min_value=0, max_value=10))
def test_systemInfo_deterministic(dummy_param):
    """systemInfo should be deterministic - multiple calls should return same structure"""
    result1 = help_module.systemInfo()
    result2 = help_module.systemInfo()
    
    # Structure should be identical
    assert list(result1.keys()) == list(result2.keys())
    assert result1['platform'].keys() == result2['platform'].keys()
    assert result1['interpreter'] == result2['interpreter']
    assert list(result1['OpenSSL'].keys()) == list(result2['OpenSSL'].keys())


def test_pythonVersion_pypy_coverage():
    """Test PyPy version handling if running on PyPy"""
    result = help_module._pythonVersion()
    
    if result['name'] == 'PyPy':
        # Version should be in expected format
        version_parts = result['version'].split('.')
        # Should have at least major.minor.micro
        assert len(version_parts) >= 3
        # First three parts should be numeric (before any release level)
        for i in range(min(3, len(version_parts))):
            # Handle case where releaselevel is appended without separator
            numeric_part = version_parts[i]
            for suffix in ['alpha', 'beta', 'candidate', 'final']:
                if suffix in numeric_part:
                    numeric_part = numeric_part.split(suffix)[0]
            assert numeric_part.isdigit(), f"Part {i} ({version_parts[i]}) should start with digits"


def test_systemInfo_version_strings():
    """All version fields should be non-empty strings"""
    result = help_module.systemInfo()
    
    # cloudscraper version should be a string
    assert isinstance(result['cloudscraper'], str)
    assert len(result['cloudscraper']) > 0
    
    # requests version should be a string  
    assert isinstance(result['requests'], str)
    assert len(result['requests']) > 0
    
    # urllib3 version should be a string
    assert isinstance(result['urllib3'], str)
    assert len(result['urllib3']) > 0
    
    # OpenSSL version should be a string
    assert isinstance(result['OpenSSL']['version'], str)
    assert len(result['OpenSSL']['version']) > 0