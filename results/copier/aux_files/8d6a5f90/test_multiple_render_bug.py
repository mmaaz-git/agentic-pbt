"""Test for the bug where rendering the same template twice raises MultipleYieldTagsError."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._jinja_ext import YieldEnvironment, YieldExtension
from copier.errors import MultipleYieldTagsError

print("=== Testing Multiple Render Bug ===\n")

# Create environment and template
env = YieldEnvironment(extensions=[YieldExtension])
template_str = "{% yield item from items %}content{% endyield %}"
template = env.from_string(template_str)

print(f"Template: {template_str}")
print("This template has only ONE yield tag.\n")

# First render - should work
print("First render with items=[1, 2]:")
try:
    result1 = template.render({"items": [1, 2]})
    print(f"  Success! Result: {repr(result1)}")
    print(f"  yield_name={env.yield_name}, yield_iterable={env.yield_iterable}")
except Exception as e:
    print(f"  ERROR: {e}")

# Second render - should also work but might fail
print("\nSecond render with items=[3, 4]:")
try:
    result2 = template.render({"items": [3, 4]})
    print(f"  Success! Result: {repr(result2)}")
    print(f"  yield_name={env.yield_name}, yield_iterable={env.yield_iterable}")
except MultipleYieldTagsError as e:
    print(f"  BUG FOUND: MultipleYieldTagsError raised!")
    print(f"  Error message: {e}")
    print(f"  This is incorrect - there's only one yield tag in the template!")

print("\n=== Analysis ===")
print("The bug occurs because:")
print("1. The first render sets env.yield_name and env.yield_iterable")
print("2. The second render calls _yield_support again")
print("3. _yield_support checks if attributes are already set (line 104-107)")
print("4. Since they weren't reset, it raises MultipleYieldTagsError")
print("")
print("The preprocess() method should reset these, but it's only called")
print("when creating a new template, not when rendering an existing one.")
print("")
print("This violates the expectation that templates can be rendered multiple times.")