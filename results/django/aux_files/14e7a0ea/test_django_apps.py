"""
Property-based tests for django.apps module
"""
import django
from django.conf import settings
from django.apps import apps, AppConfig
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


# Strategy for generating case variations of a string
def case_variations(s):
    """Generate different case variations of a string"""
    variations = []
    for i in range(min(2**len(s), 100)):  # Limit to avoid exponential explosion
        variant = ""
        for j, char in enumerate(s):
            if (i >> j) & 1:
                variant += char.upper()
            else:
                variant += char.lower()
        variations.append(variant)
    return variations


@given(st.sampled_from(['User', 'Group', 'Permission']))
def test_model_name_case_insensitive(model_name):
    """
    Property: AppConfig.get_model should be case-insensitive
    Based on docstring: "Return the model with the given case-insensitive model_name."
    """
    auth_app = apps.get_app_config('auth')
    
    # Get the model with original case
    original_model = auth_app.get_model(model_name)
    
    # Test various case variations
    for variant in case_variations(model_name)[:10]:  # Test first 10 variations
        retrieved_model = auth_app.get_model(variant)
        assert retrieved_model is original_model, \
            f"get_model('{variant}') returned different model than get_model('{model_name}')"


@given(st.sampled_from(['auth', 'contenttypes', 'admin', 'sessions', 'messages']))
def test_get_app_config_round_trip(app_label):
    """
    Property: apps.get_app_config(app.label) should return the same app config object
    """
    # Get the app config
    app_config = apps.get_app_config(app_label)
    
    # Round-trip: get it again using its label
    retrieved_config = apps.get_app_config(app_config.label)
    
    # They should be the same object
    assert app_config is retrieved_config, \
        f"Round-trip failed: get_app_config('{app_label}') != get_app_config(app.label)"


def test_all_apps_are_installed():
    """
    Property: All apps from get_app_configs() should report as installed via is_installed()
    """
    for app_config in apps.get_app_configs():
        assert apps.is_installed(app_config.name), \
            f"App '{app_config.name}' from get_app_configs() not reported as installed"


def test_model_retrieval_invariant():
    """
    Property: All models from AppConfig.get_models() should be retrievable via get_model()
    """
    for app_config in apps.get_app_configs():
        models = app_config.get_models()
        for model in models:
            # Should be able to retrieve the model by its name
            retrieved = app_config.get_model(model.__name__)
            assert model is retrieved, \
                f"Model {model.__name__} from get_models() not retrievable via get_model()"


@given(st.text(alphabet=string.ascii_letters + string.digits + '_', min_size=1, max_size=20))
def test_get_model_with_nonexistent_name(model_name):
    """
    Property: get_model with non-existent name should raise LookupError
    """
    auth_app = apps.get_app_config('auth')
    
    # Skip if this happens to be a real model name
    real_models = {m.__name__.lower() for m in auth_app.get_models()}
    assume(model_name.lower() not in real_models)
    
    with pytest.raises(LookupError) as exc_info:
        auth_app.get_model(model_name)
    
    assert f"doesn't have a '{model_name}' model" in str(exc_info.value)


@given(st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=20))
def test_get_app_config_with_nonexistent_label(app_label):
    """
    Property: get_app_config with non-existent label should raise LookupError
    """
    # Skip if this happens to be a real app label
    real_labels = {app.label for app in apps.get_app_configs()}
    assume(app_label not in real_labels)
    
    with pytest.raises(LookupError) as exc_info:
        apps.get_app_config(app_label)
    
    assert f"No installed app with label '{app_label}'" in str(exc_info.value)


@given(st.sampled_from(['auth', 'contenttypes', 'admin']))
def test_get_app_config_case_sensitive(app_label):
    """
    Property: get_app_config should be case-SENSITIVE for app labels
    (Unlike get_model which is case-insensitive)
    """
    # This should work
    app_config = apps.get_app_config(app_label)
    
    # This should fail with uppercase
    upper_label = app_label.upper()
    if upper_label != app_label:  # Only test if actually different
        with pytest.raises(LookupError):
            apps.get_app_config(upper_label)


def test_get_models_consistency():
    """
    Property: get_models() from Apps should include all models from individual AppConfigs
    """
    # Get all models from individual app configs
    all_models_from_apps = set()
    for app_config in apps.get_app_configs():
        all_models_from_apps.update(app_config.get_models())
    
    # Get all models from the registry
    all_models_from_registry = set(apps.get_models())
    
    # They should be the same
    assert all_models_from_apps == all_models_from_registry, \
        "Models from individual apps don't match models from registry"


@given(st.booleans(), st.booleans())
def test_get_models_parameters_consistency(include_auto_created, include_swapped):
    """
    Property: AppConfig.get_models and Apps.get_models with same parameters should be consistent
    """
    # Get models from registry with parameters
    registry_models = set(apps.get_models(
        include_auto_created=include_auto_created,
        include_swapped=include_swapped
    ))
    
    # Get models from individual apps with same parameters
    app_models = set()
    for app_config in apps.get_app_configs():
        app_models.update(app_config.get_models(
            include_auto_created=include_auto_created,
            include_swapped=include_swapped
        ))
    
    # They should match
    assert registry_models == app_models, \
        f"Models mismatch with include_auto_created={include_auto_created}, include_swapped={include_swapped}"


@given(st.sampled_from([
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages'
]))
def test_is_installed_with_full_name(app_name):
    """
    Property: is_installed should return True for all configured apps using their full name
    """
    assert apps.is_installed(app_name), f"is_installed('{app_name}') returned False"


@given(st.text(alphabet=string.ascii_letters + '.', min_size=1, max_size=50))
def test_is_installed_with_nonexistent_app(app_name):
    """
    Property: is_installed should return False for non-existent apps
    """
    # Skip if this happens to be a real app name
    real_names = {app.name for app in apps.get_app_configs()}
    assume(app_name not in real_names)
    
    assert not apps.is_installed(app_name), \
        f"is_installed('{app_name}') returned True for non-existent app"


@hyp_settings(max_examples=200)
@given(st.sampled_from(['django.contrib.auth', 'django.contrib.contenttypes']))
def test_app_config_create_idempotence(app_entry):
    """
    Property: AppConfig.create should produce equivalent configs for the same entry
    """
    # Create two app configs from the same entry
    config1 = AppConfig.create(app_entry)
    config2 = AppConfig.create(app_entry)
    
    # They should have the same properties
    assert config1.name == config2.name, "Names don't match"
    assert config1.label == config2.label, "Labels don't match"
    assert config1.verbose_name == config2.verbose_name, "Verbose names don't match"
    # Note: They won't be the same object, but should be equivalent


if __name__ == "__main__":
    # Run a quick smoke test
    print("Running property-based tests for django.apps...")
    test_model_name_case_insensitive('User')
    test_get_app_config_round_trip('auth')
    test_all_apps_are_installed()
    test_model_retrieval_invariant()
    test_get_models_consistency()
    print("Basic tests passed! Run with pytest for full suite.")