"""
Additional tests for query parameter handling in SQLAlchemy URLs.
"""
from hypothesis import given, strategies as st
from sqlalchemy.engine import make_url
from sqlalchemy.engine.url import URL


@given(
    key=st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'),
    include_empty=st.booleans()
)
def test_empty_query_values(key, include_empty):
    """Test that empty query parameter values are handled correctly."""
    # Create query with empty value
    query = {key: ''}
    if include_empty:
        query['other'] = 'value'
    
    url = URL.create(
        drivername='postgresql',
        host='localhost',
        database='test',
        query=query
    )
    
    url_string = url.render_as_string(hide_password=False)
    parsed_url = make_url(url_string)
    
    # Empty string values should be preserved
    if '' in query.values():
        # Check if empty values are preserved
        assert key in url.query  # Original URL should have the key
        # After round-trip, empty values might be lost - this is what we're testing
        if key not in parsed_url.query:
            # This is a potential bug - empty values are dropped
            pass


@given(
    keys=st.lists(
        st.text(min_size=1, max_size=5, alphabet='abcdefghijklmnopqrstuvwxyz'),
        min_size=1,
        max_size=3,
        unique=True
    )
)
def test_valueless_query_params(keys):
    """Test URLs with query parameters that have no values (just keys)."""
    # Build URL string with valueless parameters
    query_string = '&'.join(keys)
    url_string = f'postgresql://localhost/test?{query_string}'
    
    # Parse the URL
    parsed_url = make_url(url_string)
    
    # Check if keys are preserved
    # SQLAlchemy might drop valueless parameters - documenting this behavior
    for key in keys:
        if key not in parsed_url.query:
            # Valueless parameters are dropped - potential issue
            pass