#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from cloudscraper.interpreters.encapsulated import template

print("Reproducing empty k value bug in template function")
print("=" * 60)

# Bug: Empty k value causes AttributeError
body_with_empty_k = '''
<script>
setTimeout(function(){
    var k = '';
    a.value = something.toFixed(10);
}, 4000);
</script>
'''

print("Test input:")
print(body_with_empty_k)
print()

try:
    result = template(body_with_empty_k, "example.com")
    print(f"Unexpected success! Result: {result[:100]}...")
except AttributeError as e:
    print(f"✓ BUG CONFIRMED: AttributeError when k is empty string")
    print(f"  Error: {e}")
    print()
    print("This happens because the regex pattern expects at least one non-whitespace character:")
    print("  r\" k\\s*=\\s*'(?P<k>\\S+)';\"")
    print("  The \\S+ requires at least one non-whitespace character")
    print()
    print("When k = '', the regex doesn't match, returning None")
    print("Then .group('k') is called on None, causing AttributeError")
except Exception as e:
    print(f"Different error: {type(e).__name__}: {e}")

print()
print("=" * 60)
print("Additional test: k with only whitespace")

body_with_space_k = '''
<script>
setTimeout(function(){
    var k = ' ';
    a.value = something.toFixed(10);
}, 4000);
</script>
'''

try:
    result = template(body_with_space_k, "example.com")
    print(f"Result with space k: {result[:100]}...")
except Exception as e:
    print(f"Error with space k: {type(e).__name__}: {e}")