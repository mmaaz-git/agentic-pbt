"""Additional edge case tests for django.core."""

import math
from hypothesis import given, strategies as st, assume, settings, example
import django
from django.conf import settings as django_settings

# Configure Django settings for testing
if not django_settings.configured:
    django_settings.configure(
        SECRET_KEY='test-secret-key-for-hypothesis',
        SECRET_KEY_FALLBACKS=[]
    )

import django.core.signing as signing
import django.core.paginator as paginator
from django.core.signing import b64_encode, b64_decode, b62_encode, b62_decode


# Test edge cases with special Unicode characters
@given(
    st.dictionaries(
        st.text(alphabet=st.characters(blacklist_categories=('Cs',)), min_size=0),
        st.one_of(
            st.text(alphabet=st.characters(blacklist_categories=('Cs',))),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.none(),
        ),
        min_size=0,
        max_size=100
    )
)
@settings(max_examples=1000)
def test_signing_unicode_edge_cases(obj):
    """Test signing with complex Unicode strings."""
    key = "test-key-🔑"
    
    signed = signing.dumps(obj, key=key)
    result = signing.loads(signed, key=key)
    
    assert result == obj, f"Unicode round-trip failed"


# Test with nested data structures
@given(
    st.recursive(
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(max_size=100)
        ),
        lambda children: st.one_of(
            st.lists(children, max_size=10),
            st.dictionaries(
                st.text(max_size=20),
                children,
                max_size=10
            )
        ),
        max_leaves=100
    )
)
@settings(max_examples=500)
def test_signing_nested_structures(obj):
    """Test signing with deeply nested data structures."""
    key = "test-key"
    
    signed = signing.dumps(obj, key=key)
    result = signing.loads(signed, key=key)
    
    assert result == obj, f"Nested structure round-trip failed"


# Test Paginator with edge case orphans
@given(
    st.lists(st.integers(), min_size=1, max_size=100),
    st.integers(min_value=1, max_value=20),
    st.integers(min_value=0, max_value=50)
)
@settings(max_examples=1000)
def test_paginator_orphans_behavior(items, per_page, orphans):
    """Test that orphans parameter works correctly."""
    p = paginator.Paginator(items, per_page, orphans=orphans)
    
    # Get the last page
    last_page = p.page(p.num_pages)
    last_page_count = len(last_page.object_list)
    
    # Calculate expected behavior
    if p.num_pages > 1:
        # If last page has <= orphans items, they should be added to previous page
        remainder = len(items) % per_page
        if remainder > 0 and remainder <= orphans:
            # Orphans should be absorbed by previous page
            if p.num_pages == 2:
                # All items should be on one page
                assert p.num_pages == 1 or last_page_count > orphans
            else:
                # Last page should have more than orphans
                assert last_page_count > orphans or last_page_count == len(items)
    
    # Verify total item count is preserved
    total = sum(len(p.page(i).object_list) for i in p.page_range)
    assert total == len(items)


# Test b62 encoding with very large numbers
@given(st.integers(min_value=0, max_value=2**256))
@settings(max_examples=500)
def test_b62_large_numbers(num):
    """Test b62 encoding with very large numbers."""
    encoded = b62_encode(num)
    decoded = b62_decode(encoded)
    assert decoded == num, f"b62 failed for large number: {num}"


# Test signing with different salts
@given(
    st.one_of(st.integers(), st.text(), st.lists(st.integers())),
    st.text(min_size=0, max_size=50),
    st.text(min_size=0, max_size=50)
)
@settings(max_examples=500) 
def test_signing_different_salts(obj, salt1, salt2):
    """Test that different salts produce different signatures."""
    key = "test-key"
    
    signed1 = signing.dumps(obj, key=key, salt=salt1)
    signed2 = signing.dumps(obj, key=key, salt=salt2)
    
    # Different salts should produce different signatures (unless both empty and obj is simple)
    if salt1 != salt2:
        # The signed values should be different
        if obj:  # Skip for empty/None objects as they might produce same sig
            assert signed1 != signed2, f"Same signature for different salts"
    
    # But both should decode correctly with their respective salts
    result1 = signing.loads(signed1, key=key, salt=salt1)
    result2 = signing.loads(signed2, key=key, salt=salt2)
    
    assert result1 == obj
    assert result2 == obj
    
    # Loading with wrong salt should fail
    if salt1 != salt2:
        try:
            signing.loads(signed1, key=key, salt=salt2)
            assert False, "Should have raised BadSignature"
        except signing.BadSignature:
            pass  # Expected


# Test empty and single-element edge cases for Paginator
@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=500)
def test_paginator_empty_list(per_page):
    """Test Paginator with empty list."""
    p = paginator.Paginator([], per_page)
    
    assert p.count == 0
    assert p.num_pages == 1  # Should have 1 empty page
    
    page = p.page(1)
    assert len(page.object_list) == 0
    assert page.has_next() is False
    assert page.has_previous() is False


@given(
    st.integers(),
    st.integers(min_value=1, max_value=100)
)
@settings(max_examples=500)
def test_paginator_single_item(item, per_page):
    """Test Paginator with single item."""
    p = paginator.Paginator([item], per_page)
    
    assert p.count == 1
    assert p.num_pages == 1
    
    page = p.page(1)
    assert len(page.object_list) == 1
    assert page.object_list[0] == item