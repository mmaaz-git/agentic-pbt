"""
Advanced property-based tests for django.apps module - looking for edge cases
"""
import django
from django.conf import settings
from django.apps import apps, AppConfig
from django.core.exceptions import ImproperlyConfigured
from hypothesis import given, strategies as st, assume, settings as hyp_settings
import string
import pytest


def setup_django():
    """Configure minimal Django settings for testing"""
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY='test-secret-key',
            INSTALLED_APPS=[
                'django.contrib.admin',
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.messages',
            ],
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            }
        )
        django.setup()


setup_django()


@given(st.text(alphabet=' \t\n', min_size=1, max_size=10))
def test_model_name_with_whitespace(whitespace):
    """
    Property: get_model with only whitespace should handle gracefully
    """
    auth_app = apps.get_app_config('auth')
    
    with pytest.raises(LookupError) as exc_info:
        auth_app.get_model(whitespace)
    
    # Should raise LookupError, not crash
    assert "doesn't have a" in str(exc_info.value)


@given(st.text(alphabet=string.punctuation, min_size=1, max_size=10))
def test_model_name_with_special_chars(special_chars):
    """
    Property: get_model with special characters should handle gracefully
    """
    auth_app = apps.get_app_config('auth')
    
    with pytest.raises(LookupError) as exc_info:
        auth_app.get_model(special_chars)
    
    assert "doesn't have a" in str(exc_info.value)


def test_empty_model_name():
    """
    Property: get_model with empty string should raise appropriate error
    """
    auth_app = apps.get_app_config('auth')
    
    with pytest.raises((LookupError, KeyError, ValueError)):
        auth_app.get_model('')


def test_empty_app_label():
    """
    Property: get_app_config with empty string should raise appropriate error
    """
    with pytest.raises((LookupError, KeyError)):
        apps.get_app_config('')


@given(st.sampled_from(['User', 'Group', 'Permission']))
def test_model_name_with_mixed_spacing(model_name):
    """
    Property: Model names with internal spaces should be handled consistently
    """
    auth_app = apps.get_app_config('auth')
    
    # Original should work
    original = auth_app.get_model(model_name)
    
    # With spaces should fail appropriately
    spaced_name = ' '.join(model_name)  # U s e r
    if spaced_name != model_name:
        with pytest.raises(LookupError):
            auth_app.get_model(spaced_name)


@given(st.integers(min_value=-1000, max_value=1000))
def test_model_name_as_integer(num):
    """
    Property: get_model should handle non-string input appropriately
    """
    auth_app = apps.get_app_config('auth')
    
    # Should either convert to string or raise appropriate error
    try:
        model = auth_app.get_model(str(num))
        # If it doesn't raise, it should be a LookupError for non-existent model
        assert False, "Should have raised LookupError"
    except LookupError as e:
        assert f"doesn't have a '{num}' model" in str(e)


@given(st.sampled_from(['auth', 'contenttypes', 'admin']))
def test_app_label_with_leading_trailing_spaces(app_label):
    """
    Property: App labels with leading/trailing spaces should be handled
    """
    # Original should work
    original = apps.get_app_config(app_label)
    
    # With spaces should fail
    with pytest.raises(LookupError):
        apps.get_app_config(f" {app_label} ")


def test_get_models_include_auto_created_behavior():
    """
    Property: include_auto_created should affect the result set
    """
    # Get models with and without auto-created
    without_auto = list(apps.get_models(include_auto_created=False))
    with_auto = list(apps.get_models(include_auto_created=True))
    
    # with_auto should be a superset of without_auto
    assert set(without_auto).issubset(set(with_auto)), \
        "Models without auto_created should be subset of models with auto_created"


def test_unicode_in_model_names():
    """
    Property: Unicode characters in model lookups should be handled
    """
    auth_app = apps.get_app_config('auth')
    
    # Test with various unicode strings
    unicode_names = ['用户', 'ユーザー', 'المستخدم', '🦄', 'Üser']
    
    for name in unicode_names:
        with pytest.raises(LookupError) as exc_info:
            auth_app.get_model(name)
        # Should handle gracefully
        assert "doesn't have a" in str(exc_info.value)


@hyp_settings(max_examples=500)
@given(st.text(min_size=1, max_size=100))
def test_model_name_case_insensitive_comprehensive(random_name):
    """
    Property: Any string should either find a model (case-insensitive) or raise LookupError
    """
    auth_app = apps.get_app_config('auth')
    real_models = {m.__name__.lower(): m for m in auth_app.get_models()}
    
    try:
        result = auth_app.get_model(random_name)
        # If it succeeds, it should match a real model (case-insensitive)
        assert random_name.lower() in real_models
        assert result is real_models[random_name.lower()]
    except LookupError as e:
        # If it fails, the error message should be appropriate
        assert "doesn't have a" in str(e) and random_name in str(e)
    except AttributeError:
        # This might happen if the input isn't a string-like object
        pass


def test_null_and_none_handling():
    """
    Property: None as input should be handled appropriately
    """
    auth_app = apps.get_app_config('auth')
    
    # Test with None
    with pytest.raises((TypeError, AttributeError, LookupError)):
        auth_app.get_model(None)
    
    with pytest.raises((TypeError, KeyError, LookupError)):
        apps.get_app_config(None)


@given(st.lists(st.sampled_from(['auth', 'contenttypes', 'admin']), min_size=1, max_size=5))
def test_get_app_config_consistency_across_calls(app_labels):
    """
    Property: Multiple calls to get_app_config should return the same object
    """
    for label in app_labels:
        config1 = apps.get_app_config(label)
        config2 = apps.get_app_config(label)
        assert config1 is config2, f"get_app_config('{label}') returns different objects"


@given(st.booleans())
def test_model_retrieval_with_require_ready_parameter(require_ready):
    """
    Property: get_model with require_ready parameter should work consistently
    """
    auth_app = apps.get_app_config('auth')
    
    # Should work with both True and False
    user_model_true = auth_app.get_model('User', require_ready=True)
    user_model_param = auth_app.get_model('User', require_ready=require_ready)
    
    # Should return the same model
    assert user_model_true is user_model_param


def test_app_config_models_dict_consistency():
    """
    Property: AppConfig.models dict should be consistent with get_models()
    """
    for app_config in apps.get_app_configs():
        if hasattr(app_config, 'models'):
            # models dict keys should be lowercase model names
            models_from_dict = set(app_config.models.values())
            models_from_method = set(app_config.get_models())
            
            # They should contain the same models
            assert models_from_dict == models_from_method, \
                f"AppConfig.models dict inconsistent with get_models() for {app_config.label}"


if __name__ == "__main__":
    print("Running advanced property tests...")
    test_empty_model_name()
    test_empty_app_label()
    test_get_models_include_auto_created_behavior()
    test_unicode_in_model_names()
    test_null_and_none_handling()
    print("Advanced tests completed!")