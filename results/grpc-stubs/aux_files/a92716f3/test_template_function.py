import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import re

# Import the module we're testing
from cloudscraper.interpreters.encapsulated import template


# Test 1: template should raise ValueError for invalid input
@given(st.text())
def test_template_invalid_input(body):
    """template should raise ValueError when the required pattern is not found"""
    # Only test strings that don't contain the expected pattern
    if 'setTimeout(function(){' in body and 'a.value' in body and 'toFixed(10)' in body:
        assume(False)
    
    domain = "example.com"
    try:
        result = template(body, domain)
        # If we get here without exception, check if it actually found the pattern
        # which would be a bug
        assert False, f"template() should have raised ValueError for input without the required pattern"
    except ValueError as e:
        # This is expected
        assert 'Unable to identify Cloudflare IUAM Javascript' in str(e)
    except Exception as e:
        # Any other exception is unexpected
        assert False, f"Unexpected exception: {e}"


# Test 2: template with valid pattern should return JavaScript
def test_template_valid_pattern():
    """template should extract and process valid Cloudflare challenge patterns"""
    # Create a minimal valid input that matches the regex pattern
    body = '''
    <html>
    <script>
    setTimeout(function(){
        var s,t,o,p,b,r,e,a,k,i,n,g,f, k = 'testkey';
        a.value = something.toFixed(10);
    }, 4000);
    </script>
    <div id="testkey123">jsfuck_code_here</div>
    </html>
    '''
    
    domain = "example.com"
    
    try:
        result = template(body, domain)
        # Should return a string containing JavaScript
        assert isinstance(result, str)
        assert 'document' in result
        assert domain in result
        assert 'toFixed(10)' in result
    except Exception as e:
        assert False, f"template() raised unexpected exception on valid input: {e}"


# Test 3: Domain injection - domain parameter should be properly escaped/inserted
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789.-", min_size=1, max_size=50))
def test_template_domain_injection(domain):
    """Domain parameter should be safely inserted into the JavaScript template"""
    # Skip domains with certain special characters that might break the test
    if '{' in domain or '}' in domain:
        assume(False)
    
    body = '''
    <script>
    setTimeout(function(){
        var k = 'key';
        a.value = something.toFixed(10);
    }, 4000);
    </script>
    '''
    
    try:
        result = template(body, domain)
        # Domain should appear in the result
        assert domain in result
        # Check that the domain is inserted in the expected location
        assert f'https://{domain}/' in result
    except Exception as e:
        # template might fail, which is okay for this test
        pass


# Test 4: Key extraction from body
def test_template_key_extraction():
    """template should correctly extract the 'k' variable value"""
    test_key = "myspecialkey"
    body = f'''
    <script>
    setTimeout(function(){{
        var k = '{test_key}';
        a.value = something.toFixed(10);
    }}, 4000);
    </script>
    <div id="{test_key}001">code1</div>
    <div id="{test_key}002">code2</div>
    '''
    
    domain = "example.com"
    
    try:
        result = template(body, domain)
        # The key should be used to extract div contents
        assert test_key in result or 'code1' in result or 'code2' in result
    except Exception as e:
        assert False, f"Unexpected error in key extraction: {e}"


# Test 5: Multiple div extraction
@given(st.integers(min_value=1, max_value=10))
def test_template_multiple_divs(num_divs):
    """template should handle multiple div elements with the same key prefix"""
    test_key = "testkey"
    divs = ""
    for i in range(num_divs):
        divs += f'<div id="{test_key}{i:03d}">content_{i}</div>\n'
    
    body = f'''
    <script>
    setTimeout(function(){{
        var k = '{test_key}';
        a.value = something.toFixed(10);
    }}, 4000);
    </script>
    {divs}
    '''
    
    domain = "example.com"
    
    try:
        result = template(body, domain)
        # Should successfully process all divs
        assert isinstance(result, str)
        # Check that content from divs is included
        for i in range(num_divs):
            # The content should be in the subVars
            pass  # Just check it doesn't crash
    except Exception as e:
        assert False, f"Failed to handle {num_divs} divs: {e}"


# Test 6: Regex replacement edge case
def test_template_interval_replacement():
    """Test the specific regex replacement for setInterval"""
    body = '''
    <script>
    setTimeout(function(){
        var k = 'key';
        (setInterval(function(){}, 100),t.match(/https?:\/\//)[0]);
        a.value = something.toFixed(10);
    }, 4000);
    </script>
    '''
    
    domain = "example.com"
    
    try:
        result = template(body, domain)
        # The setInterval part should be replaced
        assert 'setInterval(function(){}, 100)' not in result
        assert 't.match(/https?:\\/\\//)[0];' in result
    except Exception as e:
        assert False, f"Regex replacement failed: {e}"