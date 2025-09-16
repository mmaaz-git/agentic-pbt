"""Property-based tests for django.core using Hypothesis."""

import math
from hypothesis import given, strategies as st, assume, settings
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


# Test 1: Round-trip property for signing.dumps/loads
@given(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers()),
        st.dictionaries(
            st.text(),
            st.one_of(st.integers(), st.text(), st.none(), st.booleans())
        )
    )
)
@settings(max_examples=500)
def test_signing_dumps_loads_roundtrip(obj):
    """Test that loads(dumps(obj)) returns the original object."""
    # Use a fixed key for testing
    key = "test-secret-key-for-hypothesis-testing"
    
    # Dump the object
    signed = signing.dumps(obj, key=key)
    
    # Load it back
    result = signing.loads(signed, key=key)
    
    # Should get the same object back
    assert result == obj, f"Round-trip failed: {obj} != {result}"


# Test 2: Round-trip for b64_encode/decode
@given(st.binary())
@settings(max_examples=500)
def test_b64_encode_decode_roundtrip(data):
    """Test that b64_decode(b64_encode(data)) returns the original data."""
    encoded = b64_encode(data)
    decoded = b64_decode(encoded)
    assert decoded == data, f"b64 round-trip failed for data of length {len(data)}"


# Test 3: Round-trip for b62_encode/decode  
@given(st.integers(min_value=0))
@settings(max_examples=500)
def test_b62_encode_decode_roundtrip(num):
    """Test that b62_decode(b62_encode(num)) returns the original number."""
    encoded = b62_encode(num)
    decoded = b62_decode(encoded)
    assert decoded == num, f"b62 round-trip failed: {num} -> {encoded} -> {decoded}"


# Test 4: Paginator invariants
@given(
    st.lists(st.integers(), min_size=0, max_size=1000),
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=0, max_value=10)
)
@settings(max_examples=500)
def test_paginator_item_count_invariant(items, per_page, orphans):
    """Test that all items are accounted for across all pages."""
    p = paginator.Paginator(items, per_page, orphans=orphans)
    
    if len(items) == 0:
        # Special case: empty list
        if p.allow_empty_first_page:
            assert p.num_pages == 1
        else:
            return  # Skip if empty first page not allowed
    
    # Collect all items from all pages
    all_items_from_pages = []
    for page_num in p.page_range:
        page = p.page(page_num)
        all_items_from_pages.extend(page.object_list)
    
    # Should have all original items
    assert len(all_items_from_pages) == len(items), \
        f"Item count mismatch: {len(all_items_from_pages)} != {len(items)}"
    assert all_items_from_pages == items, "Items don't match"


@given(
    st.lists(st.integers(), min_size=1, max_size=1000),
    st.integers(min_value=1, max_value=100)
)
@settings(max_examples=500)
def test_paginator_page_size_invariant(items, per_page):
    """Test that each page (except last) has exactly per_page items."""
    p = paginator.Paginator(items, per_page)
    
    for page_num in p.page_range:
        page = p.page(page_num)
        if page_num < p.num_pages:
            # All pages except the last should have exactly per_page items
            assert len(page.object_list) == per_page, \
                f"Page {page_num} has {len(page.object_list)} items, expected {per_page}"
        else:
            # Last page should have remaining items
            expected = len(items) % per_page or per_page
            assert len(page.object_list) == expected, \
                f"Last page has {len(page.object_list)} items, expected {expected}"


@given(
    st.lists(st.integers(), min_size=0, max_size=1000),
    st.integers(min_value=1, max_value=100)
)  
@settings(max_examples=500)
def test_paginator_num_pages_calculation(items, per_page):
    """Test that num_pages is calculated correctly."""
    p = paginator.Paginator(items, per_page)
    
    if len(items) == 0:
        expected_pages = 1 if p.allow_empty_first_page else 0
    else:
        expected_pages = math.ceil(len(items) / per_page)
    
    assert p.num_pages == expected_pages, \
        f"num_pages={p.num_pages}, expected={expected_pages} for {len(items)} items with per_page={per_page}"


# Test 5: Signing with compression
@given(
    st.one_of(
        st.text(min_size=0),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    )
)
@settings(max_examples=500)
def test_signing_dumps_loads_with_compression(obj):
    """Test that compression doesn't break round-trip."""
    key = "test-key"
    
    # Test with compression
    compressed = signing.dumps(obj, key=key, compress=True)
    result = signing.loads(compressed, key=key)
    
    assert result == obj, f"Round-trip with compression failed"