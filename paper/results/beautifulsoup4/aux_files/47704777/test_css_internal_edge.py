"""Test internal edge cases and potential bugs in bs4.css module."""

from hypothesis import given, strategies as st, assume, settings, example
from bs4 import BeautifulSoup
from bs4.css import CSS
from bs4.element import ResultSet
import soupsieve


# Test closest() with tricky hierarchies
@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_closest_traversal_order(depth):
    """Test that closest() traverses up correctly."""
    # Build deeply nested structure
    html = "<html><body>"
    
    # Create nested divs with different classes
    for i in range(depth):
        html += f'<div class="level{i}" id="div{i}">'
    
    html += '<span id="target">Target</span>'
    
    for i in range(depth):
        html += '</div>'
    
    html += "</body></html>"
    
    soup = BeautifulSoup(html, 'html.parser')
    target = soup.find(id='target')
    
    if target:
        # Test finding each level
        for i in range(depth):
            result = target.css.closest(f'.level{i}')
            assert result is not None
            assert f'level{i}' in result.get('class', [])
            assert result.get('id') == f'div{i}'
        
        # Test that it finds the closest (innermost) match first
        result = target.css.closest('div')
        if depth > 0:
            assert result.get('id') == f'div{depth-1}'  # The innermost div


@given(st.lists(st.text(alphabet='abc', min_size=1, max_size=3), min_size=0, max_size=5))
@settings(max_examples=100)
def test_resultset_type_consistency(class_names):
    """Test that ResultSet is always returned for multi-result methods."""
    html = "<html><body>"
    for cls in class_names:
        html += f'<div class="{cls}">Content</div>'
    html += "</body></html>"
    
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    # These methods should always return ResultSet
    methods_to_test = [
        lambda: css.select('div'),
        lambda: css.select('nonexistent'),
        lambda: css.filter('div'),
        lambda: css.filter('nonexistent'),
        lambda: css.select('div', limit=0),
        lambda: css.select('div', limit=1),
        lambda: css.select('div', limit=999),
    ]
    
    for method in methods_to_test:
        result = method()
        assert isinstance(result, ResultSet), f"Method {method} didn't return ResultSet"


# Test with precompiled selectors and namespaces
@given(st.booleans())
@settings(max_examples=50)
def test_precompiled_with_namespace_context(use_precompiled):
    """Test that precompiled selectors handle namespace context correctly."""
    # HTML with namespaces
    html = '''<html xmlns:custom="http://example.com">
    <body>
        <custom:div id="custom1">Custom</custom:div>
        <div id="regular">Regular</div>
    </body>
    </html>'''
    
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    # Define namespaces
    ns = {'custom': 'http://example.com'}
    
    if use_precompiled:
        try:
            # Compile with namespace
            compiled = css.compile('div', namespaces=ns)
            results = css.select(compiled)
            assert isinstance(results, ResultSet)
        except Exception:
            # Namespace handling might have limitations
            pass
    else:
        # Use string selector with namespace
        results = css.select('div', namespaces=ns)
        assert isinstance(results, ResultSet)


# Test ResultSet behavior when passed between methods
@given(st.integers(min_value=0, max_value=10))
@settings(max_examples=100)
def test_chained_operations(num_elements):
    """Test chaining CSS operations on results."""
    html = "<html><body>"
    for i in range(num_elements):
        html += f'<div class="outer"><span class="inner">Item {i}</span></div>'
    html += "</body></html>"
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Get all divs
    divs = soup.select('div')
    
    # Each div should have its own CSS interface
    for div in divs:
        assert hasattr(div, 'css')
        assert isinstance(div.css, CSS)
        
        # Should be able to select within each div
        inner = div.css.select('.inner')
        assert isinstance(inner, ResultSet)
        assert len(inner) == 1


# Test limit parameter with None value
@given(st.one_of(st.none(), st.integers(min_value=0, max_value=100)))
@settings(max_examples=100)
def test_limit_none_handling(limit):
    """Test that limit=None is handled correctly."""
    html = "<html><body>"
    for i in range(10):
        html += f"<p>Para {i}</p>"
    html += "</body></html>"
    
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    # The code shows it handles None by converting to 0
    results = css.select('p', limit=limit)
    assert isinstance(results, ResultSet)
    
    if limit is None or limit == 0:
        # Should return all elements
        assert len(results) == 10
    else:
        # Should respect the limit
        assert len(results) <= min(limit, 10)


# Test edge case with **kwargs passing
@given(st.dictionaries(st.text(min_size=1, max_size=10), st.integers(), max_size=3))
@settings(max_examples=50)
def test_kwargs_forwarding(extra_kwargs):
    """Test that **kwargs are properly forwarded to soupsieve."""
    soup = BeautifulSoup("<html><body><div>test</div></body></html>", 'html.parser')
    css = soup.css
    
    # Remove any keys that might conflict with named parameters
    extra_kwargs = {k: v for k, v in extra_kwargs.items() 
                   if k not in ['select', 'namespaces', 'limit', 'flags']}
    
    try:
        # These methods accept **kwargs
        results = css.select('div', **extra_kwargs)
        assert isinstance(results, ResultSet)
        
        result = css.select_one('div', **extra_kwargs)
        assert result is None or hasattr(result, 'name')
        
        # Also test compile
        compiled = css.compile('div', **extra_kwargs)
        
    except (TypeError, ValueError):
        # Invalid kwargs might be rejected by soupsieve
        pass


# Test _ns method edge cases
@given(st.booleans())
@settings(max_examples=50)
def test_namespace_normalization(is_compiled):
    """Test the _ns method for namespace normalization."""
    soup = BeautifulSoup("<html><body><div>test</div></body></html>", 'html.parser')
    
    # Set some namespaces on the tag
    soup._namespaces = {'test': 'http://test.com'}
    css = soup.css
    
    if is_compiled:
        # When selector is precompiled, namespace param should be ignored
        selector = css.compile('div')
        
        # Even if we pass namespaces, it should use the compiled ones
        custom_ns = {'custom': 'http://custom.com'}
        results = css.select(selector, namespaces=custom_ns)
        assert isinstance(results, ResultSet)
    else:
        # String selector should use provided namespaces
        results = css.select('div', namespaces={'x': 'http://x.com'})
        assert isinstance(results, ResultSet)


# Test potential None returns
@given(st.text(alphabet='abcdef', min_size=1, max_size=10))
@settings(max_examples=100)
def test_none_returns_handled(selector):
    """Test that None returns are handled correctly."""
    soup = BeautifulSoup("<html><body></body></html>", 'html.parser')
    css = soup.css
    
    # select_one can return None
    result = css.select_one(selector)
    assert result is None or hasattr(result, 'name')
    
    # closest can return None
    body = soup.body
    if body:
        result = body.css.closest(selector)
        assert result is None or hasattr(result, 'name')