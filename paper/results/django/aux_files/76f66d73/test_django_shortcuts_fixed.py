"""Property-based tests for django.shortcuts module - focused on edge cases"""

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
from django.utils.functional import Promise
import string


# Test edge cases in resolve_url with empty strings and special characters
@given(st.sampled_from(["", ".", "..", "./", "../", ".//", "..//", "./.", "../.", "././", ".././"]))
def test_resolve_url_edge_cases_relative(path):
    """Test edge cases for relative path handling"""
    result = resolve_url(path)
    
    # According to line 179-180, only paths STARTING with ./ or ../ are preserved
    if path.startswith("./") or path.startswith("../"):
        assert result == path, f"resolve_url({path!r}) should return {path!r}, got {result!r}"
    else:
        # Other paths should be processed normally
        # Empty string, ".", ".." should not be preserved as relative
        assert isinstance(result, str)


@given(st.text(alphabet="/.", min_size=0, max_size=5))
def test_resolve_url_slash_dot_combinations(text):
    """Test various combinations of slashes and dots"""
    try:
        result = resolve_url(text)
        
        # Special handling for relative URLs
        if text.startswith("./") or text.startswith("../"):
            assert result == text
        else:
            # If it contains "/" or "." and doesn't match a view, should return as-is
            # per lines 189-194
            assert isinstance(result, str)
    except NoReverseMatch:
        # According to lines 189-191, should only raise if:
        # 1. It's callable (not the case here)
        # 2. Doesn't "feel" like a URL (no "/" and no ".")
        assert "/" not in text and "." not in text, \
            f"resolve_url({text!r}) raised NoReverseMatch but contains '/' or '.'"


# Test with strings that are exactly "/" or "."
@given(st.sampled_from(["/", ".", "//", "..", "...", "///", "/./", "/../"]))
def test_resolve_url_minimal_urls(path):
    """Test minimal URL-like strings"""
    try:
        result = resolve_url(path)
        
        if path.startswith("./") or path.startswith("../"):
            assert result == path
        else:
            # Should return as-is since they contain "/" or "."
            assert result == path or isinstance(result, str)
    except NoReverseMatch:
        # Should not raise for strings containing "/" or "."
        assert "/" not in path and "." not in path


# Test Promise handling with edge cases
class TestPromise(Promise):
    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return self.value


@given(st.sampled_from(["", ".", "..", "/", "./", "../", None]))
def test_resolve_url_promise_edge_cases(value):
    """Test Promise objects with edge case values"""
    if value is None:
        promise_str = ""
    else:
        promise_str = value
    
    promise = TestPromise(promise_str)
    
    try:
        result = resolve_url(promise)
        
        # Promise should be converted to string first (line 176)
        if promise_str.startswith("./") or promise_str.startswith("../"):
            assert result == promise_str
        else:
            assert isinstance(result, str)
    except NoReverseMatch:
        # Should only raise if string doesn't contain "/" or "."
        assert "/" not in promise_str and "." not in promise_str


# Test interaction between redirect and resolve_url edge cases
@given(st.sampled_from(["", ".", "..", "/", "./", "../", "//", ".//", "..//"]))
def test_redirect_with_edge_urls(url):
    """Test redirect with edge case URLs"""
    try:
        # Test that redirect doesn't crash on edge cases
        response = redirect(url)
        assert isinstance(response, HttpResponseRedirect)
        
        # Check location header is set
        assert "Location" in response
        
        # For relative URLs, location should match input
        if url.startswith("./") or url.startswith("../"):
            assert response["Location"] == url
    except (NoReverseMatch, ValueError) as e:
        # Some edge cases might fail, but let's check if it's expected
        if "/" in url or "." in url:
            # According to resolve_url, these should not raise
            raise AssertionError(f"redirect({url!r}) raised {e.__class__.__name__} but url contains '/' or '.'")


# Test _get_queryset with None and edge cases
def test_get_queryset_with_none():
    """Test _get_queryset with None input"""
    result = _get_queryset(None)
    assert result is None


# Test for potential issues with URL encoding/escaping
@given(st.text(alphabet=string.printable, min_size=1, max_size=20).filter(
    lambda s: s.startswith("./") or s.startswith("../")
))
def test_resolve_url_preserves_special_chars_in_relative(url):
    """Test that special characters in relative URLs are preserved exactly"""
    result = resolve_url(url)
    assert result == url, f"Special characters not preserved: {url!r} -> {result!r}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])