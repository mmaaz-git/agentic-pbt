#!/usr/bin/env python3
"""Investigate why simple HTML snippets fail to parse dates."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from htmldate import find_date

# Test various HTML structures
test_cases = [
    # Minimal meta tag
    ('<meta name="date" content="2000-01-01">', "Minimal meta tag"),
    
    # More complete HTML
    ('<html><head><meta name="date" content="2000-01-01"></head></html>', "Complete HTML with meta"),
    
    # With body
    ('<html><head><meta name="date" content="2000-01-01"></head><body></body></html>', "HTML with body"),
    
    # Time element
    ('<time datetime="2000-01-01">Published</time>', "Time element alone"),
    ('<html><body><time datetime="2000-01-01">Published</time></body></html>', "Time in complete HTML"),
    
    # Article published meta
    ('<meta property="article:published_time" content="2000-01-01T00:00:00Z">', "Article meta alone"),
    ('<html><head><meta property="article:published_time" content="2000-01-01T00:00:00Z"></head></html>', "Article meta in HTML"),
]

print("Testing various HTML structures with find_date():\n")

for html, description in test_cases:
    result = find_date(html)
    print(f"Test: {description}")
    print(f"HTML: {html[:60]}...")
    print(f"Result: {result}")
    print()

# Test with valid complete HTML
complete_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="date" content="2000-01-01">
    <title>Test Page</title>
</head>
<body>
    <article>
        <h1>Test Article</h1>
        <time datetime="2000-01-01">January 1, 2000</time>
        <p>Content here</p>
    </article>
</body>
</html>"""

print("Complete HTML document:")
result = find_date(complete_html)
print(f"Result: {result}")
print()

# Test what the library considers valid HTML
from lxml import html as lxml_html

minimal = '<meta name="date" content="2000-01-01">'
print(f"\nParsing minimal HTML with lxml: {minimal}")
tree = lxml_html.fromstring(minimal)
print(f"Tree length: {len(tree)}")
print(f"Tree tag: {tree.tag if hasattr(tree, 'tag') else 'No tag'}")
print()

complete = '<html><head><meta name="date" content="2000-01-01"></head></html>'
print(f"Parsing complete HTML with lxml: {complete[:50]}...")
tree = lxml_html.fromstring(complete)
print(f"Tree length: {len(tree)}")
print(f"Tree tag: {tree.tag if hasattr(tree, 'tag') else 'No tag'}")