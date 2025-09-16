"""Property-based tests for Flask flash messaging system."""

from hypothesis import given, strategies as st, assume
from flask import Flask, flash, get_flashed_messages
import string


# Create a test Flask app
def create_app():
    app = Flask(__name__)
    app.secret_key = 'test_secret_key_for_hypothesis_testing'
    return app


# Test flash/get_flashed_messages round-trip property
@given(
    messages=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=1000),  # message
            st.text(alphabet=string.ascii_letters + string.digits + '_', min_size=1, max_size=50)  # category
        ),
        min_size=0,
        max_size=100
    )
)
def test_flash_get_messages_roundtrip(messages):
    """Messages that are flashed should be retrievable with correct content."""
    app = create_app()
    
    with app.test_request_context():
        # Flash all messages
        for msg, category in messages:
            flash(msg, category)
        
        # Get all messages with categories
        retrieved = get_flashed_messages(with_categories=True)
        
        # Should get back what we flashed, but note: get_flashed_messages returns (category, message)
        # while flash takes (message, category) - this is documented behavior
        expected = [(category, msg) for msg, category in messages]
        assert retrieved == expected
        
        # Second call in same request should return same messages
        retrieved2 = get_flashed_messages(with_categories=True)
        assert retrieved2 == retrieved


# Test category filtering property
@given(
    messages=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=100),
            st.sampled_from(['error', 'info', 'warning', 'success', 'debug'])
        ),
        min_size=1,
        max_size=20
    ),
    filter_categories=st.lists(
        st.sampled_from(['error', 'info', 'warning', 'success', 'debug']),
        min_size=1,
        max_size=3,
        unique=True
    )
)
def test_flash_category_filter(messages, filter_categories):
    """Category filter should only return messages with specified categories."""
    app = create_app()
    
    with app.test_request_context():
        # Flash all messages
        for msg, category in messages:
            flash(msg, category)
        
        # Get filtered messages
        filtered = get_flashed_messages(category_filter=filter_categories)
        
        # Get all messages with categories to verify
        all_messages = get_flashed_messages(with_categories=True)
        
        # Filtered messages should only contain those with specified categories
        expected = [msg for cat, msg in all_messages if cat in filter_categories]
        assert filtered == expected


# Test with_categories flag property
@given(
    messages=st.lists(
        st.tuples(
            st.text(min_size=1, max_size=100),
            st.text(alphabet=string.ascii_letters, min_size=1, max_size=20)
        ),
        min_size=0,
        max_size=20
    )
)
def test_flash_with_categories_flag(messages):
    """with_categories flag should control return format."""
    app = create_app()
    
    with app.test_request_context():
        # Flash all messages
        for msg, category in messages:
            flash(msg, category)
        
        # Get without categories
        without_cat = get_flashed_messages(with_categories=False)
        # Get with categories
        with_cat = get_flashed_messages(with_categories=True)
        
        # Without categories should just be message strings
        assert without_cat == [msg for msg, _ in messages]
        # With categories should be tuples (category, message) - note the order!
        expected = [(category, msg) for msg, category in messages]
        assert with_cat == expected


# Test default category property
@given(
    messages=st.lists(
        st.text(min_size=1, max_size=100),
        min_size=1,
        max_size=20
    )
)
def test_flash_default_category(messages):
    """When no category specified, should use 'message' as default."""
    app = create_app()
    
    with app.test_request_context():
        # Flash messages without category
        for msg in messages:
            flash(msg)  # No category specified
        
        # Get with categories
        with_cat = get_flashed_messages(with_categories=True)
        
        # All should have 'message' as category
        assert all(cat == 'message' for cat, _ in with_cat)
        assert [msg for _, msg in with_cat] == messages


# Test empty flash behavior
@given(st.just([]))
def test_flash_empty(messages):
    """get_flashed_messages on empty flash should return empty list."""
    app = create_app()
    
    with app.test_request_context():
        # Don't flash anything
        result = get_flashed_messages()
        assert result == []
        
        # With categories should also be empty
        result_cat = get_flashed_messages(with_categories=True)
        assert result_cat == []


# Test persistence within request
@given(
    messages=st.lists(
        st.text(min_size=1, max_size=100),
        min_size=1,
        max_size=10
    )
)
def test_flash_persistence_in_request(messages):
    """Messages should persist for multiple calls within same request."""
    app = create_app()
    
    with app.test_request_context():
        # Flash messages
        for msg in messages:
            flash(msg)
        
        # Multiple calls should return same messages
        result1 = get_flashed_messages()
        result2 = get_flashed_messages()
        result3 = get_flashed_messages()
        
        assert result1 == result2 == result3 == messages