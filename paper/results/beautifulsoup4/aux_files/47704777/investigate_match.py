"""Investigate the match() behavior with combinators."""

from bs4 import BeautifulSoup

# Create test HTML
html = """<html><body>
<div id="div0">First</div>
<div id="div1">Second</div>
<div id="div2">Third</div>
</body></html>"""

soup = BeautifulSoup(html, 'html.parser')

# Get elements
div0 = soup.find(id='div0')
div1 = soup.find(id='div1')
div2 = soup.find(id='div2')

print("Testing match() with combinators:")
print("-" * 40)

# Test adjacent sibling selector
selector = "#div0 + div"
print(f"Selector: {selector}")
print(f"  div0.match('{selector}'): {div0.css.match(selector)}")
print(f"  div1.match('{selector}'): {div1.css.match(selector)}")
print(f"  div2.match('{selector}'): {div2.css.match(selector)}")
print()

# What elements does select return?
selected = soup.select(selector)
print(f"  soup.select('{selector}') returns: {[el.get('id') for el in selected]}")
print()

# Test general sibling selector
selector = "#div0 ~ div"
print(f"Selector: {selector}")
print(f"  div0.match('{selector}'): {div0.css.match(selector)}")
print(f"  div1.match('{selector}'): {div1.css.match(selector)}")
print(f"  div2.match('{selector}'): {div2.css.match(selector)}")
print()

selected = soup.select(selector)
print(f"  soup.select('{selector}') returns: {[el.get('id') for el in selected]}")
print()

# Let's check what soupsieve.match does directly
import soupsieve

print("Direct soupsieve.match() calls:")
print("-" * 40)
selector_compiled = soupsieve.compile("#div0 + div")
print(f"Selector: #div0 + div")
print(f"  soupsieve.match('#div0 + div', div0): {soupsieve.match('#div0 + div', div0)}")
print(f"  soupsieve.match('#div0 + div', div1): {soupsieve.match('#div0 + div', div1)}")
print(f"  soupsieve.match('#div0 + div', div2): {soupsieve.match('#div0 + div', div2)}")
print()

# Check documentation
print("From soupsieve documentation:")
print("match() checks if an element matches a selector.")
print("For '#div0 + div', div1 matches because it's a div that follows #div0")