import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume
import re

# Import the module we're testing
from cloudscraper.interpreters.encapsulated import template


# Test 1: Malformed HTML with incomplete patterns
def test_template_incomplete_pattern():
    """Test template with incomplete setTimeout pattern"""
    test_cases = [
        # Missing closing parenthesis
        "setTimeout(function(){a.value = something.toFixed(10);",
        # Missing toFixed
        "setTimeout(function(){a.value = something;}, 4000);",
        # Missing a.value
        "setTimeout(function(){something.toFixed(10);}, 4000);",
    ]
    
    for body in test_cases:
        try:
            result = template(body, "example.com")
            assert False, f"Should have raised ValueError for incomplete pattern: {body[:50]}..."
        except ValueError as e:
            assert 'Unable to identify Cloudflare IUAM Javascript' in str(e)


# Test 2: Multiple setTimeout patterns (which one gets matched?)
def test_template_multiple_settimeout():
    """Test what happens with multiple setTimeout patterns"""
    body = '''
    <script>
    setTimeout(function(){
        var k = 'key1';
        a.value = first.toFixed(10);
    }, 1000);
    
    setTimeout(function(){
        var k = 'key2';  
        a.value = second.toFixed(10);
    }, 2000);
    </script>
    '''
    
    try:
        result = template(body, "example.com")
        # It should match the first one due to regex behavior
        assert 'first.toFixed(10)' in result or 'second.toFixed(10)' in result
        print(f"Matched pattern in result: {result[:100]}...")
    except Exception as e:
        print(f"Error with multiple patterns: {e}")


# Test 3: Special characters in k value
@given(st.text(alphabet="!@#$%^&*()[]{}\\|;:'\"<>,.?/`~", min_size=1, max_size=10))
def test_template_special_k_value(special_chars):
    """Test template with special characters in k value"""
    # Some characters might break the regex
    body = f'''
    <script>
    setTimeout(function(){{
        var k = '{special_chars}';
        a.value = something.toFixed(10);
    }}, 4000);
    </script>
    <div id="{special_chars}001">content</div>
    '''
    
    try:
        result = template(body, "example.com")
        # Should handle special characters properly
        assert isinstance(result, str)
    except Exception as e:
        # Some special characters might legitimately break the regex
        print(f"Failed with special chars '{special_chars}': {e}")


# Test 4: Very large div content
@given(st.integers(min_value=1000, max_value=10000))
def test_template_large_div_content(size):
    """Test template with very large div content"""
    large_content = "x" * size
    body = f'''
    <script>
    setTimeout(function(){{
        var k = 'key';
        a.value = something.toFixed(10);
    }}, 4000);
    </script>
    <div id="key001">{large_content}</div>
    '''
    
    try:
        result = template(body, "example.com")
        # Should handle large content
        assert isinstance(result, str)
        # The large content should be in the subVars
        assert len(result) > size  # Result should contain the large content
    except Exception as e:
        assert False, f"Failed with large content size {size}: {e}"


# Test 5: Nested quotes in div content
def test_template_nested_quotes():
    """Test template with nested quotes in div content"""
    body = '''
    <script>
    setTimeout(function(){
        var k = 'key';
        a.value = something.toFixed(10);
    }, 4000);
    </script>
    <div id="key001">content with "quotes" and 'apostrophes'</div>
    '''
    
    try:
        result = template(body, "example.com")
        # Should handle quotes properly
        assert isinstance(result, str)
    except Exception as e:
        print(f"Failed with nested quotes: {e}")


# Test 6: Empty k value
def test_template_empty_k():
    """Test template with empty k value"""
    body = '''
    <script>
    setTimeout(function(){
        var k = '';
        a.value = something.toFixed(10);
    }, 4000);
    </script>
    <div id="001">content</div>
    '''
    
    try:
        result = template(body, "example.com")
        print(f"Result with empty k: {result[:100]}...")
    except Exception as e:
        print(f"Error with empty k: {e}")


# Test 7: Regex injection in domain
def test_template_domain_with_regex_chars():
    """Test if domain with regex special characters is handled safely"""
    domains_with_special = [
        "example.com",  # Normal
        "sub.example.com",  # With dot
        "example-test.com",  # With hyphen
        "192.168.1.1",  # IP address
        # These might break if not properly escaped:
        "example[1].com",  # Brackets
        "example(1).com",  # Parentheses
        "example{1}.com",  # Braces
    ]
    
    body = '''
    <script>
    setTimeout(function(){
        var k = 'key';
        a.value = something.toFixed(10);
    }, 4000);
    </script>
    '''
    
    for domain in domains_with_special:
        try:
            result = template(body, domain)
            assert domain in result or domain.replace('.', '\\.') in result
        except Exception as e:
            print(f"Failed with domain '{domain}': {e}")


# Test 8: Case sensitivity in pattern matching
def test_template_case_sensitivity():
    """Test if pattern matching is case sensitive"""
    test_cases = [
        # Different cases of setTimeout
        "SETTIMEOUT(function(){a.value = something.toFixed(10);}, 4000);",
        "setTimeout(FUNCTION(){a.value = something.toFixed(10);}, 4000);",
        "setTimeout(function(){A.VALUE = something.toFixed(10);}, 4000);",
        "setTimeout(function(){a.value = something.TOFIXED(10);}, 4000);",
    ]
    
    for body in test_cases:
        try:
            result = template(body, "example.com")
            print(f"Unexpectedly succeeded with case variant: {body[:50]}...")
        except ValueError:
            # Expected - pattern should be case sensitive
            pass


# Test 9: HTML entities in div content
def test_template_html_entities():
    """Test template with HTML entities in div content"""
    body = '''
    <script>
    setTimeout(function(){
        var k = 'key';
        a.value = something.toFixed(10);
    }, 4000);
    </script>
    <div id="key001">&lt;script&gt;alert("xss")&lt;/script&gt;</div>
    <div id="key002">&amp;&nbsp;&quot;</div>
    '''
    
    try:
        result = template(body, "example.com")
        # HTML entities should be preserved as-is
        assert '&lt;' in result or '&amp;' in result
    except Exception as e:
        print(f"Failed with HTML entities: {e}")


# Test 10: Missing divs for declared k
def test_template_missing_divs():
    """Test template when k is declared but no matching divs exist"""
    body = '''
    <script>
    setTimeout(function(){
        var k = 'missingkey';
        a.value = something.toFixed(10);
    }, 4000);
    </script>
    <!-- No divs with id starting with 'missingkey' -->
    <div id="otherkey001">content</div>
    '''
    
    try:
        result = template(body, "example.com")
        # Should still work but subVars might be empty
        assert isinstance(result, str)
        # Check if subVars is empty or minimal
        print(f"Result with missing divs: {result[:200]}...")
    except Exception as e:
        print(f"Error with missing divs: {e}")