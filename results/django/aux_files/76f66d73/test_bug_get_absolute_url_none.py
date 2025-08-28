"""Property-based test that discovered the get_absolute_url None bug"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-secret-key',
        ROOT_URLCONF='test_urls',
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        USE_TZ=True,
    )
    django.setup()

from hypothesis import given, strategies as st
from django.shortcuts import resolve_url, redirect


class ModelWithGetAbsoluteUrl:
    """Model with configurable get_absolute_url return value"""
    def __init__(self, return_value):
        self.return_value = return_value
    
    def get_absolute_url(self):
        return self.return_value


@given(st.sampled_from([None, "", 0, False]))
def test_resolve_url_handles_falsy_get_absolute_url(value):
    """Property: resolve_url should handle falsy returns from get_absolute_url properly"""
    model = ModelWithGetAbsoluteUrl(value)
    result = resolve_url(model)
    
    # The bug: resolve_url returns the falsy value as-is
    # This causes issues downstream when redirect() tries to use it
    assert result == value, f"resolve_url returned {result!r} for get_absolute_url returning {value!r}"
    
    # The real issue: redirect() then converts these to strings
    if value is None:
        response = redirect(model)
        location = response["Location"]
        # Bug: None becomes "None" in the Location header!
        assert location == "None", f"redirect() converted None to {location!r}"
        print(f"BUG CONFIRMED: get_absolute_url returning None results in Location: 'None'")


# Run the test to demonstrate the bug
if __name__ == "__main__":
    # Direct test without hypothesis decorator
    model = ModelWithGetAbsoluteUrl(None)
    result = resolve_url(model)
    print(f"resolve_url(model with get_absolute_url()=None) returned: {result!r}")
    
    response = redirect(model)
    location = response["Location"]
    print(f"redirect(model) created Location header: {location!r}")
    
    if location == "None":
        print("BUG CONFIRMED: get_absolute_url() returning None results in Location: 'None'")