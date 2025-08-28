"""
Property-based tests for AppConfig.create method
"""
import django
from django.conf import settings
from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured
from hypothesis import given, strategies as st, assume
import pytest
import sys
from unittest.mock import patch


def setup_django():
    """Configure minimal Django settings for testing"""
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY='test-secret-key',
            INSTALLED_APPS=[],
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            }
        )
        django.setup()


setup_django()


def test_app_config_create_with_existing_apps():
    """
    Property: AppConfig.create should work with known Django apps
    """
    # Test with various Django built-in apps
    test_apps = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.admin',
    ]
    
    for app_entry in test_apps:
        config = AppConfig.create(app_entry)
        assert config.name == app_entry
        assert config.label is not None
        assert config.module is not None


def test_app_config_create_with_app_config_class():
    """
    Property: AppConfig.create should handle AppConfig subclass paths
    """
    # Test with actual AppConfig class path
    config = AppConfig.create('django.contrib.admin.apps.AdminConfig')
    assert config.name == 'django.contrib.admin'
    assert config.label == 'admin'


def test_app_config_create_with_nonexistent_module():
    """
    Property: AppConfig.create with non-existent module should raise ImportError
    """
    with pytest.raises(ImportError):
        AppConfig.create('totally.nonexistent.module')


def test_app_config_create_with_invalid_app_config_class():
    """
    Property: AppConfig.create with invalid class path should raise appropriate error
    """
    # Module exists but class doesn't
    with pytest.raises(ImportError) as exc_info:
        AppConfig.create('django.contrib.auth.NonExistentConfig')
    
    assert "does not contain a 'NonExistentConfig' class" in str(exc_info.value)


def test_app_config_create_uppercase_class_heuristic():
    """
    Property: AppConfig.create uses uppercase heuristic to determine if entry is a class
    """
    # Test that it provides helpful error for typos
    with pytest.raises(ImportError) as exc_info:
        AppConfig.create('django.contrib.auth.AppsConfig')  # Typo: should be AppConfig
    
    # Should suggest available choices
    assert "does not contain a 'AppsConfig' class" in str(exc_info.value)


def test_app_config_create_not_subclass():
    """
    Property: AppConfig.create should reject non-AppConfig classes
    """
    # Try to create with a class that exists but isn't an AppConfig
    with pytest.raises(ImproperlyConfigured) as exc_info:
        AppConfig.create('django.contrib.auth.models.User')
    
    assert "isn't a subclass of AppConfig" in str(exc_info.value)


@given(st.sampled_from(['django.contrib.auth', 'django.contrib.contenttypes']))
def test_app_config_create_multiple_times(app_entry):
    """
    Property: Multiple calls to AppConfig.create should work without side effects
    """
    # Create multiple configs
    configs = [AppConfig.create(app_entry) for _ in range(3)]
    
    # All should have same properties
    for config in configs[1:]:
        assert config.name == configs[0].name
        assert config.label == configs[0].label
        
    # But they should be different instances
    for i, config in enumerate(configs[1:], 1):
        assert config is not configs[0], f"Config {i} is same object as config 0"


def test_empty_string_app_config_create():
    """
    Property: AppConfig.create with empty string should raise appropriate error
    """
    with pytest.raises((ImportError, ValueError)):
        AppConfig.create('')


@given(st.text(alphabet=' \t\n', min_size=1, max_size=10))
def test_whitespace_only_app_config_create(whitespace):
    """
    Property: AppConfig.create with only whitespace should raise appropriate error
    """
    with pytest.raises((ImportError, ValueError)):
        AppConfig.create(whitespace)


def test_app_config_create_with_trailing_dot():
    """
    Property: Module paths with trailing dots should be handled appropriately
    """
    with pytest.raises(ImportError):
        AppConfig.create('django.contrib.auth.')
    
    with pytest.raises(ImportError):
        AppConfig.create('django.contrib.auth..')


def test_app_config_create_with_leading_dot():
    """
    Property: Relative imports (leading dots) should be handled
    """
    with pytest.raises((ImportError, ValueError)):
        AppConfig.create('.auth')
    
    with pytest.raises((ImportError, ValueError)):
        AppConfig.create('..auth')


@given(st.integers())
def test_app_config_create_with_non_string(value):
    """
    Property: AppConfig.create with non-string should fail appropriately
    """
    with pytest.raises((TypeError, AttributeError, ImportError)):
        AppConfig.create(value)


def test_app_config_create_with_none():
    """
    Property: AppConfig.create with None should fail appropriately
    """
    with pytest.raises((TypeError, AttributeError)):
        AppConfig.create(None)


def test_app_config_missing_name_attribute():
    """
    Property: AppConfig subclass without name attribute should raise ImproperlyConfigured
    """
    # Create a test AppConfig without a name
    class TestConfig(AppConfig):
        pass
    
    # Mock the import to return our test class
    with patch('django.apps.config.import_string') as mock_import:
        mock_import.return_value = TestConfig
        
        with pytest.raises(ImproperlyConfigured) as exc_info:
            AppConfig.create('test.TestConfig')
        
        assert "must supply a name attribute" in str(exc_info.value)


if __name__ == "__main__":
    print("Testing AppConfig.create edge cases...")
    test_app_config_create_with_existing_apps()
    test_app_config_create_with_app_config_class()
    test_app_config_create_with_nonexistent_module()
    test_empty_string_app_config_create()
    test_app_config_create_with_none()
    print("AppConfig.create tests completed!")