"""Property-based tests for django.shortcuts module"""

import os
import sys
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

from hypothesis import given, strategies as st, assume, settings as hyp_settings
from django.shortcuts import resolve_url, redirect, _get_queryset
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.urls import NoReverseMatch
import string


# Strategy for generating relative URLs starting with ./ or ../
relative_url_strategy = st.one_of(
    st.text(min_size=1).map(lambda s: f"./{s}"),
    st.text(min_size=1).map(lambda s: f"../{s}"),
    st.text(min_size=0).map(lambda s: f"./{s}/").filter(lambda s: s != ".//"),
    st.text(min_size=0).map(lambda s: f"../{s}/").filter(lambda s: s != "..//"),
)

# Strategy for generating URL-like strings
url_like_strategy = st.one_of(
    st.text(alphabet=string.ascii_letters + string.digits + "/-._~:?#[]@!$&'()*+,;=", min_size=1).filter(
        lambda s: ("/" in s or "." in s) and not s.startswith("./") and not s.startswith("../")
    ),
    st.text(min_size=1).map(lambda s: f"http://example.com/{s}"),
    st.text(min_size=1).map(lambda s: f"https://example.com/{s}"),
    st.text(min_size=1).map(lambda s: f"/path/{s}"),
    st.text(min_size=1).map(lambda s: f"path/{s}/page.html"),
)


@given(relative_url_strategy)
@hyp_settings(max_examples=500)
def test_resolve_url_preserves_relative_urls(url):
    """Property: resolve_url() returns relative URLs starting with ./ or ../ unchanged"""
    result = resolve_url(url)
    assert result == url, f"resolve_url({url!r}) returned {result!r}, expected {url!r}"


@given(url_like_strategy)
@hyp_settings(max_examples=500)
def test_resolve_url_passthrough_for_urls(url):
    """Property: resolve_url() returns URL-like strings as-is when reverse() fails"""
    # This should work for strings that look like URLs (contain / or .)
    # and don't match any reverse patterns
    try:
        result = resolve_url(url)
        # If it looks like a URL (has / or .), it should be returned as-is
        # unless it's a valid view name that can be reversed
        assert isinstance(result, str)
        # The result should either be the original URL or a reversed URL
        # But never raise an exception for URL-like strings
    except NoReverseMatch:
        # According to lines 189-191, if the string contains "/" or "."
        # it should NOT raise NoReverseMatch - it should return as-is
        assert "/" not in url and "." not in url, \
            f"resolve_url({url!r}) raised NoReverseMatch but url contains '/' or '.'"


@given(url_like_strategy, st.booleans(), st.booleans())
@hyp_settings(max_examples=500)
def test_redirect_returns_correct_class(url, permanent, preserve_request):
    """Property: redirect() returns correct response class based on permanent flag"""
    try:
        response = redirect(url, permanent=permanent, preserve_request=preserve_request)
        
        if permanent:
            assert isinstance(response, HttpResponsePermanentRedirect), \
                f"redirect(permanent=True) returned {type(response).__name__}, expected HttpResponsePermanentRedirect"
        else:
            assert isinstance(response, HttpResponseRedirect), \
                f"redirect(permanent=False) returned {type(response).__name__}, expected HttpResponseRedirect"
        
        # Check preserve_request is passed through
        if preserve_request:
            assert hasattr(response, 'preserve_request') and response.preserve_request == True, \
                "redirect(preserve_request=True) did not preserve request"
    except NoReverseMatch:
        # This is acceptable if the URL can't be reversed and doesn't look like a URL
        pass


class MockModel:
    """Mock model with _default_manager attribute"""
    class _default_manager:
        @staticmethod
        def all():
            return "mock_queryset"


class MockQuerySet:
    """Mock queryset without _default_manager"""
    pass


@given(st.sampled_from([MockModel, MockModel(), MockQuerySet, MockQuerySet(), "string", 123, None]))
def test_get_queryset_behavior(klass):
    """Property: _get_queryset returns manager.all() for models, klass otherwise"""
    result = _get_queryset(klass)
    
    if hasattr(klass, "_default_manager"):
        # Should return klass._default_manager.all()
        assert result == "mock_queryset", \
            f"_get_queryset with _default_manager didn't return manager.all()"
    else:
        # Should return klass unchanged
        assert result is klass, \
            f"_get_queryset without _default_manager didn't return input unchanged"


# Test for edge cases in resolve_url with Promise objects
@given(st.text())
def test_resolve_url_handles_promise(text):
    """Property: resolve_url converts Promise objects to strings"""
    from django.utils.functional import Promise
    
    class MockPromise(Promise):
        def __init__(self, value):
            self.value = value
        
        def __str__(self):
            return self.value
    
    promise = MockPromise(text)
    
    # Test that Promise is converted to string
    if text.startswith("./") or text.startswith("../"):
        # Relative URLs should be preserved
        result = resolve_url(promise)
        assert result == text
    elif "/" in text or "." in text:
        # URL-like strings should be returned
        try:
            result = resolve_url(promise)
            assert isinstance(result, str)
        except NoReverseMatch:
            # Should not raise for URL-like strings
            assert "/" not in text and "." not in text
    else:
        # Other strings might raise NoReverseMatch
        try:
            result = resolve_url(promise)
            assert isinstance(result, str)
        except NoReverseMatch:
            pass  # This is acceptable for non-URL strings


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])