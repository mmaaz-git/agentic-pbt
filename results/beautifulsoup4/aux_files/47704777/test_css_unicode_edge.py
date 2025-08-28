"""Test CSS module with Unicode and other edge cases."""

from hypothesis import given, strategies as st, assume, settings, example
from bs4 import BeautifulSoup
from bs4.css import CSS
from bs4.element import ResultSet
import string


# Test Unicode handling in selectors and escaping
@given(st.text(min_size=1, max_size=20))
@example("🦄")  # Emoji
@example("中文")  # Chinese characters  
@example("\x00")  # Null character
@example("\\")  # Backslash
@example("'")  # Single quote
@example('"')  # Double quote
@settings(max_examples=200)
def test_escape_unicode_and_special(text):
    """Test that escape handles Unicode and special characters correctly."""
    soup = BeautifulSoup("<html><body></body></html>", 'html.parser')
    css = soup.css
    
    try:
        escaped = css.escape(text)
        
        # The escaped result should be a string
        assert isinstance(escaped, str)
        
        # We should be able to use it in a selector without error
        # (even if it doesn't match anything)
        selector = f"#{escaped}"
        results = css.select(selector)
        assert isinstance(results, ResultSet)
        
        # Now create an element with this ID and verify we can select it
        html2 = f'<div id="{text}">test</div>'
        soup2 = BeautifulSoup(html2, 'html.parser')
        
        # Using the escaped ID in a selector should find the element
        escaped_selector = f"#{css.escape(text)}"
        found = soup2.select(escaped_selector)
        
        # We should find the element if the ID is valid HTML
        # Some characters might not be valid in HTML IDs
        
    except Exception as e:
        # Some characters might not be escapeable
        # But the escape function shouldn't crash on valid Unicode
        if text and all(c in string.printable for c in text):
            # Printable ASCII should always work
            raise


@given(st.integers(min_value=0, max_value=1000))
@settings(max_examples=100)
def test_limit_zero_means_unlimited(num_elements):
    """Test that limit=0 means no limit, not zero results."""
    html = "<html><body>"
    for i in range(min(num_elements, 100)):  # Cap at 100 for performance
        html += f"<p>Element {i}</p>"
    html += "</body></html>"
    
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    # Select with limit=0 should return all elements
    results_unlimited = css.select('p', limit=0)
    results_all = css.select('p')
    
    assert results_unlimited == results_all
    assert len(results_unlimited) == min(num_elements, 100)


@given(st.text(alphabet=string.ascii_letters, min_size=0, max_size=10))
@settings(max_examples=100)
def test_empty_string_selector(prefix):
    """Test behavior with empty or whitespace-only selectors."""
    soup = BeautifulSoup("<html><body><div>test</div></body></html>", 'html.parser')
    css = soup.css
    
    selectors = ["", " ", "  ", "\t", "\n"]
    
    for selector in selectors:
        full_selector = prefix + selector if prefix else selector
        
        if not full_selector.strip():
            # Empty selector should raise an error
            try:
                results = css.select(full_selector)
                # Some implementations might return empty instead of error
                assert len(results) == 0
            except Exception:
                # This is also acceptable - empty selector is invalid
                pass


@given(st.lists(st.integers(min_value=1, max_value=100), min_size=1, max_size=10))
@settings(max_examples=100)
def test_iselect_with_limit_property(limits):
    """Test that iselect respects limit parameter correctly."""
    # Create HTML with many elements
    html = "<html><body>"
    for i in range(20):
        html += f"<span class='item'>Item {i}</span>"
    html += "</body></html>"
    
    soup = BeautifulSoup(html, 'html.parser')
    css = soup.css
    
    for limit in limits:
        # Get results from both select and iselect
        select_results = css.select('.item', limit=limit)
        iselect_results = list(css.iselect('.item', limit=limit))
        
        # They should be identical
        assert select_results == iselect_results
        
        # Both should respect the limit
        assert len(select_results) <= limit
        assert len(iselect_results) <= limit


@given(
    st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=5),
    st.integers(min_value=0, max_value=10)
)
@settings(max_examples=100) 
def test_filter_vs_select_consistency(tag_name, depth):
    """Test that filter results are always a subset of select results."""
    # Build nested structure
    html = f"<{tag_name} id='root'>"
    
    # Add direct children
    for i in range(3):
        html += f"<div class='direct child{i}'>"
        # Add nested descendants
        for j in range(depth):
            html += f"<div class='nested level{j}'>"
        for j in range(depth):
            html += "</div>"
        html += "</div>"
    
    html += f"</{tag_name}>"
    
    soup = BeautifulSoup(html, 'html.parser')
    root = soup.find(id='root')
    
    if root:
        # Get results from filter and select
        filter_results = root.css.filter('div')
        select_results = root.css.select('div')
        
        # Filter results should be a subset of select results
        for elem in filter_results:
            assert elem in select_results
        
        # Filter should only have direct children
        for elem in filter_results:
            assert elem.parent == root
        
        # Select might have nested elements too
        assert len(filter_results) <= len(select_results)
        
        # If depth > 0, select should have more results than filter
        if depth > 0:
            assert len(filter_results) < len(select_results)


@given(st.text(min_size=1, max_size=100))
@settings(max_examples=100)
def test_compile_caching_behavior(selector_base):
    """Test that compile() behaves consistently with multiple calls."""
    soup = BeautifulSoup("<html><body><div>test</div></body></html>", 'html.parser')
    css = soup.css
    
    # Create a valid selector
    selector = "div"
    
    # Compile multiple times
    compiled1 = css.compile(selector)
    compiled2 = css.compile(selector)
    
    # Results should be equivalent (may or may not be same object)
    results1 = css.select(compiled1)
    results2 = css.select(compiled2)
    
    assert results1 == results2


# Test namespace parameter edge cases
@given(st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=1, max_size=50), max_size=5))
@settings(max_examples=50)
def test_namespace_parameter_types(namespaces):
    """Test that namespace parameter accepts various dictionary types."""
    soup = BeautifulSoup("<html><body><div>test</div></body></html>", 'html.parser')
    css = soup.css
    
    try:
        # Should accept namespace dictionary without error
        results = css.select('div', namespaces=namespaces)
        assert isinstance(results, ResultSet)
        
        # Also test with None
        results_none = css.select('div', namespaces=None)
        assert isinstance(results_none, ResultSet)
        
    except Exception:
        # Invalid namespace values might cause errors
        pass


@given(st.integers())
@settings(max_examples=100)
def test_flags_parameter(flags):
    """Test that flags parameter is handled correctly."""
    soup = BeautifulSoup("<html><body><DIV>test</DIV></body></html>", 'html.parser')
    css = soup.css
    
    try:
        # Try using various flag values
        results = css.select('div', flags=flags)
        assert isinstance(results, ResultSet)
        
        # Also test with compile
        compiled = css.compile('div', flags=flags)
        results2 = css.select(compiled)
        assert isinstance(results2, ResultSet)
        
    except (ValueError, TypeError):
        # Invalid flags might be rejected
        pass