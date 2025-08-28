import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-http-client_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
import python_http_client.client as client


@given(
    st.dictionaries(st.text(min_size=1), st.text(), min_size=1),
    st.text(min_size=1),
    st.dictionaries(st.text(min_size=1), st.text(), min_size=1)
)
def test_client_headers_isolation(initial_headers, segment, new_headers):
    """Test that child clients don't share mutable headers with parent"""
    # Create parent client with initial headers
    parent = client.Client(
        host="http://example.com",
        request_headers=initial_headers.copy()
    )
    
    # Store original headers
    original_headers = parent.request_headers.copy()
    
    # Create child client
    child = parent._(segment)
    
    # Update child's headers
    child._update_headers(new_headers)
    
    # Property: Parent's headers should not be modified
    # This test will FAIL, revealing the bug
    assert parent.request_headers == original_headers, \
        f"Parent headers were modified! Expected {original_headers}, got {parent.request_headers}"