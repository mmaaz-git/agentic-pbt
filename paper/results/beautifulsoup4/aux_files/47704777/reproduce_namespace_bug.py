"""Minimal reproduction of the namespace handling bug in bs4.css."""

from bs4 import BeautifulSoup

# Create a simple HTML document
html = """<html>
<body>
    <div id="test">Test content</div>
</body>
</html>"""

soup = BeautifulSoup(html, 'html.parser')
css = soup.css

print("Bug reproduction: Namespace handling with precompiled selectors")
print("=" * 60)

# Step 1: Compile a selector
compiled_selector = css.compile('div')
print(f"1. Compiled selector: {compiled_selector}")

# Step 2: Try to use the compiled selector with namespaces parameter
try:
    print("\n2. Attempting to select with compiled selector + namespaces...")
    custom_namespaces = {'custom': 'http://example.com'}
    results = css.select(compiled_selector, namespaces=custom_namespaces)
    print(f"   Success: Got {len(results)} results")
except ValueError as e:
    print(f"   ERROR: {e}")
    print("\n   This is a bug! The CSS.select() method should handle this case.")
    print("   According to the _ns() method logic, when a precompiled selector")
    print("   is passed, the namespaces parameter should be ignored, not cause")
    print("   an error.")

print("\n" + "=" * 60)
print("Expected behavior: The namespaces parameter should be ignored when")
print("using a precompiled selector, as the selector already has its")
print("namespace context compiled in.")

# Show the relevant code from css.py
print("\n" + "=" * 60)
print("Looking at the CSS._ns() method (lines 80-89 of css.py):")
print("""
def _ns(
    self, ns: Optional[_NamespaceMapping], select: str
) -> Optional[_NamespaceMapping]:
    \"\"\"Normalize a dictionary of namespaces.\"\"\"
    if not isinstance(select, self.api.SoupSieve) and ns is None:
        # If the selector is a precompiled pattern, it already has
        # a namespace context compiled in, which cannot be
        # replaced.
        ns = self.tag._namespaces
    return ns
""")

print("\nThe comment says namespace context 'cannot be replaced' for")
print("precompiled selectors, but the code doesn't actually prevent")
print("passing namespaces to soupsieve, leading to the ValueError.")