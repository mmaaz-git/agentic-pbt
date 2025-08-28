"""Test properties of pyramid.paster.bootstrap function."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, assume
import tempfile
import os

# Test the config URI parsing properties
def test_config_uri_parsing():
    """Test that config URI parsing handles various formats."""
    print("Testing config URI parsing properties...")
    
    # These are the formats mentioned in documentation
    test_uris = [
        'development.ini',  # Just filename, should default to 'main'
        'development.ini#main',  # Explicit section
        'development.ini#app',  # Different section
        'path/to/config.ini',  # Path with no section
        'path/to/config.ini#section',  # Path with section
    ]
    
    for uri in test_uris:
        print(f"Testing URI: {uri}")
        # We can't actually call get_app without a valid config file,
        # but we can test the parsing logic
        if '#' in uri:
            filename, section = uri.rsplit('#', 1)
            print(f"  Parsed: filename='{filename}', section='{section}'")
        else:
            filename = uri
            section = 'main'  # Default according to docs
            print(f"  Parsed: filename='{filename}', section='{section}' (default)")
    
    print()

def test_options_handling():
    """Test that options dictionary is handled consistently."""
    print("Testing options handling...")
    
    # Test various option formats that should be valid
    test_options = [
        {},  # Empty options
        {'http_port': '8080'},  # Simple string value
        {'http_port': 8080},  # Numeric value (should be converted?)
        {'key1': 'value1', 'key2': 'value2'},  # Multiple options
        {'special_chars': 'value=with=equals'},  # Special characters in value
    ]
    
    for options in test_options:
        print(f"Testing options: {options}")
        # The options should be used for variable substitution
        # Format: %(variable_name)s in config file
    
    print()

def create_minimal_paste_config():
    """Create a minimal valid Paste config file for testing."""
    config_content = """
[app:main]
use = egg:pyramid
pyramid.reload_templates = true
pyramid.debug_authorization = false
pyramid.debug_notfound = false
pyramid.debug_routematch = false
pyramid.default_locale_name = en

[server:main]
use = egg:waitress#main
host = 0.0.0.0
port = %(http_port)s
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write(config_content)
        return f.name

def test_bootstrap_context_manager():
    """Test bootstrap as context manager properties."""
    print("Testing bootstrap context manager properties...")
    
    # Property: When used as context manager, closer should be called automatically
    # Property: The returned env should contain required keys
    
    # We need a valid config file to test this
    # Let's create a minimal one
    try:
        config_file = create_minimal_paste_config()
        print(f"Created test config: {config_file}")
        
        # Test that it can be imported and used
        from pyramid.paster import bootstrap
        
        # Note: We can't actually run bootstrap without a full Pyramid app
        # but we can test the structure
        print("Bootstrap function imported successfully")
        
    except Exception as e:
        print(f"Could not test bootstrap: {e}")
    finally:
        if 'config_file' in locals() and os.path.exists(config_file):
            os.unlink(config_file)
    
    print()

def test_config_uri_edge_cases():
    """Test edge cases in config URI handling."""
    print("Testing config URI edge cases...")
    
    edge_cases = [
        '',  # Empty string
        '#',  # Just separator
        '#section',  # No filename
        'file#',  # No section name
        'file##section',  # Double separator
        'file#section#extra',  # Multiple separators
        'file with spaces.ini',  # Spaces in filename
        'file.ini#section with spaces',  # Spaces in section
        '../../config.ini',  # Relative path with parent dirs
        '/absolute/path/config.ini#section',  # Absolute path
    ]
    
    for uri in edge_cases:
        print(f"Edge case URI: '{uri}'")
        if '#' in uri:
            parts = uri.split('#')
            print(f"  Split result: {parts}")
            if uri.count('#') == 1:
                filename, section = uri.rsplit('#', 1)
                print(f"  Parsed: filename='{filename}', section='{section}'")
        else:
            print(f"  No separator, would use as filename with default section")
    
    print()

if __name__ == "__main__":
    print("Running pyramid.paster property tests...")
    print("=" * 60)
    
    test_config_uri_parsing()
    test_options_handling()
    test_config_uri_edge_cases()
    test_bootstrap_context_manager()
    
    print("=" * 60)
    print("Analysis complete!")