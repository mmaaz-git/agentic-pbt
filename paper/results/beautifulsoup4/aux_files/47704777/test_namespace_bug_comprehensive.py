"""Comprehensive test of the namespace bug across all CSS methods."""

from bs4 import BeautifulSoup
import traceback

html = """<html>
<body>
    <div id="test">Test content</div>
</body>
</html>"""

soup = BeautifulSoup(html, 'html.parser')
css = soup.css

# Compile a selector
compiled_selector = css.compile('div')
custom_namespaces = {'custom': 'http://example.com'}

print("Testing namespace parameter with precompiled selectors across all methods:")
print("=" * 70)

# Test each method that accepts a selector and namespaces
methods_to_test = [
    ('select', lambda: css.select(compiled_selector, namespaces=custom_namespaces)),
    ('select_one', lambda: css.select_one(compiled_selector, namespaces=custom_namespaces)),
    ('iselect', lambda: list(css.iselect(compiled_selector, namespaces=custom_namespaces))),
    ('closest', lambda: soup.body.css.closest(compiled_selector, namespaces=custom_namespaces) if soup.body else None),
    ('match', lambda: soup.body.css.match(compiled_selector, namespaces=custom_namespaces) if soup.body else None),
    ('filter', lambda: soup.body.css.filter(compiled_selector, namespaces=custom_namespaces) if soup.body else None),
]

bugs_found = []

for method_name, test_func in methods_to_test:
    try:
        result = test_func()
        print(f"✓ {method_name:12} - No error (result type: {type(result).__name__})")
    except ValueError as e:
        if "Cannot process 'namespaces'" in str(e):
            print(f"✗ {method_name:12} - BUG: {e}")
            bugs_found.append(method_name)
        else:
            print(f"? {method_name:12} - Different error: {e}")
    except Exception as e:
        print(f"? {method_name:12} - Unexpected error: {e}")

print("\n" + "=" * 70)
print(f"Summary: Found namespace handling bug in {len(bugs_found)} method(s):")
for method in bugs_found:
    print(f"  - CSS.{method}()")

if bugs_found:
    print("\nThe bug occurs because the _ns() method doesn't properly handle")
    print("the case where a precompiled selector is used with a namespaces")
    print("parameter. The code should either:")
    print("1. Ignore the namespaces parameter for precompiled selectors, OR")
    print("2. Raise a clearer error message explaining the limitation")